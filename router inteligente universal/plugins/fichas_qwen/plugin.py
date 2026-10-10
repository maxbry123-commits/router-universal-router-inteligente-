"""fichas_qwen: las fichas 1, 2 y 3 (JSON, tal cual) conectadas al Router como plugin.

Ficha 1 = Team qwen (el modelo lo elige el selector del chat). Ficha 2 = Ask consil code. Ficha 3 = Ask consil frontend.
Cada ficha es un DAG de nodos: los nodos "goals" son datos (0 llamadas), los demas llaman a su modelo; los que no
dependen entre si van en paralelo. La SALIDA siempre se entrega.
Modelos: ids "ficha-*" del sello de la ficha 14 (sellos/), que se abre con la clave del banco del Router.
Acciones: status, fichas, chat, chat_async, resultado.
"""
from __future__ import annotations

import concurrent.futures as _cf
import hashlib
import json
import os
import re
import secrets
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

DIR = Path(__file__).resolve().parent
FICHAS = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((DIR / "fichas").glob("*.json"))}
ALIAS = {"1": "ficha1-modelos", "2": "ficha2-dag-codigo", "3": "ficha3-frontend"}
_POOL = _cf.ThreadPoolExecutor(max_workers=8, thread_name_prefix="fichas_qwen")
_LOCK = threading.Lock()
_PROCESOS: dict[str, tuple[Any, float]] = {}
_MODELOS: dict[str, dict[str, Any]] = {}
_PROGRESO: dict[str, dict[str, str]] = {}


def _abrir_sello(blob: bytes) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    clave = os.environ.get("FICHA_CLAVE_BANCO") or os.environ.get("RIU_VAULT_PASSPHRASE") or ""
    if not clave:
        raise RuntimeError("SIN_CLAVE_DEL_BANCO")
    cab = b"FICHA-SELLO-1"
    k = len(cab)
    llave = hashlib.scrypt(clave.encode(), salt=blob[k:k + 16], n=2 ** 15, r=8, p=1, dklen=32, maxmem=2 ** 26)
    return AESGCM(llave).decrypt(blob[k + 16:k + 28], blob[k + 28:], cab).decode("utf-8")


def _modelos() -> dict[str, dict[str, Any]]:
    if not _MODELOS:
        for f in sorted((DIR / "sellos").glob("*.sello")):
            texto = _abrir_sello(f.read_bytes())
            for m in re.finditer(r"^ {6}(ficha-[a-z0-9]+):\n((?: {8}.*\n?)+)", texto, re.M):
                cuerpo = m.group(2)
                url = re.search(r'baseURL:\s*"([^"]+)"', cuerpo)
                mid = re.search(r'models:\s*\[\{id:\s*"([^"]+)"', cuerpo)
                claves = re.findall(r'apiKey:\s*"([^"<]+)"', cuerpo)
                if url and mid and claves:
                    _MODELOS[m.group(1)] = {"url": url.group(1).rstrip("/"), "modelo": mid.group(1), "claves": claves}
    return _MODELOS


def _cfg(ficha: dict[str, Any]) -> tuple[int, int, int, int]:
    # lee de la ficha activa: timeout API (s), intentos, tokens de salida, limite de chars por llamada
    d = ficha.get('dsl') or {}
    try:
        return (int(d['timeouts']['api_seconds']), int(d['retry']['max_attempts']),
                int(d['tokens']['max_output_tokens']), int(ficha['motor']['limite_llamada_chars']))
    except (KeyError, TypeError, ValueError) as x:
        raise RuntimeError('FICHA_SIN_CONFIG:' + repr(x))


