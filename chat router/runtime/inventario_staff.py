"""S1 — Inventario verificado de componentes y staff.

Recorre las rutas donde el motor de descarga dejó los componentes y emite un manifiesto
con conteo de archivos, tamaño y hash del árbol (sha256 de la lista ordenada ruta+tamaño).
Un componente con 0 archivos se marca GAP: DESCARGADO != INTEGRADO.

Uso:  python3 "chat router/runtime/inventario_staff.py"  [--out chat router/EVIDENCIA/S1-INVENTARIO.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMPONENTES = REPO / "router inteligente universal" / "Componente open soure router inteligente universal"
DONORS = REPO / "router inteligente universal" / "agents-yaiwes" / "donors"

# nombre lógico del plan -> rutas candidatas (la primera que exista con archivos gana)
STAFF: dict[str, list[Path]] = {
    "rowboat": [COMPONENTES / "rowboat", REPO / "router inteligente universal" / "rowboat"],
    "ruflo": [COMPONENTES / "ruflo"],
    "hermes": [REPO / "hermes-agent"],
    "microsoft_agent_framework": [COMPONENTES / "microsoft-agent-framework"],
    "memanto": [COMPONENTES / "memanto"],
    "graphiti": [COMPONENTES / "graphiti"],
    "graphify": [COMPONENTES / "graphify"],
    "muse_code": [DONORS / "muse-code-sdk"],
    "metacua": [DONORS / "meta-model-cookbook-13-macos-cua"],
    "cua_mcp": [DONORS / "meta-model-cookbook-12-computer-use"],
    "meta_agentic_fundamentals": [DONORS / "meta-oss-cookbook-agentic-fundamentals"],
    "smolagents": [DONORS / "smolagents"],
    "pocketflow": [DONORS / "pocketflow"],
    "open_webui": [COMPONENTES / "open-webui"],
    "omniroute": [COMPONENTES / "OmniRoute"],
    "litellm": [COMPONENTES / "litellm", COMPONENTES / "LiteLLM"],
    "mcp_python_sdk": [COMPONENTES / "MCP-Python-SDK"],
    "muse_glimmer": [DONORS / "muse-glimmer"],
    "claude_code": [COMPONENTES / "claude-code"],
    "grokbot": [COMPONENTES / "grokbot"],
    "grok_build_gui": [COMPONENTES / "grok-build-gui"],
    "codex": [COMPONENTES / "codex"],
    "mimo_code": [COMPONENTES / "mimo-code"],
}


def medir(raiz: Path) -> tuple[int, int, str]:
    """(archivos, bytes, hash del árbol) de un directorio."""
    h = hashlib.sha256()
    archivos = 0
    total = 0
    for p in sorted(raiz.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        archivos += 1
        total += size
        h.update(f"{p.relative_to(raiz)}:{size}\n".encode())
    return archivos, total, "sha256:" + h.hexdigest()


def inventariar() -> dict:
    items = []
    for nombre, candidatos in STAFF.items():
        elegido = None
        for c in candidatos:
            if c.is_dir():
                archivos, total, digest = medir(c)
                if archivos:
                    elegido = {"ruta": str(c.relative_to(REPO)), "archivos": archivos, "bytes": total, "hash": digest}
                    break
                elegido = elegido or {"ruta": str(c.relative_to(REPO)), "archivos": 0, "bytes": 0, "hash": digest}
        if elegido is None:
            items.append({"componente": nombre, "estado": "GAP", "motivo": "ruta inexistente",
                          "rutas_buscadas": [str(c.relative_to(REPO)) for c in candidatos]})
        elif elegido["archivos"] == 0:
            items.append({"componente": nombre, "estado": "GAP", "motivo": "carpeta vacía", **elegido})
        else:
            items.append({"componente": nombre, "estado": "DESCARGADO", **elegido})
    ok = [i for i in items if i["estado"] == "DESCARGADO"]
    return {
        "schema": "yaiwes.inventario/v1",
        "nodo": "S1_descargas_staff",
        "generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "resumen": {"total": len(items), "descargados": len(ok), "gaps": len(items) - len(ok)},
        "componentes": sorted(items, key=lambda i: (i["estado"], i["componente"])),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "chat router" / "EVIDENCIA" / "S1-INVENTARIO.json"))
    args = ap.parse_args()
    data = inventariar()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(data["resumen"], ensure_ascii=False))
    for i in data["componentes"]:
        if i["estado"] == "GAP":
            print("GAP:", i["componente"], "-", i["motivo"])


if __name__ == "__main__":
    main()
