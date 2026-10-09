"""Modelos de imagen y voz del Token Plan: NO usan chat/completions. Direcciones segun docs.qwencloud.com (best-practices/integrate-multimodal-gen).
imagen (qwen-image-*, wan2.7-image*): POST /api/v1/services/aigc/multimodal-generation/generation
texto a voz (qwen-audio-3.0-tts-plus): WebSocket de DashScope, wss://.../api-ws/v1/inference (SDK dashscope)
voz a texto (qwen-audio-3.0-asr-flash): mismo POST de multimodal-generation con audio URL o Base64 (formato segun Model Studio; sin verificar en Token Plan)
voz en vivo (qwen-audio-3.0-realtime-plus): WebSocket .../api-ws/v1/realtime?model=... (NO implementado)"""
import base64
import json
import os
import socket
import time
import urllib.error
import urllib.request

from .api_engine import ErrorApi

HOST = 'https://token-plan.maas.qwencloudapi.com'
RUTA_GEN = '/api/v1/services/aigc/multimodal-generation/generation'
WS_TTS = 'wss://token-plan.maas.qwencloudapi.com/api-ws/v1/inference'
WS_REALTIME = 'wss://token-plan.maas.qwencloudapi.com/api-ws/v1/realtime?model=qwen-audio-3.0-realtime-plus'


def _post(url, cuerpo, key, timeout=120):
    req = urllib.request.Request(url, json.dumps(cuerpo).encode(), {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'ficha-motor/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ErrorApi('http ' + str(e.code) + ' ' + e.read()[:150].decode('utf-8', 'replace'))
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
        raise ErrorApi(type(e).__name__)


def _partes(d):
    try:
        return [c for ch in d['output']['choices'] for c in ch['message']['content']]
    except (KeyError, TypeError):
        return []


def imagen(modelo_id, prompt, key, host=HOST, size='1024*1024'):
    cuerpo = {'model': modelo_id, 'input': {'messages': [{'role': 'user', 'content': [{'text': prompt}]}]}, 'parameters': {'size': size}}
    urls = [c['image'] for c in _partes(_post(host + RUTA_GEN, cuerpo, key)) if c.get('image')]
    if not urls:
        raise ErrorApi('la respuesta no trae imagen')
    return 'IMAGEN ' + urls[0]


def voz_a_texto(modelo_id, audio, key, host=HOST):
    if not audio.startswith('http') and os.path.exists(audio):  # archivo local -> Data URI Base64
        audio = 'data:audio/wav;base64,' + base64.b64encode(open(audio, 'rb').read()).decode()
    cuerpo = {'model': modelo_id, 'input': {'messages': [{'role': 'user', 'content': [{'audio': audio}]}]}}
    textos = [c['text'] for c in _partes(_post(host + RUTA_GEN, cuerpo, key)) if c.get('text')]
    if not textos:
        raise ErrorApi('la respuesta no trae texto')
    return ' '.join(textos)


def texto_a_voz(modelo_id, texto, key, ws=WS_TTS, voz='longxiaochun', carpeta='.'):
    try:
        import dashscope
        from dashscope.audio.tts_v2 import AudioFormat, SpeechSynthesizer
    except ImportError:
        raise ErrorApi('falta el SDK: pip install dashscope')
    dashscope.api_key = key
    dashscope.base_websocket_api_url = ws
    try:
        audio = SpeechSynthesizer(model=modelo_id, voice=voz, format=AudioFormat.MP3_22050HZ_MONO_256KBPS).call(texto)
    except Exception as e:
        raise ErrorApi('tts ' + type(e).__name__ + ' ' + str(e)[:120])
    if not audio:
        raise ErrorApi('el TTS no devolvio audio')
    ruta = os.path.join(carpeta, 'voz_' + str(int(time.time() * 1000)) + '.mp3')
    open(ruta, 'wb').write(audio)
    return 'AUDIO ' + ruta


def fabrica_especiales(provs, host=HOST, ws=WS_TTS, carpeta='.'):
    def esp(modelo, tipo, texto):
        p = provs.get(modelo)
        if not p or not getattr(p, '_k', ''):
            raise ErrorApi('SIN_API: falta la clave de ' + modelo)
        if tipo == 'imagen':
            return imagen(p.modelo, texto, p._k, host)
        if tipo == 'voz-a-texto':
            return voz_a_texto(p.modelo, texto, p._k, host)
        if tipo == 'texto-a-voz':
            return texto_a_voz(p.modelo, texto, p._k, ws, carpeta=carpeta)
        if tipo == 'voz-en-vivo':
            raise ErrorApi('GAP_REALTIME_WEBSOCKET: va por WebSocket (' + WS_REALTIME + '), todavia no implementado')
        raise ErrorApi('GAP_TIPO_DESCONOCIDO: ' + tipo)
    return esp