def _llamar(modelo: str, prompt: str, ficha: dict[str, Any]) -> str:
    m = _modelos().get(modelo)
    if not m:
        raise RuntimeError('MODELO_NO_ESTA_EN_EL_SELLO:' + str(modelo))
    if not m['claves']:
        raise RuntimeError('MODELO_SIN_CLAVE:' + str(modelo))
    api_s, intentos, max_tokens, limite = _cfg(ficha)
    if len(prompt) > limite:
        raise RuntimeError('INPUT_SUPERA_LIMITE:%d>%d' % (len(prompt), limite))
    fin = time.time() + api_s  # 90 s TOTAL por nodo; los reintentos van dentro de ese tiempo
    ultimo = ''
    for n in range(intentos):  # mismo modelo siempre; nunca otro
        resto = fin - time.time()
        if resto < 1:
            break
        clave = m['claves'][n % len(m['claves'])]
        cuerpo = json.dumps({'model': m['modelo'], 'messages': [{'role': 'user', 'content': prompt}],
                             'max_tokens': max_tokens}).encode()
        req = urllib.request.Request(m['url'] + '/chat/completions', data=cuerpo, method='POST',
                                     headers={'Authorization': 'Bearer ' + clave, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=resto) as r:
                d = json.loads(r.read().decode('utf-8', 'replace'))
            t = str(((d.get('choices') or [{}])[0].get('message') or {}).get('content') or '').strip()
            if t:
                return t
            ultimo = 'respuesta vacia'
        except Exception as x:  # noqa: BLE001
            ultimo = str(x)[:200]
    raise RuntimeError('MODELO_SIN_RESPUESTA:%s:%s' % (modelo, ultimo))


def _elegido(ficha: dict[str, Any], pedido: str) -> str:
    sel = ficha.get("selector") or []
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())  # noqa: E731
    for s in sel:
        if pedido and (pedido == s.get("id") or norm(pedido) in (norm(s.get("id")), norm(s.get("nombre")))):
            return s["id"]
    return None if sel else pedido  # modelo que el selector no reconoce: nunca cambiar de modelo en silencio


_QW = {'ficha-qwen38max': 'qw-qwen-3-8-max', 'ficha-qwen38flash': 'qw-qwen-3-8-flash', 'ficha-qwen37max': 'qw-qwen-3-7-max',
       'ficha-qwen37plus': 'qw-qwen-3-7-plus', 'ficha-qwen36flash': 'qw-qwen-3-6-flash', 'ficha-dsv4pro': 'qw-deepseek-v4-pro',
       'ficha-dsv4pro0813': 'qw-deepseek-v4-pro-0813', 'ficha-dsv4flash': 'qw-deepseek-v4-flash', 'ficha-glm52': 'qw-glm-5-2'}
_ESCRIBE = ('github_escribir', 'hf_escribir', 'hf_almacenamiento')
_VERBOS = ('modifica', 'edita', 'corrige', 'cambia', 'crea ', 'escribe', 'borra', 'elimina', 'sube', 'commit', 'push', 'despliega',
           'reinicia', 'restaura', 'aplica', 'implementa', 'arregla', 'actualiza', 'reemplaza', 'mueve', 'renombra')


def _muta(texto: str) -> bool:
    t = texto.lower()
    return any(v in t for v in _VERBOS)


