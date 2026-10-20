"""Deterministic report of the auditor: merges the JSON of every audit pass (steps `lens_*` and the older `audit_pass_*`) into
  AUDIT-CHECKLIST.md  — by status (REFUTADO / PENDIENTE / AMBIGUO / PARCIAL / HECHO), each item with its verbatim quote, evidence and note;
  DELEGACION.md       — the list of what will be handed to the agents: every item that is not HECHO, grouped by area, with its task.
No LLM. Quotes and evidence paths were already verified by the Sheriff (verbatim / existing)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ORDER = ("REFUTADO", "PENDIENTE", "AMBIGUO", "PARCIAL", "HECHO")
AREAS = ("chat", "almacenamiento", "agentes", "modelos", "aceleradores")


def load(agent_dir: str) -> list[dict]:
    items: list[dict] = []
    for out in sorted((Path(agent_dir) / "steps").glob("*/results/output.txt")):
        step = out.parents[1].name
        if not step.startswith(("lens_", "audit_pass_")):
            continue
        try:
            body = re.sub(r"^```(?:json)?\s*|\s*```$", "", out.read_text(encoding="utf-8").strip())
            for it in json.loads(body[body.find("{"): body.rfind("}") + 1]).get("items", []):
                it["_pass"] = step
                items.append(it)
        except Exception:  # noqa: BLE001 - an unreadable pass is simply not merged
            continue
    seen, merged = set(), []
    for it in items:
        key = re.sub(r"\s+", " ", str(it.get("quote", ""))).strip().lower()[:120]
        if key and key not in seen:
            seen.add(key)
            merged.append(it)
    return merged


def build(agent_dir: str) -> Path:
    merged = load(agent_dir)
    now = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())
    lines = [f"# AUDIT-CHECKLIST — {now}", "",
             "Generado por el agente auditor (pasadas `lens_*`, validadas por el Sheriff: cada cita es textual del Director y cada evidencia existe en el repo) "
             "y unido de forma determinista. Refutado = el trabajo de un agente no cumple lo pedido.", "",
             "| estado | ítems |", "|---|---|"] + [f"| {s} | {sum(1 for i in merged if i.get('status') == s)} |" for s in ORDER] + [""]
    for s in ORDER:
        rows = [i for i in merged if i.get("status") == s]
        if not rows:
            continue
        lines += [f"## {s}", ""]
        for i in rows:
            ev = ", ".join(f"`{e}`" for e in (i.get("evidence") or [])) or "-"
            lines += [f"- **{i.get('id', '?')}** ({i.get('_pass')}, {i.get('area', 'sin_area')}) «{str(i.get('quote', '')).strip()}»", f"  - evidencia: {ev}", f"  - nota: {i.get('note', '-')}"]
        lines.append("")
    path = Path(agent_dir) / "AUDIT-CHECKLIST.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    todo = [i for i in merged if i.get("status") != "HECHO"]
    d = [f"# DELEGACIÓN — lo que se manda hacer a los agentes ({now})", "",
         f"Sale de la auditoría de las notas del Director en 4 pasadas ({len(merged)} requisitos: {len(merged) - len(todo)} HECHO, {len(todo)} por hacer). "
         "Prioridad del Director: SOLO el chat y los modelos de IA locales.", ""]
    for area in (*AREAS, "sin_area"):
        rows = [i for i in todo if (i.get("area") or "sin_area") == area or (area == "sin_area" and i.get("area") not in AREAS)]
        if not rows:
            continue
        d += [f"## {area} ({len(rows)})", ""]
        for i in sorted(rows, key=lambda x: ORDER.index(x.get("status")) if x.get("status") in ORDER else 9):
            d += [f"- [{i.get('status')}] **{i.get('id', '?')}** — {i.get('tarea') or i.get('note') or 'sin tarea escrita'}", f"  - pedido: «{str(i.get('quote', '')).strip()}»"]
        d.append("")
    (Path(agent_dir) / "DELEGACION.md").write_text("\n".join(d), encoding="utf-8")
    return path
