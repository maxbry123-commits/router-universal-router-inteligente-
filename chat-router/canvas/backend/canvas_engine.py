"""Orquestador del Canvas (N4-A).

Fichero: canvas_engine.py
Responsabilidad: cargar los 6 adapters de forma aislada (importlib), exponer
`health_all()`, `render_diagram()`, `render_motion()` y `cross_convert()`.

FAIL_CLOSED:
  - Un adapter caido NUNCA rompe el engine: se aísla en try/except.
  - `health_all()` nunca lanza; un adapter que revienta -> {"tool","status":"ERROR"}.
  - `render_*` nunca lanza por un adapter caido: devuelve {"ok":false,"error":...}.
  - Solo se lanzan ValueError para herramientas desconocidas (el API las mapea a 400).

Componentes autorizados (y solo estos): Excalidraw, Mermaid, D2, HyperFrames,
Remotion, Rive.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parent
ADAPTERS_DIR = BACKEND_DIR / "adapters"

#: Mapa tool -> fichero adaptador (carga aislada con importlib).
ADAPTER_FILES: Dict[str, str] = {
    "excalidraw": "excalidraw.py",
    "mermaid": "mermaid.py",
    "d2": "d2.py",
    "hyperframes": "hyperframes.py",
    "remotion": "remotion.py",
    "rive": "rive.py",
}

#: Cache de modulos ya cargados: tool -> ModuleType.
ADAPTERS: Dict[str, ModuleType] = {}

DIAGRAM_TOOLS: List[str] = ["excalidraw", "mermaid", "d2"]
MOTION_TOOLS: List[str] = ["hyperframes", "remotion", "rive"]
ALL_TOOLS: List[str] = DIAGRAM_TOOLS + MOTION_TOOLS


def load_adapter(tool: str) -> Optional[ModuleType]:
    """Carga (y cachea) un adapter por ruta. Devuelve None si no se puede cargar."""
    if tool in ADAPTERS:
        return ADAPTERS[tool]
    filename = ADAPTER_FILES.get(tool)
    if not filename:
        return None
    path = ADAPTERS_DIR / filename
    try:
        if not path.exists():
            return None
        module_name = f"canvas_adapters_{tool}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        ADAPTERS[tool] = module
        return module
    except Exception:
        return None


def health_all() -> List[Dict[str, Any]]:
    """Estado real de los 6 adapters. NUNCA lanza."""
    results: List[Dict[str, Any]] = []
    for tool in ALL_TOOLS:
        entry: Dict[str, Any] = {"tool": tool}
        try:
            module = load_adapter(tool)
            if module is None:
                entry.update(
                    {
                        "status": "ERROR",
                        "reason": f"adapter '{tool}' no se pudo cargar desde {ADAPTERS_DIR / ADAPTER_FILES.get(tool, '')}",
                        "version": None,
                        "checked_at": time.time(),
                    }
                )
                results.append(entry)
                continue
            ping = getattr(module, "ping", None)
            if not callable(ping):
                entry.update(
                    {
                        "status": "ERROR",
                        "reason": f"adapter '{tool}' no expone ping()",
                        "version": None,
                        "checked_at": time.time(),
                    }
                )
                results.append(entry)
                continue
            status = ping()
            if not isinstance(status, dict):
                entry.update(
                    {
                        "status": "ERROR",
                        "reason": f"adapter '{tool}' devolvio un ping no-dict: {type(status).__name__}",
                        "version": None,
                        "checked_at": time.time(),
                    }
                )
                results.append(entry)
                continue
            entry.update(status)
            entry.setdefault("tool", tool)
            entry.setdefault("status", "ERROR")
            entry["checked_at"] = time.time()
            results.append(entry)
        except Exception as exc:
            entry.update(
                {
                    "status": "ERROR",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "version": None,
                    "checked_at": time.time(),
                }
            )
            results.append(entry)
    return results


def _call_adapter(tool: str, func_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Llama a un metodo del adapter aislando cualquier excepcion."""
    module = load_adapter(tool)
    if module is None:
        return {
            "ok": False,
            "tool": tool,
            "error": f"adapter '{tool}' no disponible (no se pudo cargar)",
        }
    func = getattr(module, func_name, None)
    if not callable(func):
        return {
            "ok": False,
            "tool": tool,
            "error": f"adapter '{tool}' no expone {func_name}()",
        }
    try:
        result = func(*args, **kwargs)
    except Exception as exc:
        return {
            "ok": False,
            "tool": tool,
            "error": f"{type(exc).__name__}: {exc}",
        }
    if not isinstance(result, dict):
        return {
            "ok": False,
            "tool": tool,
            "error": f"adapter '{tool}.{func_name}()' devolvio {type(result).__name__} (se exige dict)",
        }
    result.setdefault("tool", tool)
    return result


def render_diagram(tool: str, payload: Any) -> Dict[str, Any]:
    """Renderiza un diagrama. `tool` ∈ {excalidraw, mermaid, d2}.

    ValueError si la herramienta no es de diagramas (el API la mapea a 400).
    """
    if tool not in DIAGRAM_TOOLS:
        raise ValueError(
            f"tool de diagrama desconocido: '{tool}' (validos: {', '.join(DIAGRAM_TOOLS)})"
        )
    return _call_adapter(tool, "render", payload)


