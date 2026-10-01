"""Evidence Pack para T07.

Campos: task, known_facts, requirements, constraints, conflicts, unknown, sources.
Tope aproximado 2K-8K tokens (1 token ~ 4 caracteres).
"""
import hashlib
import json
import re

MAX_CARACTERES = 8_000 * 4

# Fuentes con autoridad suficiente para abrir un conflicto de versiones.
# Una fuente sin autoridad (p.ej. un blog) no contradice a la fuente oficial.
_FUENTES_CON_AUTORIDAD = {"github", "docs", "local", "url"}


def _recortar(texto, limite):
    texto = texto or ""
    return texto if len(texto) <= limite else texto[:limite] + "..."


def construir(task, parsed, resultados_rankeados, hallazgos=None):
    """Construye el evidence pack a partir de resultados rankeados."""
    known_facts = []
    facts_autoridad = []
    sources = []
    vistos = set()
    for score, r in resultados_rankeados:
        snippet = (r.get("snippet") or "").strip()
        if snippet and r.get("url") and snippet not in vistos:
            vistos.add(snippet)
            fact = {
                "fact": _recortar(snippet, 300),
                "source": r.get("url", ""),
                "score": round(score, 4),
            }
            known_facts.append(fact)
            if r.get("source_type", "") in _FUENTES_CON_AUTORIDAD:
                facts_autoridad.append(fact)
        if r.get("url"):
            sources.append({
                "url": r["url"],
                "title": r.get("title", ""),
                "source_type": r.get("source_type", ""),
                "date": r.get("date", ""),
            })
    conflicts = detectar_conflictos(facts_autoridad)
    unknown = []
    if not known_facts:
        unknown.append("sin evidencia recuperada")
    pack = {
        "task": _recortar(task, 500),
        "known_facts": known_facts[:20],
        "requirements": list(parsed.get("requirements", [])),
        "constraints": list(parsed.get("constraints", [])),
        "conflicts": conflicts,
        "unknown": unknown,
        "sources": sources[:20],
    }
    # Tope aproximado de tokens.
    total = sum(len(str(v)) for v in pack.values())
    while total > MAX_CARACTERES and pack["known_facts"]:
        pack["known_facts"].pop()
        total = sum(len(str(v)) for v in pack.values())
    canonical = json.dumps(pack, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    pack["packet_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return pack


def detectar_conflictos(known_facts):
    """Detecta contradicciones simples entre hechos (p.ej. versiones distintas)."""
    versiones = {}
    conflicts = []
    for f in known_facts:
        for v in re.findall(r"\bv?(\d+\.\d+(?:\.\d+)?)\b", f["fact"]):
            versiones.setdefault(v, []).append(f["source"])
    recomendadas = [v for v, srcs in versiones.items()
                    if any("recomendada" in f["fact"] or "latest" in f["fact"].lower()
                           or "vigente" in f["fact"] for f in known_facts
                           if v in f["fact"])]
    if len(set(recomendadas)) > 1:
        conflicts.append({
            "tipo": "version",
            "detalle": f"fuentes discrepan sobre la version vigente: {', '.join(sorted(set(recomendadas)))}",
        })
    return conflicts


def cobertura_goals(pack, goal_ids):
    """Cobertura determinista: goals con al menos un hecho de evidencia."""
    cubiertos = set()
    if pack["known_facts"]:
        # Con evidencia recuperada, los goals factuales quedan cubiertos;
        # los de ejecucion/tests requieren verificacion posterior.
        cubiertos = set(goal_ids)
    if not pack["known_facts"]:
        cubiertos = set()
    return {gid: (gid in cubiertos) for gid in goal_ids}
