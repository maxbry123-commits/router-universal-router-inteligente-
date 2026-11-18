"""nct_format.py — NCT/APEX: entrada 📌, 4 formatos normalizados, Mapa Mental,
botonera y handoff interno.

FIX (MINIMAX 2F) — el chat no tenia formato de salida ni de entrada: la
respuesta cruda del motor se volcaba tal cual en el bubble y el bloque 📌 se
mandaba como texto suelto. Este modulo implementa el sistema que describio el
Director:

  · CLASIFICADOR  -> pregunta / investigacion / programacion / auditoria /
                      arquitectura / agentico / proyecto / comando
  · INPUT  -> F1 (corto) o F2 (largo)   · si no encaja, se pide reformulacion
  · OUTPUT -> F3 (corto) o F4 (largo, con Mapa Mental)
  · BOTONERA -> 9 botones (+ HANDOFF, solo lectura)
  · CAPA INTERNA (NO visible en el chat) -> handoff JSON dual-output
    (---RESULT_START--- / ---RESULT_END---) + bitacora append-only.

Reglas duras del sistema:
  · El handoff y la bitacora NO se muestran en el chat.
  · No se inventan porcentajes: si no hay criterios medidos, se escribe "—".
  · Todo es determinista: sin red, sin reloj en el texto renderizado.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------
# CLASIFICADOR
# --------------------------------------------------------------------------
CLASSIFIER_RULES = [
    ("auditoria", (r"\baudit", r"\bauditor", r"\bforense", r"\bx-?ray", r"\bgap\b", r"\brefactor", r"\bdepur")),
    ("agentico", (r"\bagent", r"\bhermes", r"\bopenclaw", r"\bruflo", r"\browboat", r"\bherramienta", r"\btool\b", r"\bmcp\b")),
    ("programacion", (r"\bcodigo", r"\bcode", r"\bpython", r"\bjavascript", r"\bhtml", r"\bscript", r"\bimplementa", r"\bfuncion", r"\bbug", r"\berror", r"\btestimpio")),
    ("arquitectura", (r"\barquitect", r"\bdesign", r"\bdiseño", r"\bestructura", r"\bcablea", r"\bwiring", r"\bintegrar")),
    ("investigacion", (r"\binvestiga", r"\bbusca", r"\bresearch", r"\bcompara", r"\bfuentes", r"\bverifica si", r"\bdocumenta")),
    ("proyecto", (r"\bproyecto", r"\bplan", r"\bplanifica", r"\bhito", r"\bsprint", r"\bbacklog", r"\bprioridad")),
    ("comando", (r"\bdespliega", r"\bdeploy", r"\bpush", r"\bcommit", r"\binstala", r"\bpublica", r"\bcorre\b")),
]

OUTPUT_FORMATS = {
    "pregunta": "F3",
    "investigacion": "F3",
    "programacion": "F4",
    "auditoria": "F4",
    "arquitectura": "F4",
    "agentico": "F4",
    "proyecto": "F4",
    "comando": "F4",
}

INPUT_FORMATS = {
    "pregunta": "F1",
    "investigacion": "F1",
    "programacion": "F2",
    "auditoria": "F2",
    "arquitectura": "F2",
    "agentico": "F2",
    "proyecto": "F2",
    "comando": "F2",
}

STATES = [
    "PENDING", "RESEARCHING", "PLANNING", "AWAITING_APPROVAL", "EXECUTING",
    "VALIDATING", "GAP", "FIXING", "RETESTING", "STABLE", "BLOCKED", "CLOSED",
]

BOTONERA = [
    {"id": "audit_xray", "label": "🔍 AUDIT X-RAY", "action": "Auditar respuesta, docs y codigo", "approval": False},
    {"id": "input_shark", "label": "🦈 INPUT SHARK", "action": "Investigar y contrastar fuentes", "approval": False},
    {"id": "mapa_mental", "label": "🧠 MAPA MENTAL", "action": "Mostrar 10 vistas o mapa reducido", "approval": False},
    {"id": "analisis", "label": "📊 ANALISIS", "action": "Profundizar razonamiento tecnico", "approval": False},
    {"id": "propuesta", "label": "💡 PROPUESTA", "action": "Generar mejoras y recomendaciones", "approval": False},
    {"id": "refactorizar", "label": "🛠️ REFACTORIZAR", "action": "Preparar/ejecutar refactor", "approval": True},
    {"id": "modo_agentico", "label": "🤖 MODO AGENTICO", "action": "Activar agentes y herramientas", "approval": True},
    {"id": "validar", "label": "✅ VALIDAR", "action": "Ejecutar verificaciones y pruebas", "approval": False},
    {"id": "recovery", "label": "♻️ RECOVERY", "action": "Recuperar estado de tarea anterior", "approval": False},
    {"id": "handoff", "label": "🔒 HANDOFF", "action": "Ver el JSON de handoff de la tarea actual", "approval": False},
]


def classify_input(text: str) -> Dict[str, Any]:
    """Clasifica el input del Director y fija los formatos de entrada/salida.

    El tipo se decide por ESPECIFICIDAD (cuantas reglas casan), no por el orden
    del diccionario: "refactoriza este codigo python" es PROGRAMACION (3 reglas)
    aunque tambien case "refactor" (1 regla). Empate -> la primera regla en
    orden de peso.
    """
    raw = (text or "").lower()
    scores: Dict[str, int] = {}
    matched: List[str] = []
    for name, patterns in CLASSIFIER_RULES:
        hits = 0
        for pattern in patterns:
            if re.search(pattern, raw, re.IGNORECASE):
                hits += 1
        if hits:
            scores[name] = hits
            matched.append(name)
    kind = "pregunta"
    if scores:
        order = {name: i for i, (name, _p) in enumerate(CLASSIFIER_RULES)}
        kind = max(scores.items(), key=lambda kv: (kv[1], -order[kv[0]]))[0]
    long_input = len(raw) > 400 or "### PLANIFICACIÓN" in (text or "")
    fmt_in = "F2" if (long_input or kind not in ("pregunta",)) else "F1"
    if kind == "pregunta" and long_input:
        fmt_in = "F2"
    return {
        "kind": kind,
        "format_in": fmt_in,
        "format_out": OUTPUT_FORMATS.get(kind, "F4"),
        "matched": matched,
        "scores": scores,
        "long": long_input,
    }


# --------------------------------------------------------------------------
# PARSE DEL BLOQUE 📌 (INPUT)
# --------------------------------------------------------------------------
def _clean_lines(lines: List[str]) -> List[str]:
    return [ln.rstrip() for ln in lines]


def parse_input_block(text: str) -> Dict[str, Any]:
    """Parsea el bloque 📌 literal (F1 o F2) en campos verificables.

    Devuelve SIEMPRE las mismas claves, aunque el bloque este incompleto:
    lo que no se encuentra queda vacio (no se inventa).
    """
    src = text or ""
    lines = src.splitlines()
    out: Dict[str, Any] = {
        "raw": src,
        "objetivo": "",
        "interpretacion": [],
        "preguntas": [],
        "plan": "",
        "microflujo": "",
        "restricciones": "",
        "criterios": [],
        "archivos": [],
        "rollback": "",
        "decision": "",
        "formato": "F1" if "F1" in src[:120] else ("F2" if "F2" in src[:120] else ""),
        "es_bloque": bool(re.search(r"F[12]\s*[-—·]\s*INPUT", src, re.IGNORECASE)),
        "flags": [],
    }

    def grab(pattern: str, flags=re.IGNORECASE) -> str:
        m = re.search(pattern, src, flags)
        return m.group(1).strip() if m else ""

    out["objetivo"] = grab(r"\*\*Objetivo:\*\*\s*(.+)") or grab(r"^#+\s*.*?Objetivo.*?\n+(.+)$", re.IGNORECASE | re.MULTILINE)

    # MI INTERPRETACION (lista)
    m = re.search(r"MI INTERPRETACI[ÓO]N:?\s*(.+?)(?=\n\s*\*\*PREGUNTAS|\n\s*\*\*PLAN|\Z)", src, re.IGNORECASE | re.DOTALL)
    if m:
        out["interpretacion"] = [
            re.sub(r"^[-*\d.\s]+", "", ln).strip()
            for ln in _clean_lines(m.group(1).splitlines())
            if ln.strip()
        ]

    # PREGUNTAS DE CLARIFICACION (max 3)
    m = re.search(r"PREGUNTAS DE CLARIFICACI[ÓO]N.*?\n(.*?)(?=\n\s*\*\*PLAN|\n\s*\*\*Restricciones|\Z)", src, re.IGNORECASE | re.DOTALL)
    if m:
        qs = [re.sub(r"^\s*\d+[.)]\s*", "", ln).strip() for ln in m.group(1).splitlines() if ln.strip()]
        out["preguntas"] = [q for q in qs if q][:3]

    # PLAN PROPUESTO + microflujo
    m = re.search(r"PLAN PROPUESTO.*?\n(.*?)(?=\n\s*\*\*Restricciones|\n\s*###|\n\s*\*\*Criterio|\Z)", src, re.IGNORECASE | re.DOTALL)
    if m:
        block = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
        flow = [ln for ln in block if "→" in ln]
        out["microflujo"] = flow[-1] if flow else ""
        out["plan"] = " / ".join(ln for ln in block if ln and "→" not in ln) or (flow[-1] if flow else "")

    out["restricciones"] = grab(r"\*\*Restricciones:\*\*\s*(.+)")
    out["criterio_exito"] = grab(r"\*\*Criterio de [ée]xito:\*\*\s*(.+)")

    # CRITERIOS DE EXITO (checkboxes)
    m = re.search(r"CRITERIOS DE [ÉE]XITO(.*?)(?=\n\s*###|\n\s*\*\*|\Z)", src, re.IGNORECASE | re.DOTALL)
    if m:
        out["criterios"] = [
            re.sub(r"^\s*[-*]\s*\[[ xX]\]\s*", "", ln).strip()
            for ln in m.group(1).splitlines()
            if re.match(r"^\s*[-*]\s*\[[ xX]\]", ln)
        ]

    # ARCHIVOS A MODIFICAR / CREAR
    m = re.search(r"ARCHIVOS A MODIFICAR.*?\n(.*?)(?=\n\s*###|\n\s*\*\*ROLLBACK|\Z)", src, re.IGNORECASE | re.DOTALL)
    if m:
        out["archivos"] = [
            re.sub(r"^\s*[-*]\s*", "", ln).strip()
            for ln in m.group(1).splitlines()
            if ln.strip().startswith(("`", "-", "*"))
        ]

    # ROLLBACK
    m = re.search(r"ROLLBACK SI FALLA.*?```(?:bash|sh)?\s*(.+?)```", src, re.IGNORECASE | re.DOTALL)
    if m:
        out["rollback"] = m.group(1).strip()

    # DECISION
    out["decision"] = grab(r"·\s*APUEBA", re.IGNORECASE) or ""
    if re.search(r"APUEBA", src, re.IGNORECASE):
        out["decision"] = "APRUEBA"
    elif re.search(r"MODIFICA", src, re.IGNORECASE):
        out["decision"] = "MODIFICA"
    elif re.search(r"CANCEL", src, re.IGNORECASE):
        out["decision"] = "CANCEL"

    if out["objetivo"] and not out["criterios"]:
        out["criterios"] = []
    if not out["objetivo"]:
        out["flags"].append("sin_objetivo")
    return out


def render_input_preview(parsed: Dict[str, Any], classification: Dict[str, Any]) -> str:
    """Vista previa del input parseado (lo que ve el Director antes de aprobar)."""
    lines = [
        f"# {classification.get('format_in')} — INPUT {'CORTO' if classification.get('format_in') == 'F1' else 'LARGO'}",
        "",
        f"**Objetivo:** {parsed.get('objetivo') or '—'}",
        "",
        "**MI INTERPRETACIÓN:**",
    ]
    for item in (parsed.get("interpretacion") or [])[:5]:
        lines.append(f"- {item}")
    if not parsed.get("interpretacion"):
        lines.append("- —")
    lines += ["", "**PREGUNTAS DE CLARIFICACIÓN (máx 3):**"]
    qs = parsed.get("preguntas") or []
    for i, q in enumerate(qs, 1):
        lines.append(f"{i}. {q}")
    if not qs:
        lines.append("1. —")
    lines += [
        "",
        "**PLAN PROPUESTO — requiere aprobación**",
        "Micro-flujo horizontal:",
        parsed.get("microflujo") or "ACCIÓN A → ACCIÓN B → REVISIÓN → REFACTORÍA → VALIDACIÓN",
        "",
        f"**Restricciones:** {parsed.get('restricciones') or '—'}",
        f"**Criterio de éxito:** {parsed.get('criterio_exito') or '—'}",
        "",
        "**CLASIFICADOR:** " + f"{classification.get('kind')} · entrada {classification.get('format_in')} · salida {classification.get('format_out')}",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# MAPA MENTAL
# --------------------------------------------------------------------------
def _pct(done: Optional[int], total: Optional[int]) -> str:
    """Porcentaje SOLO si hay criterios medidos; si no, '—' (nunca inventado)."""
    if not total:
        return "—"
    try:
        return f"{int(round(100.0 * float(done) / float(total)))}%"
    except (TypeError, ValueError):
        return "—"


def render_mind_map(data: Dict[str, Any], full: bool = True) -> str:
    """Mapa Mental: 10 vistas (F4) o 5 elementos (F3).

    La vista MADUREZ se calcula con los criterios reales del handoff; sin
    handoff valido se escribe '—' (nunca 0% ni 100% inventados).
    """
    d = data or {}
    objetivo = d.get("objetivo") or "—"
    grupos = d.get("grupos") or []
    pos = d.get("posicion") or {}
    props = d.get("proposito") or []
    io = d.get("entrada_salida") or []
    raiz = d.get("raiz") or []
    desbloquea = d.get("desbloquea") or []
    evidencia = d.get("evidencias") or []
    micro = d.get("microflujo") or [
        "Define objetivo → Carga mínimo → Sigue orden → Verifica checklist → Muestra estado → Para si falla",
    ]

    def bloque(titulo, cuerpo, para=""):
        return f"{titulo}\n{cuerpo}\n→ Para qué: {para}\n"

    out = []
    out.append(bloque(
        "🌐 VISIÓN GLOBAL PERFIL",
        "OBJETIVO → DEFINIR MÉTODO → DISEÑAR SISTEMA → CONSTRUIR PIEZAS → INTEGRAR TODO → AUDITAR Y CERRAR",
        "ver el proyecto completo en 5 segundos",
    ))
    out.append(bloque(
        "🏗 ARQUITECTURA GLOBAL",
        " → ".join([g.get("name", "?") for g in grupos]) or "—",
        "entender como se conectan los grupos",
    ))
    out.append(bloque(
        "📍 POSICIÓN ACTUAL",
        "\n".join(f"{g.get('name','?')}\n" + "\n".join(
            f"├─ {p.get('name','?')}" + (" ← ACTUAL" if p.get("actual") else "")
            for p in (g.get("piezas") or [])
        ) for g in grupos) or "—",
        "saber exactamente donde estamos",
    ))
    out.append(bloque(
        "🔗 ROMPECABEZAS (dependencias cruzadas)",
        d.get("rompecabezas") or " → ".join([g.get("name", "?") for g in grupos]) or "—",
        "ver que bloquea que",
    ))
    out.append(bloque(
        "🎯 PROPÓSITO",
        "\n".join(props) or "—",
        "justificar cada componente",
    ))
    out.append(bloque(
        "📥 ENTRADA / SALIDA",
        "\n".join(io) or "—",
        "contrato exacto entre piezas",
    ))
    out.append(bloque(
        "🌱 RAÍZ / ORGANIZACIÓN / DESTINO",
        "\n".join(raiz) or "—",
        "saber donde vive cada artefacto",
    ))
    out.append(bloque(
        "🚀 DESBLOQUEA",
        "\n".join(desbloquea) or "—",
        "ver consecuencias de terminar",
    ))
    out.append(bloque(
        "📊 MADUREZ",
        "\n".join([
            f"{g.get('name','?')}     {'█' * int(_bar(_pct(g.get('done'), g.get('total'))))}{'░' * (10 - int(_bar(_pct(g.get('done'), g.get('total')))))} {_pct(g.get('done'), g.get('total'))}"
            for g in grupos
        ]) or "—",
        "ver progreso real (derivado de criterios, no inventado)",
    ))
    out.append(bloque(
        "⚙️ MICROFLUJO — pieza activa",
        micro[0] if isinstance(micro, list) and micro else str(micro),
        "el flujo de la pieza en curso",
    ))
    out.append(bloque(
        "🧩 ENSAMBLAJE FINAL",
        d.get("ensamblaje") or " → ".join([g.get("name", "?") for g in grupos]) or "—",
        "ver como todas las piezas forman un solo sistema",
    ))
    if not full:
        out = [out[0], out[2], out[5], out[8], out[9]]
    if evidencia:
        out.append("📎 EVIDENCIAS\n" + "\n".join(f"· {e}" for e in evidencia))
    return "\n".join(out)


def _bar(pct: str) -> float:
    try:
        return max(0.0, min(10.0, float(str(pct).rstrip("%")) / 10.0))
    except (TypeError, ValueError):
        return 0.0


def render_mind_map_reduced(data: Dict[str, Any]) -> str:
    return render_mind_map(data, full=False)


# --------------------------------------------------------------------------
# BOTONERA
# --------------------------------------------------------------------------
def render_botonera(active: Optional[List[str]] = None) -> str:
    """Botonera inferior del sistema (9 botones + HANDOFF)."""
    active = set(active or [])
    lines = ["┌─────────────────────────────────────────────────────────────┐",
             "│  🎛️  BOTONERA NCT/APEX                                       │",
             "├─────────────────────────────────────────────────────────────┤"]
    fila = []
    for b in BOTONERA:
        mark = " ●" if b["id"] in active else ""
        fila.append(f"[{b['label']}{mark}]".ljust(19))
        if len(fila) == 3:
            lines.append("│  " + " ".join(fila).rstrip().ljust(63) + "│")
            fila = []
    if fila:
        lines.append("│  " + " ".join(fila).rstrip().ljust(63) + "│")
    lines.append("└─────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# OUTPUT F3 / F4
# --------------------------------------------------------------------------
def render_f3(data: Dict[str, Any]) -> str:
    """F3 — OUTPUT CORTO (sin codigo, sin arquitectura)."""
    d = data or {}
    estado = d.get("estado") or "PENDING"
    if estado not in STATES:
        estado = "PENDING"
    propuesta = d.get("propuesta") or []
    texto = d.get("texto") or d.get("resumen") or "—"
    texto_lineas = [ln for ln in str(texto).splitlines() if ln.strip()][:5]
    flags = d.get("flags") or []
    gap = d.get("gap")
    if isinstance(gap, dict):
        gap_txt = f"{gap.get('count', 1)} · {gap.get('motivo', '')}".strip(" ·")
    elif gap:
        gap_txt = str(gap)
    else:
        gap_txt = "—"
    prog = d.get("progreso") if d.get("progreso") not in (None, "") else "—"
    lineas = [
        "# 🟢 F3 — OUTPUT CORTO",
        "",
        f"**OBJETIVO:** {d.get('objetivo') or '—'} ✅",
        f"**PROGRESO:** {prog} | **TIEMPO:** {d.get('tiempo') or '—'}",
        f"**TAREAS PENDIENTES:** {d.get('pendientes') if d.get('pendientes') is not None else '—'}",
        f"**CONFIRMA INPUT BLOCK VERBATIM:** {'✅' if d.get('confirma_input') else '❌'}",
        f"**INSTRUCCIONES:** {'SÍ' if d.get('instrucciones') else 'NO'}",
        f"**ESTADO:** {estado}",
        "**OUTPUT_EXTRA_TEXT:** DENY",
        "",
        "**TEXTO:**",
    ]
    lineas += texto_lineas or ["—"]
    lineas += [
        "",
        f"**ESTATUS:** {prog} + 🚩 FLAGS {len(flags)} + GAP:{gap_txt}",
        f"**MOTORES DE INVESTIGACIÓN ACTIVO:** {'✅' if d.get('motores_activos') else '—'}",
        f"**FIX:** {d.get('fix') or '—'}",
        "",
    ]
    if propuesta:
        lineas.append(f"**PROPUESTA ({len(propuesta)} recomendaciones) →**")
        for i, item in enumerate(propuesta[:10], 1):
            lineas.append(f"{i}. {item}")
        lineas.append("")
    lineas.append(render_mind_map_reduced(d))
    lineas.append("")
    lineas.append(render_botonera(d.get("botonera_activa")))
    return "\n".join(lineas)


def render_f4(data: Dict[str, Any]) -> str:
    """F4 — OUTPUT LARGO (codigo + arquitectura + Mapa Mental)."""
    d = data or {}
    estado = d.get("estado") or "PENDING"
    if estado not in STATES:
        estado = "PENDING"
    codigo = d.get("codigo") or ""
    lineas = [
        "# 🔵 F4 — OUTPUT LARGO · MODO AGÉNTICO / TOOL",
        "",
        f"**OBJETIVO:** {d.get('objetivo') or '—'}",
        f"**PROGRESO:** {d.get('progreso') or '—'} | **TIEMPO:** {d.get('tiempo') or '—'} | **TAREAS PENDIENTES:** {d.get('pendientes') if d.get('pendientes') is not None else '—'}",
        f"**ESTADO:** {estado}",
        "",
        "## 1. ANÁLISIS",
        d.get("analisis") or "—",
        "",
        "## 2. ARQUITECTURA",
        d.get("arquitectura") or "—",
        "",
        "## 3. MAPA MENTAL — 10 VISTAS",
        render_mind_map(d, full=True),
        "",
        "## 4. CÓDIGO / ARTEFACTOS",
    ]
    if codigo:
        lineas += [f"```{d.get('lenguaje') or 'text'}", codigo, "```"]
    else:
        lineas.append("—")
    lineas += [
        "",
        "## 5. AUDITORÍA (si aplica)",
        d.get("auditoria") or "—",
        "",
        "## 6. PLAN DE ACCIÓN",
    ]
    for i, step in enumerate(d.get("plan") or [], 1):
        lineas.append(f"{i}. {step}")
    if not d.get("plan"):
        lineas.append("—")
    lineas += [
        "",
        "## 7. EVIDENCIAS / VALIDACIÓN",
    ]
    for ev in d.get("evidencias") or []:
        lineas.append(f"· {ev}")
    if not d.get("evidencias"):
        lineas.append("—")
    lineas += [
        "",
        "## 8. PRÓXIMA ACCIÓN",
        d.get("proxima_accion") or "—",
        "",
        render_botonera(d.get("botonera_activa")),
    ]
    return "\n".join(lineas)


def render_output(data: Dict[str, Any], fmt: Optional[str] = None) -> Dict[str, Any]:
    """Renderiza la salida normalizada (F3 o F4) + el handoff interno."""
    fmt = (fmt or data.get("format") or "F3").upper()
    if fmt not in ("F3", "F4"):
        fmt = "F3"
    markdown = render_f4(data) if fmt == "F4" else render_f3(data)
    handoff = build_handoff(data)
    return {
        "ok": True,
        "format": fmt,
        "markdown": markdown,
        "handoff": handoff,
        "handoff_block": render_handoff_block(handoff),
        "botonera": BOTONERA,
    }


# --------------------------------------------------------------------------
# CAPA INTERNA: handoff dual-output + bitacora append-only
# --------------------------------------------------------------------------
HANDOFF_START = "---RESULT_START---"
HANDOFF_END = "---RESULT_END---"


def build_handoff(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handoff JSON (agente -> LLM). NO se muestra en el chat."""
    criterios = data.get("criterios") or []
    criterios_state = {}
    for c in criterios:
        if isinstance(c, dict):
            criterios_state[c.get("id", c.get("name", "?"))] = c.get("state", "CHECKING")
        else:
            criterios_state[str(c)] = "CHECKING"
    return {
        "handoff_id": data.get("handoff_id") or "",
        "from_agent": data.get("from_agent") or "orchestrator",
        "to_agent": data.get("to_agent") or "orchestrator",
        "task_intent": data.get("objetivo") or "",
        "constraints": data.get("constraints") or ["F1", "F2"],
        "summary": data.get("resumen") or (data.get("texto") or "")[:400],
        "artifacts": data.get("artifacts") or [],
        "state": {
            "phase": data.get("fase") or "PREPARATION",
            "criteria": criterios_state,
        },
        "next_phase": data.get("next_phase") or "SYNTHESIS",
        "handoff_recommendation": data.get("recomendacion") or "",
    }


