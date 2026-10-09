import json
import os
import random
import socket
import time
import urllib.error
import urllib.request

from .limites import Guarda

TIMEOUT = 90            # 1,5 minutos maximo por llamada
LIMITE_LLAMADA = 18000  # al llegar a 18k caracteres la llamada se reinicia partida en bloques
BLOQUE = 8500           # caracteres por bloque
MAX_ESPERA = 120        # si un proveedor pide esperar mas, se pasa al siguiente


class ErrorApi(Exception):
    pass


class Agotado(ErrorApi):
    pass


class Proveedor:
    def __init__(self, nombre, url, modelo, key_env, perfil='libre', carpeta='estado'):
        self.nombre, self.url, self.modelo, self.key_env = nombre, url, modelo, key_env
        self.guarda = Guarda(nombre, perfil, carpeta)

    def key(self):
        return os.environ.get(self.key_env, '')


def chars(mensajes):
    return sum(len(m['content']) for m in mensajes)


def tokens_est(mensajes):
    return chars(mensajes) // 4 + 1


def cargar_proveedores(ruta, carpeta):
    with open(ruta) as f:
        return [Proveedor(carpeta=carpeta, **d) for d in json.load(f)]


class Motor:
    """Llama al modelo. Sistemas de recuperacion:
    1 reintentos con espera creciente (429/5xx/timeout, respeta Retry-After)
    2 cambio de API/proveedor cuando uno falla o llega a su limite diario
    3 llamada partida en bloques de 8500 caracteres al llegar a 18000
    4 peticion reducida (contexto recortado, menos tokens) como ultimo intento
    """

    def __init__(self, proveedores, timeout=TIMEOUT, reintentos=3, dormir=time.sleep, pulso=None):
        self.provs = proveedores
        self.timeout = timeout
        self.reintentos = reintentos
        self._dormir = dormir
        self.pulso = pulso or (lambda: None)
        self.i = 0
        self.bitacora = []

    def dormir(self, seg):
        fin = time.time() + seg
        while True:
            self.pulso()
            resto = fin - time.time()
            if resto <= 0:
                return
            self._dormir(min(5.0, resto))

    def _post(self, p, mensajes, max_tokens):
        cuerpo = json.dumps({'model': p.modelo, 'messages': mensajes, 'max_tokens': max_tokens}).encode()
        req = urllib.request.Request(p.url, cuerpo, {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + p.key()})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read())
        return d['choices'][0]['message']['content']

    def _con_reintentos(self, p, mensajes, max_tokens):  # sistema 1
        est = tokens_est(mensajes) + max_tokens
        ultimo = 'sin intento'
        for n in range(self.reintentos):
            e = p.guarda.espera(est)
            if e < 0:
                raise ErrorApi('peticion demasiado grande para ' + p.nombre)
            if e > MAX_ESPERA:
                raise Agotado(p.nombre + ' agotado, espera ' + str(int(e)) + ' s')
            if e > 0:
                self.dormir(e)
            self.pulso()
            p.guarda.registrar(est)
            try:
                return self._post(p, mensajes, max_tokens)
            except urllib.error.HTTPError as h:
                if h.code not in (429, 500, 502, 503, 504):
                    raise ErrorApi(p.nombre + ' error ' + str(h.code))
                ultimo = p.nombre + ' http ' + str(h.code)
                try:
                    pausa = float(h.headers.get('Retry-After', ''))
                except Exception:
                    pausa = min(30.0, 2 ** n + random.random())
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as x:
                ultimo = p.nombre + ' ' + type(x).__name__
                pausa = min(30.0, 2 ** n + random.random())
            self.bitacora.append(ultimo)
            if pausa > 0:
                self.dormir(pausa)
        raise ErrorApi('reintentos agotados: ' + ultimo)

    def _ronda(self, mensajes, max_tokens):  # sistemas 2 y 4
        errores = []
        for intento in range(2):
            ms, mt = (mensajes, max_tokens) if intento == 0 else (self._reducir(mensajes), max(256, max_tokens // 2))
            for p in self.provs[self.i:] + self.provs[:self.i]:
                try:
                    r = self._con_reintentos(p, ms, mt)
                    self.i = self.provs.index(p)
                    return r
                except ErrorApi as e:
                    errores.append(str(e))
                    self.bitacora.append('cambio de API: ' + str(e))
        raise ErrorApi(' | '.join(errores))

    def _reducir(self, mensajes):
        sis = [m for m in mensajes if m['role'] == 'system']
        ult = mensajes[-1]
        return sis + [{'role': ult['role'], 'content': ult['content'][-6000:]}] if ult['role'] != 'system' else sis

    def _por_bloques(self, mensajes, max_tokens):  # sistema 3
        texto = chr(10).join(m['role'] + ': ' + m['content'] for m in mensajes)
        partes = [texto[k:k + BLOQUE] for k in range(0, len(texto), BLOQUE)]
        notas = ''
        for k, parte in enumerate(partes, 1):
            ultima = k == len(partes)
            sis = 'Parte ' + str(k) + '/' + str(len(partes)) + ' de una peticion larga. Notas previas: ' + notas[-1500:]
            sis += ' Da la respuesta final completa.' if ultima else ' Responde SOLO con notas breves de lo importante.'
            salida = self._ronda([{'role': 'system', 'content': sis}, {'role': 'user', 'content': parte}], max_tokens)
            if ultima:
                return salida
            notas += ' [' + str(k) + '] ' + salida[:600]

    def llamar(self, mensajes, max_tokens=1024):
        if chars(mensajes) >= LIMITE_LLAMADA:
            return self._por_bloques(mensajes, max_tokens)
        return self._ronda(mensajes, max_tokens)
