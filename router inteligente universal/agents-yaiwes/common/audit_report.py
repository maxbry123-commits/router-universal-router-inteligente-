"""Deterministic report of the auditor: merges the JSON of every audit pass into AUDIT-CHECKLIST.md (no LLM).
Sections by status (HECHO / PARCIAL / PENDIENTE / AMBIGUO / REFUTADO), each item with its verbatim quote, evidence paths and note."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ORDER = ("REFUTADO", "PENDIENTE", "AMBIGUO", "PARCIAL", "HECHO")


def build(agent_dir: str) -> Path:
    items: list[dict] = []
    for out in sorted((Path(agent_dir) / "steps").glob("audit_pass_*/results/output.txt")):
        try:
            body = re.sub(r"^```(?:json)?\s*|\s*```$", "", out.read_text(encoding="utf-8").strip())
            data = json.loads(body[body.find("{"): body.rfind("}") + 1])
            for it in data.get("items", []):
                it["_pass"] = out.parents[1].name
                items.append(it)
        except Exception:  # noqa: BLE001 - an unreadable pass is simply not merged
            continue
    seen, merged = set(), []
    for it in items:
        key = re.sub(r"\s+", " ", str(it.get("quote", ""))).strip().lower()[:120]
        if key and key not in seen:
            seen.add(key)
            merged.append(it)
    lines = [f"# AUDIT-CHECKLIST — {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}", "",
             "Generado por el agente auditor (pasos `audit_pass_*`, validados por el Sheriff: cada cita es textual del Director y cada evidencia existe en el repo) "
             "y unido de forma determinista. Refutado = el trabajo de un agente no cumple lo pedido.", "",
             "| estado | ítems |", "|---|---|"] + [f"| {s} | {sum(1 for i in merged if i.get('status') == s)} |" for s in ORDER] + [""]
    for s in ORDER:
        rows = [i for i in merged if i.get("status") == s]
        if not rows:
            continue
        lines += [f"## {s}", ""]
        for i in rows:
            ev = ", ".join(f"`{e}`" for e in (i.get("evidence") or [])) or "-"
            lines += [f"- **{i.get('id', '?')}** ({i.get('_pass')}) «{str(i.get('quote', '')).strip()}»", f"  - evidencia: {ev}", f"  - nota: {i.get('note', '-')}"]
        lines.append("")
    path = Path(agent_dir) / "AUDIT-CHECKLIST.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
