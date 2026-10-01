"""Compilador de busquedas determinista (sin LLM) para T07.

Genera consultas a partir de plantillas por task_type y por goal (G01..G12).
"""
import goals

# Plantillas adicionales por task_type.
TASK_TEMPLATES = {
    "SEARCH": ["{target} documentacion", "{target} ejemplos"],
    "INSTALL": ["{target} install guide", "{target} pip install requirements"],
    "DOWNLOAD": ["{target} download official", "{target} releases download"],
    "EXTRACT": ["{target} extract archive docs"],
    "DEPLOY": ["{target} deploy guide", "{target} production deployment checklist"],
    "MODIFY_CODE": ["{target} contributing guide", "{target} code style"],
    "DEBUG": ["{target} troubleshooting", "{target} known issues error"],
    "TEST": ["{target} testing guide", "{target} pytest CI"],
    "COMPARE": ["{target} vs alternativas", "{target} comparison benchmark"],
    "AUDIT": ["{target} security audit", "{target} CVE vulnerabilities"],
    "RESEARCH": ["{target} overview architecture", "{target} design docs"],
    "VERIFY": ["{target} verification steps", "{target} acceptance criteria"],
}


def _render(template, parsed):
    target = parsed["targets"][0] if parsed["targets"] else parsed["raw"][:60]
    task = parsed["raw"][:80] or target
    return template.replace("{target}", target).replace("{task}", task).strip()


def compilar(parsed, goal_ids=None):
    """Devuelve lista de consultas deterministas: [{goal, query}]."""
    goal_ids = goal_ids or goals.GOAL_IDS
    queries = []
    task_type = parsed.get("task_type", "UNKNOWN")
    if task_type not in TASK_TEMPLATES:
        return []
    for gid in goal_ids:
        for tpl in goals.plantillas(gid):
            queries.append({"goal": gid, "query": _render(tpl, parsed)})
    for tpl in TASK_TEMPLATES.get(task_type, []):
        queries.append({"goal": None, "query": _render(tpl, parsed)})
    # Deduplicar preservando orden.
    seen = set()
    out = []
    for q in queries:
        if q["query"] not in seen:
            seen.add(q["query"])
            out.append(q)
    return out
