"""Plugin secretos (Director 2026-10-16): claves y tokens del chat, cifrados en el servidor y usados por nombre.

Ruta: COMPONENTE (ventana Claves del chat) -> HARNESS (PluginHost.call, POST /plugins/secretos/call/<accion>) -> este plugin.
Cifrado: el MISMO formato del banco unico (FICHA-SELLO-1 = cabecera + sal 16 + nonce 12 + AES-GCM, llave scrypt n=2^15 de
FICHA_CLAVE_BANCO). Sin esa clave en el entorno no se guarda ni se lee nada (fail-closed).
Persistencia: SQLite de memoria_yaiwes (adaptador sqlite directo: NUNCA a grafo, Qdrant ni Graphiti) -> autosync al bucket con la base,
y ademas un espejo cifrado en el bucket (riu-chat/secretos/secretos.json) que se restaura solo si el SQLite llega vacio.
Salida: ninguna accion HTTP devuelve el valor en claro; solo nombre, proveedor y mascara. Excepcion unica: mcp_token_nuevo devuelve el
token que acaba de generar UNA vez, para pegarlo en el cliente MCP.
API para otros plugins (no expuesta por HTTP): obtener(nombre), por_proveedor(proveedor), verificar_token_mcp(token).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets as _secrets
import threading
import time
from typing import Any, Callable

SCOPE = "chat-ui:secretos"
CAB = b"FICHA-SELLO-1"
MIRROR = "secretos/secretos.json"
MCP_NOMBRE = "mcp/token"
NOMBRE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-/]{0,63}$")
PROV_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
MAX_VALOR = 8192
MAX_SECRETOS = 500

_lock = threading.RLock()
_llaves: dict[bytes, bytes] = {}  # sal -> llave derivada (scrypt es lento: una vez por proceso)
_cache: dict[str, Any] = {"filas": None}  # nombre -> registro vigente (cifrado)
_restaurado = {"hecho": False, "estado": "NO_RUN"}
_espejo_estado: dict[str, Any] = {"ultimo": None, "error": None}
_espejo_lock = threading.Lock()
_backend: dict[str, Any] = {"mem": None, "bucket": None}  # tests: set_backend()


# ---- backends -------------------------------------------------------------------------------------------------------
def set_backend(mem: Any = None, bucket: Callable[[str, dict], dict] | None = None) -> None:
    """Tests: mem = objeto con save/search (adaptador SQLite); bucket = fn(accion, payload) como hf_storage.handle. Limpia la cache."""
    _backend["mem"], _backend["bucket"] = mem, bucket
    with _lock:
        _cache["filas"] = None
        _restaurado.clear()
        _restaurado.update(hecho=False, estado="NO_RUN")


def _mem() -> Any:
    if _backend["mem"] is not None:
        return _backend["mem"]
    from integration.chat_mvp.memoria_loader import _memory
    return _memory().sqlite  # solo SQLite: un secreto (aunque cifrado) no va a replicas semanticas


def _bucket(accion: str, payload: dict) -> dict:
    if _backend["bucket"] is not None:
        return _backend["bucket"](accion, payload)
    from plugins.hf_storage.plugin import handle as hf
    return hf(accion, payload)


# ---- cifrado (formato del banco unico) ------------------------------------------------------------------------------
def _clave_banco() -> str:
    return os.environ.get("FICHA_CLAVE_BANCO") or os.environ.get("RIU_VAULT_PASSPHRASE") or ""


def _llave(sal: bytes) -> bytes:
    clave = _clave_banco()
    if not clave:
        raise RuntimeError("SIN_CLAVE_DEL_BANCO_EN_EL_ROUTER")
    k = hashlib.sha256(clave.encode() + sal).digest()  # indice de cache sin guardar la clave
    with _lock:
        if k not in _llaves:
            _llaves[k] = hashlib.scrypt(clave.encode(), salt=sal, n=2 ** 15, r=8, p=1, dklen=32, maxmem=2 ** 26)
        return _llaves[k]


def _sal() -> bytes:
    """Una sal por almacen (guardada en el registro meta y en el espejo) para derivar la llave una sola vez."""
    for f in _buscar("meta"):
        d = f.get("data") if isinstance(f, dict) else None
        if isinstance(d, dict) and d.get("sal"):
            return base64.b64decode(d["sal"])
    sal = os.urandom(16)
    _mem().save(SCOPE, "meta", {"sal": base64.b64encode(sal).decode(), "ts": time.time()})
    return sal


def sellar(valor: str, sal: bytes) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(12)
    return base64.b64encode(CAB + sal + nonce + AESGCM(_llave(sal)).encrypt(nonce, valor.encode("utf-8"), CAB)).decode()


def abrir(sello_b64: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    b = base64.b64decode(sello_b64)
    k = len(CAB)
    if b[:k] != CAB:
        raise ValueError("SELLO_INVALIDO")
    sal, nonce, ct = b[k:k + 16], b[k + 16:k + 28], b[k + 28:]
    return AESGCM(_llave(sal)).decrypt(nonce, ct, CAB).decode("utf-8")


def mascara(valor: str) -> str:
    n = len(valor)
    if n >= 16:
        return valor[:3] + "…" + valor[-4:]
    if n >= 8:
        return "••••" + valor[-2:]
    return "••••"


# ---- almacen --------------------------------------------------------------------------------------------------------
def _buscar(q: str, k: int = 2000) -> list[dict]:
    res = _mem().search(SCOPE, q, k)
    return res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])


def _vigentes() -> dict[str, dict]:
    """nombre -> registro mas reciente (incluye borrados marcados). Cache en RAM; se invalida al escribir."""
    with _lock:
        if _cache["filas"] is not None:
            return _cache["filas"]
        arrancar = not _restaurado["hecho"] and not _restaurado.get("en_curso")
        if arrancar:
            _restaurado["en_curso"] = True
    if arrancar:  # el espejo del bucket es lento: nunca en el camino del chat; se restaura en segundo plano
        threading.Thread(target=_restaurar_bg, daemon=True, name="secretos-restaurar").start()
    out = _vigentes_sqlite()
    with _lock:
        _cache["filas"] = out
    return out


def _vigentes_sqlite() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in _buscar("secreto:"):  # SQLite devuelve lo mas nuevo primero
        d = f.get("data") if isinstance(f, dict) else None
        key = str(f.get("key") or "") if isinstance(f, dict) else ""
        if isinstance(d, dict) and key.startswith("secreto:") and d.get("nombre"):
            prev = out.get(d["nombre"])
            if prev is None or float(d.get("ts") or 0) > float(prev.get("ts") or 0):
                out[d["nombre"]] = d
    return out


def _escribir(reg: dict) -> None:
    _mem().save(SCOPE, "secreto:" + reg["nombre"], reg)
    with _lock:
        _cache["filas"] = None


def _espejo_doc() -> dict:
    sal = None
    for f in _buscar("meta"):
        d = f.get("data") if isinstance(f, dict) else None
        if isinstance(d, dict) and d.get("sal"):
            sal = d["sal"]
            break
    return {"schema": "riu.secretos/v1", "sal": sal, "ts": time.time(), "secretos": _vigentes()}


def espejo_bucket(sincrono: bool = False) -> dict:
    """Copia cifrada al bucket (riu-chat/secretos/secretos.json). En segundo plano salvo sincrono=True."""
    def run() -> dict:
        try:
            with _espejo_lock:
                try:  # union con lo que ya hay en el bucket: escribir el espejo nunca borra un secreto de otra copia
                    doc = _leer_espejo()
                    if doc:
                        _fusionar(doc)
                except Exception:  # noqa: BLE001
                    pass
                r = _bucket("write", {"path": MIRROR, "content": json.dumps(_espejo_doc(), ensure_ascii=False)})
            ok = isinstance(r, dict) and r.get("status") == "ok"
            _espejo_estado.update(ultimo=time.time() if ok else _espejo_estado["ultimo"], error=None if ok else str((r or {}).get("error"))[:200])
            return {"ok": ok}
        except Exception as exc:  # noqa: BLE001
            _espejo_estado["error"] = type(exc).__name__
            return {"ok": False, "error": type(exc).__name__}
    if sincrono:
        return run()
    threading.Thread(target=run, daemon=True, name="secretos-espejo").start()
    return {"ok": None, "en_curso": True}


def _restaurar_bg() -> None:
    try:
        _restaurar_si_vacio()
    finally:
        _restaurado["en_curso"] = False


def _leer_espejo() -> dict | None:
    r = _bucket("read", {"path": MIRROR})
    if not (isinstance(r, dict) and r.get("status") == "ok"):
        return None
    doc = json.loads(r.get("content") or "{}")
    return doc if isinstance(doc, dict) else None


def _fusionar(doc: dict) -> int:
    """Importa del espejo lo que falta en SQLite o es mas nuevo alli (gana el ts mayor). Nunca borra nada local."""
    if doc.get("sal") and not _buscar("meta", 1):
        _mem().save(SCOPE, "meta", {"sal": doc["sal"], "ts": time.time(), "origen": "espejo"})
    with _lock:
        _cache["filas"] = None
    loc = _vigentes_sqlite()
    n = 0
    for nombre, reg in (doc.get("secretos") or {}).items():
        if not (isinstance(reg, dict) and NOMBRE_RE.match(str(nombre)) and reg.get("nombre") == nombre):
            continue
        if nombre not in loc or float(reg.get("ts") or 0) > float(loc[nombre].get("ts") or 0):
            _mem().save(SCOPE, "secreto:" + nombre, reg)
            n += 1
    with _lock:
        _cache["filas"] = None
    return n


def _restaurar_si_vacio(forzar: bool = False) -> dict:
    """Al primer uso (o con forzar): fusiona el espejo cifrado del bucket en SQLite (reinicio sin snapshot = nada se pierde)."""
    with _lock:
        if _restaurado["hecho"] and not forzar:
            return dict(_restaurado)
        _restaurado["hecho"] = True
    try:
        doc = _leer_espejo()
        if doc is None:
            _restaurado["estado"] = "SIN_ESPEJO"
            return dict(_restaurado)
        _restaurado.update(estado="RESTAURADO", importados=_fusionar(doc))
    except Exception as exc:  # noqa: BLE001
        _restaurado["estado"] = "ERROR:" + type(exc).__name__
    return dict(_restaurado)


def _publico(reg: dict) -> dict:
    return {k: reg.get(k) for k in ("nombre", "proveedor", "mascara", "nota", "creado", "actualizado", "largo")}


# ---- API para otros plugins (no HTTP) ---------------------------------------------------------------------------
def obtener(nombre: str) -> str | None:
    """Valor en claro de un secreto por nombre (solo dentro del proceso del Router). None si no existe, esta borrado o no abre."""
    reg = _vigentes().get(str(nombre or ""))
    if not reg or reg.get("borrado") or not reg.get("sello"):
        return None
    try:
        return abrir(reg["sello"])
    except Exception:  # noqa: BLE001
        return None


def por_proveedor(proveedor: str) -> list[str]:
    """Valores de los secretos marcados con ese proveedor (groq, nvidia, hf, ...), mas antiguos primero; los usa vault_hook."""
    try:
        regs = [r for r in _vigentes().values() if r.get("proveedor") == proveedor and not r.get("borrado") and r.get("sello")]
    except Exception:  # noqa: BLE001 - sin memoria o sin clave: nada, nunca rompe el pool
        return []
    out = []
    for r in sorted(regs, key=lambda x: float(x.get("creado") or 0)):
        try:
            out.append(abrir(r["sello"]))
        except Exception:  # noqa: BLE001
            continue
    return out


def verificar_token_mcp(token: str | None) -> bool:
    """True si el token coincide (tiempo constante) con RIU_MCP_TOKEN o con el secreto mcp/token."""
    if not token:
        return False
    validos = [os.environ.get("RIU_MCP_TOKEN") or ""]
    try:
        validos.append(obtener(MCP_NOMBRE) or "")
    except Exception:  # noqa: BLE001
        pass
    return any(v and hmac.compare_digest(v.encode(), str(token).encode()) for v in validos)


# ---- acciones HTTP ----------------------------------------------------------------------------------------------
def _guardar(p: dict) -> dict:
    nombre = str(p.get("nombre") or "").strip()
    valor = p.get("valor")
    if not NOMBRE_RE.match(nombre):
        return {"error": "NOMBRE_INVALIDO", "regla": "letras, numeros, . _ - / (max 64)"}
    if not isinstance(valor, str) or not valor or len(valor) > MAX_VALOR:
        return {"error": "VALOR_INVALIDO"}
    prov = str(p.get("proveedor") or "").strip().lower()
    if prov and not PROV_RE.match(prov):
        return {"error": "PROVEEDOR_INVALIDO"}
    if not _clave_banco():
        return {"error": "SIN_CLAVE_DEL_BANCO_EN_EL_ROUTER"}
    vig = _vigentes()
    if nombre not in vig and sum(1 for r in vig.values() if not r.get("borrado")) >= MAX_SECRETOS:
        return {"error": "DEMASIADOS_SECRETOS", "max": MAX_SECRETOS}
    ahora = time.time()
    prev = vig.get(nombre) or {}
    reg = {"nombre": nombre, "proveedor": prov or None, "sello": sellar(valor, _sal()), "mascara": mascara(valor), "largo": len(valor),
           "nota": str(p.get("nota") or "")[:200], "creado": prev.get("creado") if not prev.get("borrado") and prev.get("creado") else ahora,
           "actualizado": ahora, "ts": ahora, "borrado": False}
    _escribir(reg)
    espejo_bucket()
    return {"ok": True, "secreto": _publico(reg), "rotado": bool(prev and not prev.get("borrado"))}


def _borrar(p: dict) -> dict:
    nombre = str(p.get("nombre") or "").strip()
    reg = _vigentes().get(nombre)
    if not reg or reg.get("borrado"):
        return {"error": "NO_EXISTE"}
    ahora = time.time()
    _escribir({"nombre": nombre, "borrado": True, "ts": ahora, "actualizado": ahora})  # marca: el sello viejo no se copia
    espejo_bucket()
    return {"ok": True, "nombre": nombre}


def _pin_ok(p: dict) -> bool:
    """RIU_SECRETOS_PIN (opcional): si esta puesto, escribir/borrar/generar token MCP exige payload.pin igual. Sin PIN = 0 friccion."""
    pin = os.environ.get("RIU_SECRETOS_PIN") or ""
    return not pin or hmac.compare_digest(pin.encode(), str(p.get("pin") or "").encode())


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    try:
        if action == "status":
            vig = _vigentes()
            return {"ok": True, "clave_banco": bool(_clave_banco()), "secretos": sum(1 for r in vig.values() if not r.get("borrado")),
                    "restauracion": dict(_restaurado), "espejo": dict(_espejo_estado), "mcp_token": bool(obtener(MCP_NOMBRE) or os.environ.get("RIU_MCP_TOKEN"))}
        if action == "listar":
            vig = _vigentes()
            return {"ok": True, "secretos": sorted((_publico(r) for r in vig.values() if not r.get("borrado")), key=lambda x: x["nombre"])}
        if action in ("guardar", "borrar", "restaurar", "mcp_token_nuevo") and not _pin_ok(p):
            return {"error": "PIN_REQUERIDO"}
        if action == "guardar":
            return _guardar(p)
        if action == "borrar":
            return _borrar(p)
        if action == "restaurar":
            r = _restaurar_si_vacio(forzar=True)
            return {"ok": r.get("estado") == "RESTAURADO", **r}
        if action == "mcp_token_nuevo":
            token = "riu-mcp-" + _secrets.token_urlsafe(32)
            r = _guardar({"nombre": MCP_NOMBRE, "valor": token, "nota": "token del MCP HTTP (/mcp)"})
            if not r.get("ok"):
                return r
            return {"ok": True, "token": token, "una_vez": True, "aviso": "Copialo ahora: no se vuelve a mostrar."}
        return {"error": "ACCION_DESCONOCIDA"}
    except Exception as exc:  # noqa: BLE001 - nunca devuelve detalles con valores
        return {"error": "SECRETOS_FALLO", "detalle": type(exc).__name__}
