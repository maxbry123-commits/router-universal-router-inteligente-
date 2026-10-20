"""Parser determinista (sin LLM) para la Puerta de Evidencia T07.

Convierte un input en lenguaje natural a una estructura:
{task_type, targets, requirements, constraints, forbidden, verification}
"""
import re

TASK_TYPES = [
    "SEARCH", "INSTALL", "DOWNLOAD", "EXTRACT", "DEPLOY", "MODIFY_CODE",
    "DEBUG", "TEST", "COMPARE", "AUDIT", "RESEARCH", "VERIFY",
]

# Reglas: palabras clave (ES/EN) -> task_type. Orden importa: primera coincidencia gana.
_RULES = [
    (r"\b(instala|install|pip install|npm install|apt-get)\b", "INSTALL"),
    (r"\b(descarga|download|fetch|wget|curl)\b", "DOWNLOAD"),
    (r"\b(extrae|extract|descomprime|unzip|untar)\b", "EXTRACT"),
    (r"\b(despliega|deploy|publica|release|rollout)\b", "DEPLOY"),
    (r"\b(modifica|modify|cambia|change|edita|refactor|implementa)\b", "MODIFY_CODE"),
    (r"\b(depura|debug|falla|error|traceback|bug|fix|arregla)\b", "DEBUG"),
    (r"\b(test|prueba|pytest|unittest|coverage)\b", "TEST"),
    (r"\b(compara|compare|versus|vs\.?|diferencias)\b", "COMPARE"),
    (r"\b(audita|audit|revisa seguridad|vulnerab)\b", "AUDIT"),
    (r"\b(investiga|research|analiza|estudia)\b", "RESEARCH"),
    (r"\b(verifica|verify|comprueba|valida|check)\b", "VERIFY"),
    (r"\b(busca|search|encuentra|find|localiza)\b", "SEARCH"),
]

# Targets con estructura (rutas, dominios, URLs, nombres con punto).
_TARGET_RE = re.compile(r"[\w\-\./]+(?:\.[\w\-]+)+|[\w\-]+://[\w\-\./]+", re.UNICODE)
# Targets simples: sustantivo tras preposicion (de/en/sobre/para/del).
_NOUN_RE = re.compile(
    r"\b(?:de|del|en|sobre|para)\s+([A-Za-z][\w\-]{2,})(?![\w\-\./])",
    re.UNICODE)
# Palabras que no son entidades aunque sigan a una preposicion.
_STOPWORDS = {
    "la", "el", "los", "las", "un", "una", "que", "con", "sin", "por",
    "del", "al", "lo", "su", "sus", "este", "esta", "esto", "ese", "esa",
    "the", "a", "an", "this", "that", "it", "its",
}
_FORBIDDEN_RE = re.compile(r"(?:no|prohibido|nunca|sin|don't|do not|never)\s+([^.,;]+)", re.IGNORECASE)
_CONSTRAINT_RE = re.compile(r"(?:debe|must|tiene que|obligatorio|max(?:imo)?|min(?:imo)?)\s+([^.,;]+)", re.IGNORECASE)
_VERIFY_RE = re.compile(r"(?:verificar|comprobar|demostrar|aceptaci[oó]n|exit\s*0)\s*([^.,;]*)", re.IGNORECASE)


def _find_all(pattern, text):
    return [m.group(1).strip() for m in pattern.finditer(text) if m.group(1).strip()]


def _targets(text):
    encontrados = list(_TARGET_RE.findall(text))
    for m in _NOUN_RE.finditer(text):
        palabra = m.group(1)
        if palabra.lower() not in _STOPWORDS:
            encontrados.append(palabra)
    # Deduplicar preservando orden; descartar subcadenas de targets ya vistos.
    out = []
    for t in encontrados:
        if any(t == u or (t in u and "/" in u) for u in out):
            continue
        out.append(t)
    return out


def parse(text):
    """Parsea el input del usuario de forma determinista. Sin LLM."""
    text = (text or "").strip()
    low = text.lower()
    task_type = "SEARCH"
    for pattern, ttype in _RULES:
        if re.search(pattern, low):
            task_type = ttype
            break
    targets = _targets(text)
    requirements = _find_all(_CONSTRAINT_RE, text)
    constraints = list(requirements)
    forbidden = _find_all(_FORBIDDEN_RE, text)
    verification = _find_all(_VERIFY_RE, text)
    return {
        "task_type": task_type,
        "targets": targets,
        "requirements": requirements,
        "constraints": constraints,
        "forbidden": forbidden,
        "verification": verification,
        "raw": text,
    }


if __name__ == "__main__":
    import sys
    import json
    print(json.dumps(parse(" ".join(sys.argv[1:])), ensure_ascii=False, indent=2))
