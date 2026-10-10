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


def _llamar(modelo: str, prompt: str, max_tokens: int = 8000) -> str:
    m = _modelos().get(modelo)
    if not m:
        raise RuntimeError("MODELO_NO_ESTA_EN_EL_SELLO:" + str(modelo))
    ultimo = ""
    for _vuelta in range(2):  # mismo modelo siempre; nunca otro
        for clave in m["claves"]:
            cuerpo = json.dumps({"model": m["modelo"], "messages": [{"role": "user", "content": prompt}],
                                 "max_tokens": max_tokens}).encode()
            req = urllib.request.Request(m["url"] + "/chat/completions", data=cuerpo, method="POST",
                                         headers={"Authorization": "Bearer " + clave, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=170) as r:
                    d = json.loads(r.read().decode("utf-8", "replace"))
                t = str(((d.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
                if t:
                    return t
                ultimo = "respuesta vacia"
            except Exception as x:  # noqa: BLE001
                ultimo = str(x)[:200]
    raise RuntimeError("MODELO_SIN_RESPUESTA:%s:%s" % (modelo, ultimo))


def _elegido(ficha: dict[str, Any], pedido: str) -> str:
    sel = ficha.get("selector") or []
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())  # noqa: E731
    for s in sel:
        if pedido and (pedido == s.get("id") or norm(pedido) in (norm(s.get("id")), norm(s.get("nombre")))):
            return s["id"]
    return sel[0]["id"] if sel else pedido


def _correr(ficha: dict[str, Any], mensaje: str, modelo: str) -> tuple[str, list[dict[str, Any]]]:
    nodos = {n["id"]: n for n in ficha.get("nodos", [])}
    orden = [n["id"] for n in ficha.get("nodos", [])]
    elegido = _elegido(ficha, modelo)
    out: dict[str, str] = {}

    def nodo(i: str) -> str:
        n = nodos[i]
        if n.get("tipo") == "goals":
            return "\n".join(g.get("texto", "") for g in n.get("goals", []) if g.get("texto") and g.get("texto") != "PONER AQUI")
        ctx = "\n\n".join("[%s]\n%s" % (d, out[d]) for d in n.get("depende_de", []) if out.get(d))
        prompt = "%s\n\nTAREA DEL DIRECTOR (INPUT BLOCK VERBATIM):\n%s\n\n%s" % (n.get("rol", ""), mensaje, ctx)
        mod = elegido if n.get("modelo") == "selector" else n.get("modelo")
        try:
            return _llamar(mod, prompt)
        except Exception as x:  # noqa: BLE001
            return "GAP %s (%s): %s" % (i, mod, x)

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
              "rol": {"N1":"analiza (ask consil)","N2":"analiza (ask consil)","N3":"analiza (ask consil)","N4":"ejecuta","N6":"revisa y refactoriza","N7":"revisa y refactoriza"}.get(i, ""), "ok": not out.get(i, "").startswith("GAP")} for i in orden if i in out]
    return final, traza


def _chat(p: dict[str, Any]) -> dict[str, Any]:
    fid = ALIAS.get(str(p.get("ficha_qwen") or ""), str(p.get("ficha_qwen") or ""))
    if fid not in FICHAS:
        return {"error": "FICHA_NO_EXISTE", "validas": list(ALIAS)}
    mensaje = str(p.get("message") or "")
    if not mensaje:
        mensaje = next((str(m.get("content", "")) for m in reversed(p.get("messages") or []) if m.get("role") == "user"), "")
    t0 = time.time()
    salida, traza = _correr(FICHAS[fid], mensaje, str(p.get("modelo") or ""))
    return {"model": FICHAS[fid].get("ficha", fid), "reply": salida,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": salida}}],
            "traza": traza, "ms": int((time.time() - t0) * 1000)}


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
            _PROCESOS[clave] = (_POOL.submit(_chat, dict(p)), time.time())
        return {"estado": "procesando", "proceso_id": clave}
    if action == "resultado":
        item = _PROCESOS.get(str(p.get("proceso_id") or ""))
        if not item:
            return {"error": "PROCESO_NO_EXISTE"}
        if not item[0].done():
            return {"estado": "procesando", "proceso_id": p.get("proceso_id")}
        try:
            return item[0].result()
        except Exception as x:  # noqa: BLE001
            return {"error": "CHAT_FAILED", "detalle": type(x).__name__}
    return {"error": "ACCION_DESCONOCIDA"}
