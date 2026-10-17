"""Plugin watchdog (Director 2026-10-16): vigila el Router y repara lo que se puede reparar solo.

Ruta: el hilo del watchdog y la UI entran por el HARNESS (PluginHost.call); los otros plugins se revisan SIEMPRE con host.call/host.health.
Que vigila en cada ronda (cada RIU_WATCHDOG_S, 60 s por defecto; 0 = sin hilo):
  1. health   GET <router>/health local (RIU_WATCHDOG_HEALTH_URL o http://127.0.0.1:$PORT/health).
  2. fichas   plugins del host: invalid/degraded -> host.sync() (relee fichas) y vuelve a probar; puente_chat debe listar modelos.
  3. memoria  autosync SQLite -> bucket (storage_lifecycle.STATUS): hilo muerto -> se rearranca; sync viejo o con error -> sync manual.
  4. agentes  plugins cuyo id contiene agent/orquest: health; si exponen 'reiniciar' se llama una vez por caida.
Avisos: cambio de estado (cae / se recupera) -> alerta en RAM (200) + SQLite de memoria (scope chat-ui:watchdog); la campana del chat
los lee con la accion 'alertas' {desde}. Un fallo repetido no se repite en la campana mas de una vez cada 10 min.
Reinicio del Space: solo si RIU_WATCHDOG_RESTART_SPACE=1 y /health falla 3 rondas seguidas (POST HF /restart con HF_TOKEN).
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.request
from typing import Any, Callable

SCOPE = "chat-ui:watchdog"
REPETIR_S = 600
MAX_ALERTAS = 200
CLAVE = ("puente_chat", "fichas_qwen", "deepseek_harness", "hf_storage", "secretos")
AGENTE_RE = re.compile(r"agent|orquest")

_lock = threading.RLock()
_alertas: list[dict] = []
_estado: dict[str, dict] = {}  # chequeo -> {ok, desde, ultimo_aviso, fallos, detalle}
_ronda: dict[str, Any] = {"n": 0, "ultima": None, "ms": None, "resultado": None}
_hilo: dict[str, Any] = {"t": None, "stop": None, "cada_s": None}
_deps: dict[str, Any] = {}  # tests: set_deps(host=..., health=..., storage=..., mem=..., restart=...)


def set_deps(**kw: Any) -> None:
    _deps.clear()
    _deps.update(kw)
    with _lock:
        _alertas.clear()
        _estado.clear()
        _ronda.update(n=0, ultima=None, ms=None, resultado=None)


# ---- dependencias reales (inyectables) -----------------------------------------------------------------------------
def _host() -> Any:
    if "host" in _deps:
        return _deps["host"]
    from integration.plugin_host.host import get_host
    return get_host()


def _health_http() -> tuple[bool, str]:
    if "health" in _deps:
        return _deps["health"]()
    url = os.getenv("RIU_WATCHDOG_HEALTH_URL") or "http://127.0.0.1:%s/health" % (os.getenv("PORT") or "7860")
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return (200 <= r.status < 300), "HTTP %d" % r.status
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


def _storage() -> dict:
    """{'status': STATUS, 'reiniciar': fn, 'sync': fn, 'cada_s': n}."""
    if "storage" in _deps:
        return _deps["storage"]()
    from integration.chat_mvp import storage_lifecycle as sl
    from integration.chat_mvp.router import get_store, sync_to_bucket
    bucket, token = os.getenv("HF_BUCKET_ID"), os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN")

    def reiniciar() -> Any:
        sl._thread = None if (sl._thread is not None and not sl._thread.is_alive()) else sl._thread
        return sl.start_autosync(get_store, sync_to_bucket, bucket, token)

    def sync() -> Any:
        r = sync_to_bucket(get_store(), bucket, token)
        sl.STATUS["last_sync"], sl.STATUS["last_error"] = time.time(), None
        return r

    vivo = sl._thread is not None and sl._thread.is_alive()
    return {"status": dict(sl.STATUS), "vivo": vivo, "configurado": bool(bucket and token), "reiniciar": reiniciar, "sync": sync,
            "cada_s": float(os.getenv("RIU_AUTOSYNC_SECONDS", "60") or 60)}


def _mem_save(key: str, data: dict) -> None:
    try:
        if "mem" in _deps:
            _deps["mem"](key, data)
            return
        from integration.chat_mvp.memoria_loader import _memory
        _memory().sqlite.save(SCOPE, key, data)
    except Exception:  # noqa: BLE001 - un aviso que no se guarda no tumba al watchdog
        pass


def _restart_space() -> str:
    if "restart" in _deps:
        return _deps["restart"]()
    space, token = os.getenv("SPACE_ID") or "COMAND-CENTER-1/riu-router", os.getenv("HF_TOKEN") or ""
    req = urllib.request.Request("https://huggingface.co/api/spaces/%s/restart" % space, method="POST",
                                 headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=15) as r:
        return "HTTP %d" % r.status


# ---- avisos ------------------------------------------------------------------------------------------------------
def _avisar(nivel: str, chequeo: str, mensaje: str, accion: str | None = None) -> None:
    a = {"ts": time.time(), "nivel": nivel, "chequeo": chequeo, "mensaje": mensaje[:220]}
    if accion:
        a["accion"] = accion[:160]
    with _lock:
        _alertas.append(a)
        del _alertas[:-MAX_ALERTAS]
    _mem_save("alerta:%d" % int(a["ts"] * 1000), a)


def _marcar(chequeo: str, ok: bool, detalle: str, accion: str | None = None) -> dict:
    """Registra el resultado y avisa solo en cambios (cae / se recupera) o si sigue caido tras REPETIR_S."""
    ahora = time.time()
    with _lock:
        prev = _estado.get(chequeo)
        st = {"ok": ok, "detalle": detalle[:200], "accion": accion, "ts": ahora,
              "desde": prev["desde"] if prev and prev["ok"] == ok else ahora,
              "fallos": 0 if ok else (prev.get("fallos", 0) + 1 if prev else 1),
              "ultimo_aviso": prev.get("ultimo_aviso") if prev else None}
        if not ok and prev and prev.get("reiniciado"):
            st["reiniciado"] = True
        _estado[chequeo] = st
    if not ok and (prev is None or prev["ok"] or ahora - float(prev.get("ultimo_aviso") or 0) >= REPETIR_S):
        _avisar("error", chequeo, "Watchdog: %s caído (%s)" % (chequeo, detalle), accion)
        st["ultimo_aviso"] = ahora
    elif ok and prev is not None and not prev["ok"]:
        _avisar("ok", chequeo, "Watchdog: %s recuperado%s" % (chequeo, (" (" + accion + ")") if accion else ""), accion)
        st["ultimo_aviso"] = ahora
    elif ok and accion:  # reparado en esta misma ronda: se avisa que hubo reparacion
        _avisar("ok", chequeo, "Watchdog: %s reparado (%s)" % (chequeo, accion), accion)
    return st


# ---- chequeos ----------------------------------------------------------------------------------------------------
def _chk_health() -> dict:
    ok, det = _health_http()
    accion = None
    prev = _estado.get("health") or {}
    if not ok and prev.get("fallos", 0) + 1 >= 3 and os.getenv("RIU_WATCHDOG_RESTART_SPACE") == "1" and not prev.get("reiniciado"):
        try:
            accion = "reinicio del Space pedido: " + _restart_space()
        except Exception as exc:  # noqa: BLE001
            accion = "reinicio del Space fallo: " + type(exc).__name__
    st = _marcar("health", ok, det, accion)
    if accion:
        st["reiniciado"] = True
    return st


def _plugin_ok(host: Any, pid: str) -> tuple[bool, str]:
    rec = host.get(pid)
    if rec is None:
        return False, "no registrado"
    if rec.get("status") == "off":
        return True, "apagado a mano"
    if rec.get("status") == "invalid":
        return False, "ficha invalida"
    h = host.health(pid)
    if h is not None and h.get("status") != "ok":
        return False, str(h.get("reason") or h.get("status"))[:120]
    return True, "ok"


def _chk_fichas() -> list[dict]:
    host = _host()
    ids = [r["id"] for r in host.list_plugins()]
    vigilar = [i for i in ids if i in CLAVE] + [i for i in ids if i not in CLAVE and host.get(i).get("status") in ("invalid", "degraded") and not str((host.get(i) or {}).get("last_error") or "").startswith("placeholder")]
    fallos = {pid: det for pid in vigilar for ok, det in [_plugin_ok(host, pid)] if not ok}
    accion, antes = None, set(fallos)
    if fallos:  # reparacion: releer plugins/ (fichas y switches) sin reiniciar y volver a probar
        try:
            host.sync()
            accion = "fichas recargadas (host.sync)"
        except Exception as exc:  # noqa: BLE001
            accion = "host.sync fallo: " + type(exc).__name__
        fallos = {pid: det for pid in fallos for ok, det in [_plugin_ok(host, pid)] if not ok}
    out = []
    for pid in vigilar:
        out.append(_marcar("ficha:" + pid, pid not in fallos, fallos.get(pid, "ok"), accion if accion and pid in antes and pid not in fallos else None))
    if "puente_chat" in ids and "puente_chat" not in fallos:  # los modelos del chat: la lista de fichas no puede llegar vacia
        r = host.call("puente_chat", "modelos")
        n = len(((r.get("result") or {}).get("modelos") or [])) if r.get("status") == "ok" else 0
        out.append(_marcar("fichas:modelos", n > 0, "%d modelos" % n if n else str(r.get("reason") or "0 modelos")))
    return out


def _chk_memoria() -> dict:
    try:
        s = _storage()
    except Exception as exc:  # noqa: BLE001
        return _marcar("memoria:sync", False, "storage no cargo: " + type(exc).__name__)
    if not s.get("configurado"):
        return _marcar("memoria:sync", False, "bucket o token sin configurar")
    st, accion = s["status"], None
    edad = time.time() - float(st.get("last_sync") or 0) if st.get("last_sync") else None
    malo = (not s.get("vivo")) or bool(st.get("last_error")) or (edad is not None and edad > 3 * s["cada_s"])
    if not s.get("vivo"):
        try:
            s["reiniciar"]()
            accion = "autosync rearrancado"
        except Exception as exc:  # noqa: BLE001
            accion = "rearranque fallo: " + type(exc).__name__
    if malo:
        try:
            s["sync"]()
            accion = (accion + " + " if accion else "") + "sync manual ok"
            malo = False
        except Exception as exc:  # noqa: BLE001
            accion = (accion + " + " if accion else "") + "sync manual fallo: " + type(exc).__name__
    det = "ultimo sync hace %ds" % int(edad) if edad is not None else ("sync pendiente" if not malo else "sin sync")
    if st.get("last_error"):
        det += ", error " + str(st["last_error"])[:60]
    return _marcar("memoria:sync", not malo, det, accion)


def _chk_agentes() -> list[dict]:
    host = _host()
    out = []
    for rec in host.list_plugins():
        pid = rec["id"]
        if not AGENTE_RE.search(pid) or rec.get("status") == "off":
            continue
        ok, det = _plugin_ok(host, pid)
        accion = None
        if not ok:
            r = host.call(pid, "reiniciar")
            if r.get("status") == "ok":
                accion = "reiniciar pedido"
                ok, det = _plugin_ok(host, pid)
        out.append(_marcar("agente:" + pid, ok, det, accion))
    return out


def revisar() -> dict:
    t0 = time.perf_counter()
    res: dict[str, Any] = {}
    for nombre, fn in (("health", _chk_health), ("fichas", _chk_fichas), ("memoria", _chk_memoria), ("agentes", _chk_agentes)):
        try:
            res[nombre] = fn()
        except Exception as exc:  # noqa: BLE001 - un chequeo roto no detiene a los demas
            res[nombre] = _marcar("watchdog:" + nombre, False, "chequeo fallo: " + type(exc).__name__)
    with _lock:
        _ronda.update(n=_ronda["n"] + 1, ultima=time.time(), ms=int((time.perf_counter() - t0) * 1000))
        caidos = sorted(k for k, v in _estado.items() if not v["ok"])
        _ronda["resultado"] = {"caidos": caidos, "total": len(_estado)}
    return {"ok": not caidos, "caidos": caidos, "chequeos": {k: dict(v) for k, v in _estado.items()}, "ms": _ronda["ms"]}


# ---- hilo ---------------------------------------------------------------------------------------------------------
def arrancar(cada_s: float | None = None) -> dict:
    secs = float(os.getenv("RIU_WATCHDOG_S", "60") or 60) if cada_s is None else float(cada_s)
    with _lock:
        t = _hilo["t"]
        if t is not None and t.is_alive():
            return {"ok": True, "ya_corria": True, "cada_s": _hilo["cada_s"]}
        if secs <= 0:
            return {"ok": False, "apagado": True}
        secs = max(10.0, secs)
        stop = threading.Event()

        def loop() -> None:
            stop.wait(min(30.0, secs))  # deja arrancar al Router antes de la primera ronda
            while not stop.is_set():
                try:
                    revisar()
                except Exception:  # noqa: BLE001
                    pass
                stop.wait(secs)

        t = threading.Thread(target=loop, daemon=True, name="riu-watchdog")
        _hilo.update(t=t, stop=stop, cada_s=secs)
        t.start()
    return {"ok": True, "cada_s": secs}


def detener() -> dict:
    with _lock:
        if _hilo["stop"] is not None:
            _hilo["stop"].set()
        _hilo.update(t=None, stop=None)
    return {"ok": True}


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    try:
        if action == "status":
            with _lock:
                vivo = _hilo["t"] is not None and _hilo["t"].is_alive()
                return {"ok": True, "hilo": vivo, "cada_s": _hilo["cada_s"], "ronda": dict(_ronda),
                        "caidos": sorted(k for k, v in _estado.items() if not v["ok"]), "alertas": len(_alertas)}
        if action == "revisar":
            return revisar()
        if action == "alertas":
            try:
                desde = float(p.get("desde") or 0)
            except (TypeError, ValueError):
                desde = 0.0
            with _lock:
                lista = [dict(a) for a in _alertas if a["ts"] > desde]
            return {"ok": True, "alertas": lista[-50:], "ahora": time.time()}
        if action == "arrancar":
            return arrancar(p.get("cada_s"))
        if action == "detener":
            return detener()
        return {"error": "ACCION_DESCONOCIDA"}
    except Exception as exc:  # noqa: BLE001
        return {"error": "WATCHDOG_FALLO", "detalle": type(exc).__name__}