def render_motion(tool: str, payload: Any) -> Dict[str, Any]:
    """Renderiza una animacion. `tool` ∈ {hyperframes, remotion, rive}.

    Mapeo de payload por herramienta:
      hyperframes -> html, duration, format
      remotion    -> composition, props, project_dir
      rive        -> riv_path, state_machine
    """
    if tool not in MOTION_TOOLS:
        raise ValueError(
            f"tool de motion desconocido: '{tool}' (validos: {', '.join(MOTION_TOOLS)})"
        )
    source = payload if isinstance(payload, dict) else {}
    if tool == "hyperframes":
        mapped = {
            "html": source.get("html"),
            "duration": source.get("duration", 5),
            "format": source.get("format", "mp4"),
        }
        if source.get("fps") is not None:
            mapped["fps"] = source["fps"]
    elif tool == "remotion":
        mapped = {
            "composition": source.get("composition") or source.get("composition_id"),
            "props": source.get("props") or {},
            "project_dir": source.get("project_dir"),
        }
        if source.get("out"):
            mapped["out"] = source["out"]
    else:  # rive
        mapped = {
            "riv_path": source.get("riv_path") or source.get("path"),
            "state_machine": source.get("state_machine"),
        }
        if source.get("out"):
            mapped["out"] = source["out"]
        if source.get("format"):
            mapped["format"] = source["format"]
    result = _call_adapter(tool, "render", mapped)
    result.setdefault("tool", tool)
    return result


def _elements_to_mermaid(elements: Any) -> str:
    """Convierte elementos Excalidraw en codigo mermaid flowchart (determinista)."""
    if not isinstance(elements, list):
        raise ValueError("payload.elements debe ser una lista de elementos Excalidraw")
    shapes: Dict[str, Dict[str, Any]] = {}
    labels: Dict[str, str] = {}
    for element in elements:
        if not isinstance(element, dict):
            continue
        etype = element.get("type")
        eid = element.get("id")
        if etype == "text" and element.get("containerId"):
            labels[element["containerId"]] = str(element.get("text") or "").strip()
        elif etype in ("rectangle", "ellipse", "diamond", "circle", "text") and eid:
            shapes[eid] = element

    def label_for(eid: str) -> str:
        element = shapes.get(eid) or {}
        own = str(element.get("text") or "").strip()
        return own or labels.get(eid) or eid

    lines: List[str] = ["flowchart TD"]
    for eid in shapes:
        label = label_for(eid).replace('"', "'")
        lines.append(f'  {eid}["{label}"]')
    for element in elements:
        if not isinstance(element, dict):
            continue
        if element.get("type") not in ("arrow", "line"):
            continue
        start = element.get("startBinding") or {}
        end = element.get("endBinding") or {}
        src = start.get("elementId")
        dst = end.get("elementId")
        if src and dst:
            lines.append(f"  {src} --> {dst}")
    return "\n".join(lines)


def cross_convert(src: str, dst: str, payload: Any) -> Dict[str, Any]:
    """Convierte entre herramientas de diagrama.

    Reglas (deterministas, sin inventar formato):
      - dst == "excalidraw": usa el codigo mermaid de `payload["code"]`
        (src mermaid/d2) y llama a `excalidraw.from_mermaid(code)`.
      - dst == "mermaid": si `payload["elements"]` -> conversion determinista
        elementos Excalidraw -> flowchart mermaid; si `payload["code"]` ->
        se devuelve el codigo tal cual (converted=False).
      - dst == "d2": `payload["code"]` se devuelve como fuente d2 (converted=False).
    """
    if src not in DIAGRAM_TOOLS:
        raise ValueError(
            f"herramienta origen desconocida: '{src}' (validas: {', '.join(DIAGRAM_TOOLS)})"
        )
    if dst not in DIAGRAM_TOOLS:
        raise ValueError(
            f"herramienta destino desconocida: '{dst}' (validas: {', '.join(DIAGRAM_TOOLS)})"
        )
    source = payload if isinstance(payload, dict) else {}

    if dst == "excalidraw":
        code = source.get("code") or source.get("mermaid") or source.get("source")
        if not isinstance(code, str) or not code.strip():
            return {
                "ok": False,
                "src": src,
                "dst": dst,
                "error": "falta 'code' (mermaid) en el payload para convertir a excalidraw",
            }
        result = _call_adapter("excalidraw", "from_mermaid", code)
        result["src"] = src
        result["dst"] = dst
        result["converted"] = True
        return result

    if dst == "mermaid":
        elements = source.get("elements")
        if elements is not None:
            try:
                code = _elements_to_mermaid(elements)
            except ValueError as exc:
                return {"ok": False, "src": src, "dst": dst, "error": str(exc)}
            return {
                "ok": True,
                "src": src,
                "dst": dst,
                "converted": True,
                "code": code,
                "mermaid": code,
                "error": None,
            }
        code = source.get("code") or source.get("mermaid") or source.get("source")
        if isinstance(code, str) and code.strip():
            return {
                "ok": True,
                "src": src,
                "dst": dst,
                "converted": False,
                "code": code,
                "mermaid": code,
                "error": None,
            }
        return {
            "ok": False,
            "src": src,
            "dst": dst,
            "error": "payload invalido: se esperaba 'elements' (excalidraw) o 'code' (mermaid)",
        }

    # dst == "d2"
    code = source.get("code") or source.get("d2") or source.get("source")
    if isinstance(code, str) and code.strip():
        return {
            "ok": True,
            "src": src,
            "dst": dst,
            "converted": False,
            "code": code,
            "d2": code,
            "error": None,
        }
    return {
        "ok": False,
        "src": src,
        "dst": dst,
        "error": "payload invalido: se esperaba 'code' (fuente d2)",
    }