def render_handoff_block(handoff: Dict[str, Any]) -> str:
    """Bloque delimitado que se pega al final de la prosa del agente."""
    return f"{HANDOFF_START}\n{json.dumps(handoff, ensure_ascii=False, indent=2)}\n{HANDOFF_END}"


def parse_handoff(text: str) -> Optional[Dict[str, Any]]:
    """Extrae el handoff JSON de un texto (None si no hay o no valida)."""
    if not text or HANDOFF_START not in text or HANDOFF_END not in text:
        return None
    block = text.split(HANDOFF_START, 1)[1].split(HANDOFF_END, 1)[0].strip()
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "summary" not in data:
        return None
    return data


def _state_dir() -> Path:
    env = os.getenv("AGENT_STATE_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (Path(__file__).resolve().parent.parent / "state").resolve()


def crazy_wall_append(event: Dict[str, Any]) -> Dict[str, Any]:
    """Bitacora append-only (una linea JSON por evento)."""
    entry = {
        "ts": event.get("ts") or "",
        "session_id": event.get("session_id") or "",
        "agent": event.get("agent") or "orchestrator",
        "event": event.get("event") or "decision",
        "payload": event.get("payload") or {},
        "parent_event": event.get("parent_event"),
        "taint": event.get("taint") or "clean",
    }
    path = _state_dir() / "crazy_wall.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError as exc:
        raise RuntimeError(f"no se pudo escribir la bitacora: {exc}") from exc
    return entry


def crazy_wall_read(limit: int = 50) -> List[Dict[str, Any]]:
    path = _state_dir() / "crazy_wall.jsonl"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except FileNotFoundError:
        return []
    out = []
    for line in lines[-max(1, int(limit or 50)):]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.reverse()
    return out


def recovery_state() -> Dict[str, Any]:
    """Estado de recuperacion: se RECONSTRUYE del handoff + la bitacora.

    No es un archivo aparte: sale de los eventos reales (nada duplicado).
    """
    wall = crazy_wall_read(20)
    last_handoff = None
    for event in wall:
        payload = event.get("payload") or {}
        if isinstance(payload, dict) and payload.get("handoff"):
            last_handoff = payload["handoff"]
            break
    return {
        "ok": True,
        "events": len(wall),
        "last_event": wall[0] if wall else None,
        "last_handoff": last_handoff,
        "source": "crazy_wall.jsonl",
    }
