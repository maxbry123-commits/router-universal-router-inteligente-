#!/usr/bin/env python3
"""OpenClaw usa la MISMA memoria del chat Yaiwes (bucket HF, memoria/<scope>.json): reutiliza mvp.memoria, sin sistema nuevo.
Uso: memoria_hf.py save <scope> <key>  (JSON por stdin)  |  load <scope> <key>  |  search <scope> [query] [k]. El token sale de HF_TOKEN del entorno."""
import asyncio, json
import os, sys
from pathlib import Path


def _preparar_rutas():
    """El script se basta solo (no depende de PYTHONPATH): ubica `mvp` en router-mvp y en chat-router/chat/backend subiendo desde __file__ (o desde RIU_REPO_ROOT)."""
    aqui = Path(__file__).resolve()
    raices = [Path(os.environ["RIU_REPO_ROOT"])] if os.environ.get("RIU_REPO_ROOT") else [p for p in aqui.parents[:5]]
    for raiz in raices:
        for rel in (("router-mvp",), ("chat-router", "chat", "backend")):
            ruta = raiz.joinpath(*rel)
            if ruta.is_dir() and str(ruta) not in sys.path:
                sys.path.append(str(ruta))


_preparar_rutas()
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
    elif accion == "search":  # search <scope> [query] [k]: devuelve los registros del scope (historial)
        cuerpo = {"scope": scope, "query": argv[2] if len(argv) > 2 else "", "k": argv[3] if len(argv) > 3 else 200}
    elif accion != "load":
        raise ValueError("accion no soportada")
    return asyncio.run(memoria.aplicar(accion, cuerpo, lambda: token))


if __name__ == "__main__":
    try:
        print(json.dumps(main(sys.argv[1:], sys.stdin.read() if sys.argv[1:2] == ["save"] else ""), ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 - salida corta para el bridge
        print(json.dumps({"ok": False, "error": type(exc).__name__ + ": " + str(getattr(exc, "detail", exc))[:120]})); sys.exit(1)