def _pc():
    # el Harness original (puente_chat): se reutiliza el modulo que el Router ya cargo
    import importlib.util
    import sys
    for m in list(sys.modules.values()):
        try:
            f = str(getattr(m, '__file__', '') or '').replace(chr(92), '/')
            if f.endswith('puente_chat/plugin.py') and hasattr(m, '_chat'):
                return m
        except Exception:  # noqa: BLE001
            continue
    spec = importlib.util.spec_from_file_location('puente_chat_desde_fichas', DIR.parent / 'puente_chat' / 'plugin.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _llamar_harness(modelo: str, prompt: str, ficha: dict[str, Any], n: dict[str, Any], opts: dict[str, Any]) -> str:
    # Ask consil por el Harness original (puente_chat): mismo HTTP, mismas herramientas, mismo modelo Qwencloud
    qw = _QW.get(modelo)
    pc = _pc()
    if not qw or qw not in pc.FICHAS:
        raise RuntimeError('FICHA_QW_NO_EXISTE:' + str(modelo))
    api_s, _, max_tok, limite = _cfg(ficha)
    api_s = int(n.get('timeout_s') or api_s)
    max_tok = int(n.get('max_output_tokens') or max_tok)
    if len(prompt) > limite:
        raise RuntimeError('INPUT_SUPERA_LIMITE:%d>%d' % (len(prompt), limite))
    escribe = n.get('id') == 'N4' and bool(opts.get('aprobado'))
    r = pc._chat({'model': qw, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tok,
                  'sesion': opts.get('sesion') or 'fichas', 'presupuesto_s': api_s, 'solo_lectura': not escribe})
    if r.get('error'):
        det = str(r.get('detalle') or r.get('mensaje') or '')[:160]
        if 'tool' in det.lower() and '400' in det:
            raise RuntimeError('MODELO_SIN_TOOLS:' + qw)
        raise RuntimeError('HARNESS_' + str(r['error']) + (':' + det if det else ''))
    t = str(((r.get('choices') or [{}])[0].get('message') or {}).get('content') or '').strip()
    if not t:
        raise RuntimeError('RESPUESTA_VACIA:' + qw)
    usadas = [x for x in (r.get('herramientas') or []) if isinstance(x, dict)]
    opts.setdefault('herr', {})[str(n.get('id'))] = [{'herramienta': x.get('herramienta'), 'ok': bool(x.get('ok'))} for x in usadas]
    if escribe and opts.get('muta') and not any(x.get('ok') and x.get('herramienta') in _ESCRIBE for x in usadas):
        raise RuntimeError('EJECUCION_SIN_EVIDENCIA: la tarea pedia cambios y ninguna herramienta de escritura termino bien')
    return t


def _prog(pid: str, nodo: str, estado: str) -> None:
    if pid:
        _PROGRESO.setdefault(pid, {})[nodo] = estado


def _texto_prog(pid: str) -> str:
    sim = {'ok': '✓', 'gap': '✗'}
    return ' | '.join('%s %s' % (n, sim.get(e, 'trabajando...')) for n, e in list(_PROGRESO.get(pid, {}).items()))


def _correr(ficha: dict[str, Any], mensaje: str, modelo: str, pid: str = "", opts: dict[str, Any] | None = None) -> tuple[str, list[dict[str, Any]]]:
    nodos = {n["id"]: n for n in ficha.get("nodos", [])}
    orden = [n["id"] for n in ficha.get("nodos", [])]
    elegido = _elegido(ficha, modelo)
    if elegido is None:
        return 'GAP MODELO_SELECTOR_INVALIDO: ' + repr(modelo) + ' no esta en el selector', []
    opts = {} if opts is None else opts
    out: dict[str, str] = {}

    def nodo(i: str) -> str:
        n = nodos[i]
        if n.get('tipo') == 'goals':
            r = chr(10).join(g.get('texto', '') for g in n.get('goals', []) if g.get('texto') and g.get('texto') != 'PONER AQUI')
            _prog(pid, i, 'ok')
            return r
        _prog(pid, i, 'trabajando')
        nl = chr(10)
        ctx = (nl * 2).join('[%s]%s%s' % (d, nl, out[d]) for d in n.get('depende_de', []) if out.get(d))
        prompt = n.get('rol', '') + nl * 2 + 'TAREA DEL DIRECTOR (INPUT BLOCK VERBATIM):' + nl + mensaje + nl * 2 + ctx
        if n.get('id') == 'N4' and opts.get('muta') and not opts.get('aprobado'):
            prompt += nl * 2 + 'AVISO DEL SISTEMA: falta la aprobacion del Director. NO ejecutes cambios ni uses herramientas de escritura. Entrega solo el PLAN (pasos, archivos, riesgos) y termina con la linea ESPERANDO_APROBACION. El Director aprueba escribiendo /aprobar al inicio de su mensaje.'
        mod = elegido if n.get('modelo') == 'selector' else n.get('modelo')
        try:
            r = _llamar_harness(mod, prompt, ficha, n, opts)
        except Exception as x:  # noqa: BLE001
            r = 'GAP %s (%s): %s' % (i, mod, x)
        _prog(pid, i, 'gap' if r.startswith('GAP') else 'ok')
        return r

    pend = list(orden)
    while pend:
        listos = [i for i in pend if all(d in out for d in nodos[i].get("depende_de", []))]
        if not listos:
            break
        with _cf.ThreadPoolExecutor(max_workers=len(listos)) as ex:
            futs = {i: ex.submit(nodo, i) for i in listos}
            for i, f in futs.items():
                out[i] = f.result()
                pend.remove(i)
    usados = {d for n in nodos.values() for d in n.get("depende_de", [])}
    finales = [i for i in orden if i not in usados and nodos[i].get("tipo") != "goals"]
    final = out.get(finales[-1], "") if finales else ""
    if not final or final.startswith("GAP"):
        final = next((out[i] for i in reversed(orden) if out.get(i) and not out[i].startswith("GAP")
                      and nodos[i].get("tipo") != "goals"), final)
    traza = [{"nodo": i, "modelo": (elegido if nodos[i].get("modelo") == "selector" else nodos[i].get("modelo")) or "goals",
              "rol": {"N1":"analiza (ask consil)","N2":"analiza (ask consil)","N3":"analiza (ask consil)","N4":"ejecuta","N6":"revisa y refactoriza","N7":"revisa y refactoriza"}.get(i, ""), "ok": not out.get(i, "").startswith("GAP"), "herramientas": opts.get("herr", {}).get(i, [])} for i in orden if i in out]
    return final, traza


def _chat(p: dict[str, Any]) -> dict[str, Any]:
    fid = ALIAS.get(str(p.get("ficha_qwen") or ""), str(p.get("ficha_qwen") or ""))
    if fid not in FICHAS:
        return {"error": "FICHA_NO_EXISTE", "validas": list(ALIAS)}
    mensaje = str(p.get("message") or "")
    if not mensaje:
        mensaje = next((str(m.get("content", "")) for m in reversed(p.get("messages") or []) if m.get("role") == "user"), "")
    t0 = time.time()
    ap = mensaje.lstrip().lower().startswith('/aprobar')
    if ap:
        mensaje = mensaje.lstrip()[len('/aprobar'):].lstrip()
    opts = {'aprobado': ap, 'muta': _muta(mensaje), 'sesion': str(p.get("sesion") or 'fichas')[:60]}
    salida, traza = _correr(FICHAS[fid], mensaje, str(p.get("modelo") or ""), str(p.get("_pid") or ""), opts)
    return {"model": FICHAS[fid].get("ficha", fid), "reply": salida,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": salida}}],
            "traza": traza, "herramientas": [dict(x, nodo=k) for k, v in opts.get("herr", {}).items() for x in v], "ms": int((time.time() - t0) * 1000)}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    p = payload or {}
    if action == "status":
        return {"ok": True, "fichas": list(FICHAS), "sellos": len(list((DIR / "sellos").glob("*.sello")))}
    if action == "fichas":
        return {"fichas": [{"n": k, "id": v, "nombre": FICHAS[v].get("ficha")} for k, v in ALIAS.items() if v in FICHAS]}
    if action == "chat":
        return _chat(p)
    if action == "chat_async":
        clave = secrets.token_urlsafe(24)
        with _LOCK:
            for k, (fut, t) in list(_PROCESOS.items()):
                if time.time() - t > 900 and fut.done():
                    del _PROCESOS[k]
                    _PROGRESO.pop(k, None)
            _PROCESOS[clave] = (_POOL.submit(_chat, dict(p, _pid=clave)), time.time())
        return {"estado": "procesando", "proceso_id": clave}
    if action == "resultado":
        item = _PROCESOS.get(str(p.get("proceso_id") or ""))
        if not item:
            return {"error": "PROCESO_NO_EXISTE"}
        if not item[0].done():
            return {"estado": "procesando", "proceso_id": p.get("proceso_id"), "progreso": _texto_prog(str(p.get("proceso_id") or ""))}
        try:
            r = item[0].result()
            if isinstance(r, dict) and "reply" in r:
                r.setdefault("estado", "completado")
            return r
        except Exception as x:  # noqa: BLE001
            return {"error": "CHAT_FAILED", "detalle": type(x).__name__}
    return {"error": "ACCION_DESCONOCIDA"}
