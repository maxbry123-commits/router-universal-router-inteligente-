"""Genera el inventario verificable de referencias UI del plan."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = Path(__file__).resolve().parent
IMAGES = PLAN / "REFERENCIAS-UI"
OUTPUT = PLAN / "CATALOGO-REFERENCIAS-UI.json"
EXTRA_OUTPUT = PLAN / "CATALOGO-ANEXOS-VISUALES.json"
SKILL = "chat router/Workflow Loop code Yaiwes/01-PLAN/SKILLS-MAXBRY-UI/diseno/😄SKILL.md"
PALETTE = "chat router/Workflow Loop code Yaiwes/01-PLAN/SKILLS-MAXBRY-UI/diseno/README-SKILL-PARTE-1-GRIS-PRINCIPAL.md"
SPEC = "chat router/Workflow Loop code Yaiwes/01-PLAN/SKILLS-MAXBRY-UI/diseno/ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md"

# Orden alfabético de las capturas conservado en el catálogo de la fuente.
ROLES = [
    "Colores de estado, iconos y panel de escritorio V09", "Variante de colores e iconos V09",
    "Paleta de grises y jerarquía de superficies", "Referencia de selección de proyecto Grok",
    "Referencia de controles móviles en Firefox", "Manus: acceso e inicio de sesión",
    "Manus: formulario de conexión", "Manus: opciones de conexión", "Manus: campos de conexión",
    "Manus: selector de conexión", "Manus: formulario y aviso", "Manus: opciones de tarea",
    "Manus: lista de opciones", "Manus: tareas recientes", "Manus: permisos de conector",
    "Manus: confirmación de conector", "Manus: estado vacío", "Manus: cuenta y ajustes",
    "Grok Bot: lista de agentes", "Grok Bot: configuración superior",
    "Grok Bot: configuración inferior", "Grok Bot: conversación y acciones",
    "Edge: acceso a chat", "Edge: entrada del chat", "Edge: conversación inicial",
    "Edge: configuración de contexto", "Edge: selección de recursos", "Edge: acción de conexión",
    "Edge: modal de configuración", "Edge: descripción de configuración",
    "Edge: formulario de ajuste", "Edge: confirmación de ajuste",
    "Edge: sección de detalle", "Edge: parámetros de agente", "Edge: permisos y texto",
    "Edge: controles de parámetros", "Edge: error o aviso contextual",
    "Edge: respuesta extensa del asistente", "Edge: respuesta con secciones",
    "Edge: seguimiento de ejecución", "Edge: estado de ejecución",
    "Edge: resultado con bloques de código", "Edge: resultado revisado",
    "Edge: controles de revisión", "Edge: tarjetas de tarea", "Edge: estado de tarjeta",
    "Edge: más opciones de tarjeta", "Edge: respuesta y resumen", "Edge: lista y navegación",
    "Edge: navegación lateral", "Edge: tabla de estados", "Edge: pestañas de ajustes",
    "Grok: creación de bot", "Grok: ajuste de bot", "Grok: selector de modelo",
    "Grok: feedback de creación", "Manus: acción de agente en móvil",
    "Chrome: estructura de escritorio", "Chrome: panel y métricas de escritorio",
    "Chrome: lista de conectores", "Chrome: cards y navegación",
    "Chrome: densidad de información y estados", "Claude: chat y composición",
    "Claude: conversación y revisión", "Chrome: escritorio con paneles y acciones",
]


def build_catalog() -> dict:
    files = sorted(IMAGES.glob("*.png"))
    if len(files) != len(ROLES):
        raise ValueError("IMAGE_COUNT_CHANGED: revisar asignación manual de roles")
    entries = []
    seen: dict[str, str] = {}
    for index, (path, role) in enumerate(zip(files, ROLES, strict=True), 1):
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"NOT_PNG:{path.name}")
        width, height = struct.unpack(">II", data[16:24])
        digest = hashlib.sha256(data).hexdigest()
        entries.append({
            "id": f"UI-REF-{index:03}", "file": str(path.relative_to(ROOT)),
            "original": f"📂 Skills Maxbry UI fromtend/diseno/{path.name}",
            "sha256": digest, "duplicate_of": seen.get(digest),
            "format": "PNG", "bytes": len(data), "width": width, "height": height,
            "function": role, "classification": "REFERENCE_ONLY",
            "frontend": "chat router/ui/shell.css" if index <= 3 else "chat router/ui/shell.html",
            "backend": "NOT_CONNECTED", "contract": [SKILL, PALETTE, SPEC],
            "verification": "T-06: comparación visual y prueba de interacción pendientes",
            "status": "PENDING_VISUAL_VERIFICATION", "secret_review": "PENDING",
        })
        seen.setdefault(digest, f"UI-REF-{index:03}")
    for entry in entries:
        if not all((ROOT / contract).is_file() for contract in entry["contract"]):
            raise ValueError("SKILL_CONTRACT_MISSING")
    return {"schema": "yaiwes.visual-reference-catalog/v1", "count": len(entries),
            "source": "main + Git rename sin cambio de bytes", "items": entries}


def build_extra_catalog() -> dict:
    groups = {
        "ARQUITECTURA-ROUTER": ("Diagrama de arquitectura del Router", 5),
        "ADJUNTOS-CHAT": ("Captura de conversación, propuesta o revisión del PR", 12),
    }
    entries = []
    seen: dict[str, str] = {}
    for group, (role, expected) in groups.items():
        files = sorted((IMAGES / group).glob("*.png"))
        if len(files) != expected:
            raise ValueError(f"EXTRA_IMAGE_COUNT_CHANGED:{group}")
        for path in files:
            data = path.read_bytes()
            if data[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError(f"NOT_PNG:{path.name}")
            width, height = struct.unpack(">II", data[16:24])
            digest = hashlib.sha256(data).hexdigest()
            entry = {
                "id": f"UI-EXTRA-{len(entries) + 1:03}", "group": group,
                "file": str(path.relative_to(ROOT)), "sha256": digest,
                "duplicate_of": seen.get(digest), "bytes": len(data),
                "width": width, "height": height, "function": role,
                "classification": "REFERENCE_ONLY", "backend": "NOT_CONNECTED",
                "verification": "🚩 PENDIENTE: integración funcional y read-back",
            }
            if path.name == "Screenshot_20261001-093043_Edge.png":
                entry.update({
                    "function": "Captura de la selección GPT-6 Sol en la aplicación del usuario; evidencia visual de selección, no del modelo interno de Devin",
                    "backend": "CATALOG_METADATA_ONLY",
                    "verification": "🚩 PENDIENTE: verificación independiente del modelo activo",
                })
            entries.append(entry)
            seen.setdefault(digest, entries[-1]["id"])
    return {"schema": "yaiwes.visual-annex-catalog/v1", "count": len(entries), "items": entries}


def main() -> None:
    catalog = build_catalog()
    extra = build_extra_catalog()
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EXTRA_OUTPUT.write_text(json.dumps(extra, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if json.loads(OUTPUT.read_text(encoding="utf-8")) != catalog:
        raise OSError("CATALOG_READBACK_FAILED")
    if json.loads(EXTRA_OUTPUT.read_text(encoding="utf-8")) != extra:
        raise OSError("EXTRA_CATALOG_READBACK_FAILED")
    print(f"Verificadas {catalog['count']} referencias; duplicados: "
          f"{sum(bool(item['duplicate_of']) for item in catalog['items'])}; "
          f"{extra['count']} anexos visuales")


if __name__ == "__main__":
    main()
