"""Gobierno determinista de Chat BOTS (mejoras 1, 8, 9, 15, 27, 28, 34, 37, 40 del bloque de Antonio).

LLM = razona / propone. Este codigo = controla / registra / vigila / recupera. Sin modelos, sin red, sin hilos.
Patrones reciclados (solo la idea, sin copiar runtime; todos MIT):
- OpenHands automation `watchdog.py`: RUNNING con `timeout_at` vencido -> FAILED (aqui: `trabajando` + t0 vencido -> `error` FAIL_TIMEOUT).
- OpenManus `app/agent/base.py` `is_stuck` (duplicate_threshold=2): respuestas iguales repetidas -> atasco.
- OpenHands agent-server `_secret_redaction.py`: nada con forma de token entra al stream ni a los recibos.
- Agent Zero `_goal`: objetivo del agente congelado con hash.
Persistencia: la misma fachada memoria_yaiwes que usa plugin.py (SQLite -> Graphiti/Graphify/state-hub -> bucket)."""
from __future__ import annotations
import hashlib, json, re, time

TIMEOUT_S = 180          # trabajando sin respuesta mas de esto -> watchdog
DUPLICADOS = 2           # OpenManus duplicate_threshold
MAX_RECIBOS = 200
_SECRETO = re.compile(r'(hf_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}'
                      r'|gsk_[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9_-]{20,}|xai-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})')
FALLOS = {'GAP_HARNESS_HTTP': 'FAIL_NETWORK', 'CHAT_OCUPADO_REINTENTA': 'FAIL_DEPENDENCY', 'FAIL_TIMEOUT': 'FAIL_TIMEOUT',
          'LOOP': 'FAIL_MODEL', 'respuesta vacia': 'FAIL_MODEL', 'FALTA_CONFIRMACION': 'FAIL_PERMISSION', 'SANDBOX': 'FAIL_TOOL'}


def redactar(txt):
    return _SECRETO.sub('***', str(txt or ''))


def _h(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:16]


def clasificar(error):
    """FAILURE CLASSIFIER (34): codigo de error -> clase."""
    e = str(error or '')
    for k, v in FALLOS.items():
        if k in e:
            return v
    return 'FAIL_TOOL' if e.startswith('exit') else 'FAIL_MODEL' if e else ''


def fijar_objetivo(a, objetivo):
    """GOAL LOCK (1): el objetivo se congela al crear; solo el Director lo cambia con desbloquear=True."""
    o = str(objetivo or '').strip()[:2000]
    if o:
        a['objetivo'] = o
        a['objetivo_hash'] = _h(o)


def objetivo_intacto(a):
    return not a.get('objetivo') or a.get('objetivo_hash') == _h(a['objetivo'])


def recibo(a, quien, que, entrada=None, salida=None):
    """RECEIPTS (8) + TRACE (37): WHO -> WHAT -> INPUT -> OUTPUT -> TIME -> HASH, encadenado al recibo anterior."""
    rs = a.setdefault('recibos', [])
    r = {'quien': quien, 'que': que, 'entrada': _h(entrada), 'salida': _h(salida), 'estado': a.get('estado'), 't': round(time.time(), 3),
         'prev': rs[-1]['hash'] if rs else ''}
    r['hash'] = _h(r)
    rs.append(r)
    a['recibos'] = rs[-MAX_RECIBOS:]
    return r


def atascado(a):
    """LOOP DETECTOR (15), como OpenManus is_stuck: las ultimas DUPLICADOS+1 respuestas del agente son iguales."""
    ult = [m.get('content') for m in (a.get('mensajes') or []) if m.get('role') == 'assistant'][-(DUPLICADOS + 1):]
    return len(ult) == DUPLICADOS + 1 and len(set(ult)) == 1


def vencido(a, ahora=None):
    """WATCHDOG (9) + HEARTBEAT (28): `trabajando` con proceso y sin respuesta mas de TIMEOUT_S."""
    return bool(a.get('pid')) and (ahora or time.time()) - float(a.get('t0') or 0) > TIMEOUT_S


def recuperar(a, motivo):
    """RECOVERY (10) minimo: suelta el proceso colgado, deja el agente en `error` con su clase; `reiniciar` lo vuelve a `activo`."""
    a.pop('pid', None); a.pop('t0', None); a.pop('_prog', None)
    a['estado'] = 'error'
    a['fallo'] = clasificar(motivo)
    return a
