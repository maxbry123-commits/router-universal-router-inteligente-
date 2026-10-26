"""Extractor exacto (sin LLM) para T07.

HTML/Markdown -> fragmentos por titulo/parrafo/bloque de codigo con
terminos coincidentes y ventanas de contexto.
"""
import re

_TAG_RE = re.compile(r"<[^>]+>")
_CODE_RE = re.compile(r"```(?:\w*)\n(.*?)```", re.DOTALL)
_HEAD_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def _limpiar_html(texto):
    texto = _TAG_RE.sub(" ", texto)
    return re.sub(r"[ \t]+", " ", texto)


def fragmentos(texto):
    """Divide el texto en fragmentos: titulos, parrafos y bloques de codigo."""
    if not texto:
        return []
    texto = _limpiar_html(texto)
    partes = []
    codigos = _CODE_RE.findall(texto)
    for c in codigos:
        partes.append(("code", c.strip()))
    sin_codigo = _CODE_RE.sub(" ", texto)
    for m in _HEAD_RE.finditer(sin_codigo):
        partes.append(("titulo", m.group(1).strip()))
    for parrafo in re.split(r"\n\s*\n", sin_codigo):
        p = re.sub(r"\s+", " ", parrafo).strip()
        if p and not p.startswith("#"):
            partes.append(("parrafo", p))
    return partes


def extraer(texto, terminos, ventana=200, max_fragmentos=10):
    """Extrae fragmentos que contienen los terminos, con ventana de contexto."""
    terminos = [t.lower() for t in terminos if t and len(t) > 2]
    if not terminos:
        terminos = [""]
    hallazgos = []
    for tipo, frag in fragmentos(texto):
        low = frag.lower()
        if any(t in low for t in terminos):
            idx = min((low.find(t) for t in terminos if t in low), default=0)
            ini = max(0, idx - ventana // 2)
            hallazgos.append({
                "tipo": tipo,
                "fragmento": frag[ini: ini + ventana].strip(),
                "terminos": [t for t in terminos if t in low],
            })
        if len(hallazgos) >= max_fragmentos:
            break
    return hallazgos


def extraer_de_resultados(resultados, terminos):
    """Aplica el extractor a snippets normalizados de los buscadores."""
    out = []
    for r in resultados:
        texto = (r.get("title", "") + "\n\n" + r.get("snippet", "")).strip()
        for h in extraer(texto, terminos):
            h["url"] = r.get("url", "")
            h["source"] = r.get("source", "")
            h["date"] = r.get("date", "")
            h["source_type"] = r.get("source_type", "")
            out.append(h)
    return out
