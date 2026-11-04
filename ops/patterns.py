# ops/patterns.py — catalogo UNICO de patrones de cableado (ROADMAP U1: unifica 6 vs 5).
# Fuente canonica: los 6 patrones del JOB 1 de la guia "organizacion de la raiz del repo"
# (ops/historical_wiring_audit.py L82-89). Los 5 del connectivity_job.py se mapean aqui.
import re
PATTERNS={
 "http":     r"https?://|fetch\(|axios|requests\.|httpx|aiohttp",
 "mcp":      r"\bMCP\b|tools/list|tools/call|streamable|stdio",
 "endpoints":r"BASE_URL|API_URL|ENDPOINT|SERVICE_URL|/api/",
 "agents":   r"agent|orchestrator|specialist|handoff",
 "engines":  r"hermes|deepseek|engine|provider",
 "imports":  r"^\s*(import |from |require\()",
}
COMPILED={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
LEGACY_ALIASES={"environment":"endpoints","network":"http"}
def categories(text):
    out=[]
    for k,rx in COMPILED.items():
        if rx.search(text):out.append(k)
    return out
def scan_texts(items):
    hits={k:[] for k in PATTERNS}
    for path,text in items:
        for k,rx in COMPILED.items():
            if rx.search(text):hits[k].append(path)
    return hits
