# Plugin openai_sdk_lab: laboratorio TEMPORAL de pruebas del SDK de OpenAI.
# Lee las claves del banco secreto ya abierto en memoria (vault_hook). Nada de claves en el repo.
# status -> corre el motor (cache 10 min) y devuelve un resumen sin claves. invoke -> resultado limpio.
from __future__ import annotations

import base64
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CARPETA = chr(0x1F4C2) + ' laboratorio pruebas api sdk'
LAB = Path(__file__).resolve().parents[3] / CARPETA
ENGINE = LAB / 'Laboratorio Code de pruebas.py'
REPO = 'maxbry123-commits/router-universal-router-inteligente-'
RESULT_PATH = CARPETA + '/RESULTADOS-OPENAI-SDK.json'
SECRETO = re.compile('(sk-[A-Za-z0-9_-]{8,}|gh[ps]_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}|hf_[A-Za-z0-9]{10,})')
_lock = threading.Lock()
_state: dict[str, Any] = {'t': 0.0, 'res': None, 'running': False}


def _engine():
    spec = importlib.util.spec_from_file_location('lab_engine', str(ENGINE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ensure_sdk() -> None:
    try:
        import openai  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'openai'], check=False, timeout=100)


def _limpio(res: dict) -> dict:
    return json.loads(SECRETO.sub('[REDACTADO]', json.dumps(res, ensure_ascii=False, default=str)))


def _rows(res: dict) -> list:
    for v in res.values():
        if isinstance(v, list) and v and isinstance(v[0], dict) and 'key_index' in v[0]:
            return v
    return []


def _ok(row: dict) -> bool:
    return bool((row.get('models') or {}).get('ok')) and bool((row.get('responses') or {}).get('ok'))


def _resumen(res: dict) -> tuple[str, str]:
    if res.get('status') == 'blocked':
        return 'degraded', 'sin resultados: ' + str(res.get('reason', '?'))
    rows = _rows(res)
    buenas = sum(1 for r in rows if _ok(r))
    texto = '%d/%d claves PASS (models+responses) - checks %s/%s' % (buenas, len(rows), res.get('checks_pass'), res.get('checks_total'))
    return ('ok' if rows and buenas == len(rows) else 'degraded'), texto


def _publish(res: dict) -> None:
    tok = os.environ.get('GITHUB_TOKEN', '')
    if not tok:
        return
    try:
        url = 'https://api.github.com/repos/%s/contents/%s' % (REPO, urllib.parse.quote(RESULT_PATH))
        h = {'Authorization': 'Bearer ' + tok, 'User-Agent': 'riu-lab', 'Accept': 'application/vnd.github+json'}
        sha = None
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
                sha = json.loads(r.read()).get('sha')
        except Exception:
            sha = None
        estado, texto = _resumen(res)
        cuerpo = {'fecha_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'estado': estado, 'resumen': texto, 'resultado': _limpio(res)}
        data = {'message': 'lab: resultados OpenAI SDK [skip ci]', 'content': base64.b64encode(json.dumps(cuerpo, ensure_ascii=False, indent=1).encode()).decode()}
        if sha:
            data['sha'] = sha
        urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method='PUT'), timeout=25).read()
    except Exception:
        pass


def _worker() -> None:
    try:
        _ensure_sdk()
        res = _engine().run_all()
    except Exception as exc:  # noqa: BLE001
        res = {'status': 'blocked', 'reason': 'ERROR_' + type(exc).__name__}
    with _lock:
        _state.update(res=res, t=time.time(), running=False)
    if res.get('status') != 'blocked':
        _publish(res)


def _run(wait: float = 100.0):
    with _lock:
        res = _state['res']
        ttl = 30 if (res or {}).get('status') == 'blocked' else 600
        if (res is None or time.time() - _state['t'] > ttl) and not _state['running']:
            _state['running'] = True
            threading.Thread(target=_worker, daemon=True).start()
    fin = time.time() + wait
    while _state['running'] and time.time() < fin:
        time.sleep(0.5)
    return None if _state['running'] else _state['res']


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if action not in ('status', 'invoke'):
        return {'status': 'error', 'reason': 'accion desconocida: ' + str(action)}
    res = _run()
    if res is None:
        return {'status': 'degraded', 'reason': 'corriendo las pruebas; repite en 1 minuto'}
    estado, texto = _resumen(res)
    if action == 'invoke':
        return {'status': estado, 'reason': texto, 'resultado': _limpio(res)}
    return {'status': estado, 'reason': texto}
