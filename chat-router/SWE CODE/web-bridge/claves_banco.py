#!/usr/bin/env python3
"""Puente al banco de claves de Groq/NVIDIA, sin variables de Hugging Face y sin tocar el Router MVP.
- LEE (solo lectura) el banco del Router (chat/backend/mvp/data/banco.bin, o RIU_BANCO_ROUTER) con la clave de acceso RIU_API_KEY.
- GUARDA las claves que le pegan al bridge en un banco PROPIO cifrado igual (BRIDGE_STATE_DIR/banco-swe.bin; esa carpeta ya se respalda en /data).
Reutiliza mvp.bank (misma cifra Fernet). Uso: claves_banco.py leer  |  claves_banco.py guardar  (JSON por stdin {groq, nvidia})."""
import json, os, re, sys
from pathlib import Path
from mvp import bank

PATRON = re.compile(r"(GROQ|NVIDIA)_API_KEY(_\d{1,2})?")
MAX = 20


def _acceso():
    return next((os.environ[v] for v in bank.ACCESO if os.environ.get(v)), "")


def _ruta_router():
    return os.environ.get("RIU_BANCO_ROUTER") or str(Path(__file__).resolve().parents[2] / "chat" / "backend" / "mvp" / "data" / "banco.bin")


def _ruta_propia():
    return os.path.join(os.environ.get("BRIDGE_STATE_DIR") or "./state", "banco-swe.bin")


def _abrir(ruta, crear=False):
    clave = _acceso()
    if not clave or not (crear or os.path.exists(ruta)):
        return None
    try:
        return bank.abrir(ruta, clave)
    except (ValueError, OSError):
        return None  # banco ilegible o clave distinta: no se rompe, simplemente no aporta


def leer():
    out = {"groq": [], "nvidia": []}
    for ruta in (_ruta_router(), _ruta_propia()):
        b = _abrir(ruta)
        if not b:
            continue
        for nombre in b.nombres():
            m = PATRON.fullmatch(nombre)
            if m:
                lista = out[m.group(1).lower()]
                v = b.leer(nombre)
                if v and v not in lista and len(lista) < MAX:
                    lista.append(v)
    return out


def guardar(claves):
    b = _abrir(_ruta_propia(), crear=True)
    if not b:
        raise RuntimeError("sin clave de acceso (RIU_API_KEY): no se puede cifrar el banco propio")
    for prov, var in (("groq", "GROQ_API_KEY"), ("nvidia", "NVIDIA_API_KEY")):
        v = (claves or {}).get(prov)
        lista = [x.strip() for x in ([v] if isinstance(v, str) else v or []) if isinstance(x, str) and x.strip()][:MAX]
        for i, k in enumerate(lista):
            b.guardar(var if i == 0 else "%s_%d" % (var, i), k)
    return True


if __name__ == "__main__":
    try:
        if sys.argv[1:2] == ["leer"]:
            print(json.dumps(leer()))
        elif sys.argv[1:2] == ["guardar"]:
            guardar(json.loads(sys.stdin.read() or "{}")); print(json.dumps({"ok": True}))
        else:
            sys.exit("uso: claves_banco.py leer | guardar")
    except Exception as exc:  # noqa: BLE001 - salida corta, sin valores
        print(json.dumps({"ok": False, "error": type(exc).__name__})); sys.exit(1)
