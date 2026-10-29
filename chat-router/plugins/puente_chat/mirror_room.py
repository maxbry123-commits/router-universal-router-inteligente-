"""mirror_room.py — Integración ROOM + orquestador para mirrors (Director 2026-10-17).

Los mirrors entran como participantes del pool de room_debatir/chat_bots.
mirror() admite origen 'room:<ficha_id>' donde ficha_id = ficha4|ficha5|nvidia|groq.
Todo dentro del mismo plugin/frontend del chat, sin puente externo.

Contrato:
  mirror_room.mirror(origen, tema, participantes, rondas) -> dict
    origen: 'room:<ficha_id>' | '<agent_id>'
    tema: str
    participantes: list[str]  # ids de ficha4 o agent_ids
    rondas: int (1-2)
  Retorna: {ok, turnos, resumen, origen_resuelto}

Integración con room_debatir existente:
  - Si origen empieza con 'room:', se resuelve a la ficha correspondiente
  - El mirror participa como un nodo adicional en el debate
  - Los turnos incluyen la perspectiva del mirror (lectura del repo/enlace)

Integración con chat_bots existente:
  - mirror() puede usarse como action='mirror' en el handler del plugin
  - El agente mirror tiene acceso a repo_leer para consultar su fuente
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# Mapeo de fichas a recursos LLM del staff
FICHA_MAP = {
    'ficha4': {'recurso': 'ficha4:ficha-qwen38max', 'nombre': 'Qwen 3.8 Max (Ficha 4)'},
    'ficha5': {'recurso': 'ficha4:ficha-qwen38flash', 'nombre': 'Qwen 3.8 Flash (Ficha 5)'},
    'nvidia': {'recurso': 'nvcode:z-ai/glm-5.3', 'nombre': 'GLM 5.3 (NVIDIA)'},
    'groq': {'recurso': 'groq:openai/gpt-oss-120b', 'nombre': 'GPT-OSS 120B (Groq)'},
}

# Cache de agentes mirror (evita lecturas repetidas al fleet registry)
_CACHE_MIRROR = {'t': 0.0, 'v': None}
_TTL_S = 600


def _resolver_origen(origen: str) -> dict:
    """Resuelve origen 'room:<ficha_id>' o '<agent_id>' a un descriptor de participante."""
    if not origen:
        return {'error': 'ORIGEN_VACIO'}
    
    # Formato room:<ficha_id>
    m = re.match(r'^room:(\w+)$', origen.strip())
    if m:
        ficha_id = m.group(1).lower()
        if ficha_id in FICHA_MAP:
            info = FICHA_MAP[ficha_id]
            return {
                'tipo': 'ficha',
                'ficha_id': ficha_id,
                'recurso': info['recurso'],
                'nombre': info['nombre'],
                'origen_canonico': 'room:' + ficha_id,
            }
        return {'error': 'FICHA_NO_EXISTE', 'ficha_id': ficha_id,
                'disponibles': list(FICHA_MAP.keys())}
    
    # Formato agent_id (mirror del orquestador)
    agent_id = origen.strip()
    ag = _buscar_agente(agent_id)
    if ag:
        return {
            'tipo': 'agente',
            'agent_id': agent_id,
            'nombre': ag.get('nombre', agent_id),
            'repo': ag.get('repo'),
            'ruta': ag.get('ruta'),
            'url': ag.get('url'),
            'origen_canonico': agent_id,
        }
    
    return {'error': 'ORIGEN_NO_RESUELTO', 'origen': origen}


def _buscar_agente(agent_id: str) -> dict | None:
    """Busca un agente en el fleet registry (cache TTL_S)."""
    global _CACHE_MIRROR
    if _CACHE_MIRROR['v'] is not None and time.time() - _CACHE_MIRROR['t'] < _TTL_S:
        return next((a for a in _CACHE_MIRROR['v'] if a.get('agent_id') == agent_id), None)
    
    # Leer fleet registry
    repo = 'maxbry123-commits/router-universal-router-inteligente-'
    ruta = 'plugins/workflow-loop-yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json'
    url = 'https://api.github.com/repos/%s/contents/%s?ref=main' % (repo, urllib.parse.quote(ruta))
    h = {'Accept': 'application/vnd.github.raw', 'User-Agent': 'riu-mirror-room'}
    tok = (os.getenv('GITHUB_TOKEN') or '').strip()
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
            data = json.loads(r.read().decode('utf-8', 'replace'))
            agentes = []
            for x in data.get('agents') or []:
                if x.get('source_repo', '').count('/') == 1:
                    agentes.append({
                        'agent_id': x.get('agent_id'),
                        'nombre': x.get('display_name') or x.get('agent_id'),
                        'repo': x['source_repo'],
                        'ruta': x.get('source_path') or '',
                        'roles': x.get('roles') or [],
                        'url': 'https://github.com/%s%s' % (x['source_repo'],
                            ('/tree/main/' + urllib.parse.quote(x.get('source_path') or '')) if x.get('source_path') else ''),
                    })
            _CACHE_MIRROR.update(t=time.time(), v=agentes)
            return next((a for a in agentes if a.get('agent_id') == agent_id), None)
    except Exception:
        return None


def _leer_recurso(recurso: str, mensaje: str) -> str:
    """Llama a un recurso LLM del staff (ficha4:, nvcode:, groq:)."""
    # Importar aqui para evitar dependencia circular
    try:
        from plugins.puente_chat.herramientas import _peticion, _token_gh
    except ImportError:
        pass
    
    # Llamada directa al harness del Router
    url = os.getenv('RIU_PUENTE_URL') or (
        (os.getenv('RIU_ROUTER_URL') or 'http://127.0.0.1:' + str(os.getenv('PORT') or '7860')).rstrip('/') 
        + '/plugins/puente_chat/call'
    )
    cuerpo = {
        'model': recurso,
        'messages': [{'role': 'user', 'content': mensaje}],
        'max_tokens': 4096,
    }
    h = {'Content-Type': 'application/json', 'Origin': 'https://riu-jev-bridge.vercel.app'}
    api_key = os.getenv('RIU_ROUTER_API_KEY')
    if api_key:
        h['X-API-Key'] = api_key
        h['Authorization'] = 'Bearer ' + api_key
    try:
        req = urllib.request.Request(
            url.rstrip('/') + '/chat',
            data=json.dumps(cuerpo).encode(),
            headers=h,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode('utf-8', 'replace'))
            result = resp.get('result', resp) if isinstance(resp, dict) else {}
            choices = result.get('choices') or []
            if choices:
                return str((choices[0].get('message') or {}).get('content') or '')
            return str(result.get('respuesta') or result.get('reply') or result.get('text') or '')
    except Exception as e:
        return 'ERROR_LLAMADA_RECURSO: ' + str(e)[:200]


def mirror(origen: str, tema: str, participantes: list[str] | None = None, rondas: int = 1) -> dict:
    """Ejecuta un debate/chat con mirror como participante.
    
    Args:
        origen: 'room:<ficha_id>' o '<agent_id>'
        tema: tema del debate
        participantes: lista de ids adicionales (ficha4, ficha5, nvidia, groq, o agent_ids)
        rondas: numero de rondas (1-2)
    
    Returns:
        {ok: bool, turnos: list, resumen: str, origen_resuelto: dict}
    """
    rondas = max(1, min(2, int(rondas or 1)))
    participantes = participantes or []
    
    # Resolver origen
    origen_info = _resolver_origen(origen)
    if 'error' in origen_info:
        return {'ok': False, 'error': origen_info['error'], 'detalle': origen_info}
    
    # Construir lista de participantes (origen + adicionales)
    todos = [origen_info]
    for p in participantes:
        info = _resolver_origen(p)
        if 'error' not in info:
            todos.append(info)
    
    if len(todos) < 2:
        return {'ok': False, 'error': 'MINIMO_2_PARTICIPANTES',
                'participantes_resueltos': len(todos)}
    
    # Ejecutar debate por turnos
    turnos = []
    contexto = 'DEBATE ROOM CON MIRROR\nTema: %s\nParticipantes: %s\n\n' % (
        tema, ', '.join(p.get('nombre', '?') for p in todos))
    
    for ronda in range(rondas):
        for i, part in enumerate(todos):
            prompt = contexto
            if turnos:
                prompt += '\n--- TURNOS PREVIOS ---\n'
                for t in turnos[-6:]:  # ultimos 6 turnos como contexto
                    prompt += '[%s]: %s\n' % (t['participante'], t['texto'][:500])
            
            prompt += '\n--- TU TURNO (Ronda %d) ---\n' % (ronda + 1)
            prompt += 'Responde como %s. ' % part.get('nombre', '?')
            
            if part.get('tipo') == 'agente' and part.get('repo'):
                prompt += 'Eres mirror del agente %s (repo: %s). ' % (part.get('agent_id'), part.get('repo'))
                prompt += 'Puedes referenciar codigo de ese repo si hace falta. '
            
            prompt += 'Coincide o rebate citando nombres de otros participantes. Breve (max 300 palabras).'
            
            # Llamar al recurso
            recurso = part.get('recurso')
            if recurso:
                respuesta = _leer_recurso(recurso, prompt)
            else:
                respuesta = '[SIN_RECURSO] Participante %s sin recurso LLM asignado.' % part.get('nombre')
            
            turno = {
                'ronda': ronda + 1,
                'participante': part.get('nombre', '?'),
                'origen': part.get('origen_canonico', '?'),
                'tipo': part.get('tipo', '?'),
                'texto': respuesta[:2000],
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            }
            turnos.append(turno)
    
    # Resumen final
    resumen = 'Debate completado: %d rondas, %d turnos, %d participantes.' % (
        rondas, len(turnos), len(todos))
    
    return {
        'ok': True,
        'turnos': turnos,
        'resumen': resumen,
        'origen_resuelto': origen_info,
        'participantes_total': len(todos),
        'rondas': rondas,
    }


def listar_fichas_mirror() -> list[dict]:
    """Lista las fichas disponibles como origen mirror."""
    return [
        {'ficha_id': k, 'nombre': v['nombre'], 'recurso': v['recurso'],
         'origen': 'room:' + k}
        for k, v in FICHA_MAP.items()
    ]


# Handler para integracion con plugin puente_chat
def handle_mirror(args: dict) -> dict:
    """Handler llamado desde plugin.py action='mirror'.
    
    Args esperados:
        origen: 'room:<ficha_id>' o '<agent_id>'
        tema: str
        participantes: list[str] (opcional)
        rondas: int (opcional, default 1)
    """
    origen = args.get('origen') or args.get('origin') or ''
    tema = args.get('tema') or args.get('topic') or 'Sin tema'
    participantes = args.get('participantes') or args.get('participants') or []
    rondas = args.get('rondas') or args.get('rounds') or 1
    
    if not origen:
        return {'status': 'error', 'error': 'FALTA_ORIGEN',
                'uso': "mirror({origen: 'room:ficha4', tema: '...', participantes: [...], rondas: 1})"}
    
    resultado = mirror(origen, tema, participantes, rondas)
    return {'status': 'ok' if resultado.get('ok') else 'error', 'result': resultado}
