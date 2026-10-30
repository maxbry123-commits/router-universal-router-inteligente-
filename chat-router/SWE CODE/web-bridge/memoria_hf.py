#!/usr/bin/env python3
"""OpenClaw usa la MISMA memoria del chat Yaiwes (bucket HF, memoria/<scope>.json): reutiliza mvp.memoria, sin sistema nuevo.
Uso: memoria_hf.py save <scope> <key>  (JSON por stdin)  |  memoria_hf.py load <scope> <key>. El token sale de HF_TOKEN del entorno."""
import asyncio, json, os, sys
from mvp import memoria


def main(argv, stdin_texto=""):
    accion, scope = argv[0], argv[1]
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN ausente en el entorno")
    key = argv[2] if len(argv) > 2 else ""
    cuerpo = {"scope": scope, "key": key}
    if accion == "save":
        cuerpo["data"] = json.loads(stdin_texto or "{}")
    elif accion != "load":
        raise ValueError("accion no soportada")
    return asyncio.run(memoria.aplicar(accion, cuerpo, lambda: token))


if __name__ == "__main__":
    try:
        print(json.dumps(main(sys.argv[1:], sys.stdin.read() if sys.argv[1:2] == ["save"] else ""), ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 - salida corta para el bridge
        print(json.dumps({"ok": False, "error": type(exc).__name__ + ": " + str(getattr(exc, "detail", exc))[:120]})); sys.exit(1)
