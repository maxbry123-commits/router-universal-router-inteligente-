"""grammar.py · N4-C · GUÍA VIVA — MOTOR GRAMATICAL DETERMINISTA.

Descompone una ACCIÓN (texto libre en español o inglés) en la tripla
{sujeto, verbo, adjetivo} más el contexto de la descomposición:

    {
      "objetivo": "<texto de la acción normalizado>",
      "sujeto":   "<cabecera de la frase sobre la que se actúa>",
      "verbo":    "<verbo canónico en inglés>",
      "adjetivo": "<calificador final (preposición + cola)>",
      "estado":   "DECOMPUESTA | PARCIAL | AMBIGUA",
      "tipo":     "CREACION | ELIMINACION | REFACTOR | VALIDACION | ..."
    }

REGLAS DURAS
  · SOLO stdlib. SIN LLM. SIN red. SIN I/O. Determinista: misma entrada → misma salida.
  · El verbo se normaliza a un identificador canónico estable (create, remove, ...);
    la forma en superficie (añadir, add, ...) queda en el lexicón documentado en README.md.
  · `estado` describe el resultado de la DESCOMPOSICIÓN, no el estado de la guía
    (el estado frente a la guía lo decide match.py: DEFINIDA/NECESARIA/PARCIAL/NO_APLICA).
  · `tipo` se deriva del verbo canónico.

Uso:
    from grammar import decompose
    decompose("añadir reintento con backoff")
    decompose("extract function to module")
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "yaiwes.guide.grammar.v1"

# --------------------------------------------------------------------------
# 1 · LEXICÓN DE VERBOS (canónico -> formas en superficie ES/EN)
#    Se ordenan por longitud descendente al compilar el patrón, para que
#    "añadir" gane a "add" y "validar" a "valida".
# --------------------------------------------------------------------------
VERB_LEXICON: dict[str, tuple[str, ...]] = {
    "create": (
        "create", "creates", "creating", "created",
        "add", "adds", "adding", "added",
        "implement", "implements", "implementing",
        "crear", "crea", "creando", "creado", "creacion",
        "anadir", "añadir", "añade", "añadiendo", "anadido",
        "agregar", "agrega", "agregando",
        "nuevo", "nueva", "new",
    ),
    "remove": (
        "remove", "removes", "removing", "removed",
        "delete", "deletes", "deleting", "deleted",
        "drop", "drops", "dropping",
        "eliminar", "elimina", "eliminado", "eliminacion",
        "borrar", "borra", "quitar", "quita",
        "purge", "purgar", "limpiar", "limpia",
    ),
    "refactor": (
        "refactor", "refactors", "refactoring",
        "refactorize", "refactorizar", "refactoriza",
        "extract", "extracts", "extracting", "extracted",
        "restructure", "reestructurar",
        "split", "splits", "dividir", "separa", "separar",
        "extraer", "extrae", "extraido",
    ),
    "validate": (
        "validate", "validates", "validating", "validation",
        "verify", "verifies", "verifying", "verification",
        "check", "checks", "checking",
        "ensure", "ensures", "ensure_",
        "validar", "valida", "validando", "validacion",
        "verificar", "verifica", "comprobar", "comprueba",
        "asegurar", "asegura",
    ),
    "convert": (
        "convert", "converts", "converting", "conversion",
        "transform", "transforms", "transforming",
        "map", "maps", "mapping",
        "convertir", "convierte", "convertido", "conversion",
        "transformar", "transforma", "mapear", "mapea",
    ),
    "render": (
        "render", "renders", "rendering",
        "renderizar", "renderiza", "renderizacion",
        "paint", "paints", "pintar", "dibuja", "draw", "draws",
    ),
    "audit": (
        "audit", "audits", "auditing",
        "auditar", "audita", "auditoria",
        "revisar", "revisa", "revision", "review", "reviews",
        "inspect", "inspects", "inspeccionar", "inspecciona",
    ),
    "deploy": (
        "deploy", "deploys", "deploying", "deployment",
        "deployar", "desplegar", "despliega", "despliegue",
        "publish", "publishes", "publishing", "publicar", "publica",
        "release", "releases", "releasear", "liberar",
    ),
    "test": (
        "test", "tests", "testing", "testear",
        "probar", "prueba", "pruebas",
    ),
    "document": (
        "document", "documents", "documenting",
        "documentar", "documenta", "documentacion",
        "docstring", "readme",
    ),
    "rotate": (
        "rotate", "rotates", "rotating", "rotation",
        "rotar", "rota", "rotacion",
        "refresh", "refreshes", "renovar", "renueva", "renew", "renews",
        "revocar", "revoca", "revoke", "revokes",
    ),
}

VERB_TYPE: dict[str, str] = {
    "create": "CREACION",
    "remove": "ELIMINACION",
    "refactor": "REFACTOR",
    "validate": "VALIDACION",
    "convert": "CONVERSION",
    "render": "RENDER",
    "audit": "AUDITORIA",
    "deploy": "DEPLOY",
    "test": "TEST",
    "document": "DOCS",
    "rotate": "SEGURIDAD",
}

# --------------------------------------------------------------------------
# 2 · CALIFICADORES
# --------------------------------------------------------------------------
PREPOSITIONS: tuple[str, ...] = (
    "con", "de", "del", "a", "al", "para", "hacia", "en", "sobre",
    "with", "to", "for", "into", "in", "on", "under",
)

ADJECTIVES: frozenset[str] = frozenset({
    "idempotente", "atomico", "atómico", "asincrono", "asíncrono",
    "sincrono", "síncrono", "seguro", "segura", "rapido", "rápido", "lento",
    "resiliente", "idempotent", "atomic", "async", "sync", "safe", "fast",
    "slow", "resilient", "determinista", "deterministic", "configurable",
    "escalable", "robusto", "robust", "tolerante", "backoff", "exponencial",
    "exponential", "limitado", "limited", "auditable", "observable",
    "thread-safe", "threadsafe", "restringido", "restricted",
})

LEADING_ARTICLES: frozenset[str] = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas", "the", "a", "an",
})

# Prefijos que se pueden retirar antes de buscar el verbo.
STRIP_PREFIXES: tuple[str, ...] = (
    "necesita", "necesitamos", "se debe", "debe", "deben", "hay que",
    "we need to", "need to", "needs to", "please", "por favor",
    "quiero", "want", "wants to", "vamos a", "let's",
)

_TOKEN_RE = re.compile(r"[^\W_]+(?:[._-][^\W_]+)*", re.UNICODE)


def _compile_verb_pattern() -> re.Pattern[str]:
    forms: list[str] = []
    for surfaces in VERB_LEXICON.values():
        forms.extend(surfaces)
    # Orden por longitud descendente: la forma más larga gana ("refactorizar" > "refactor").
    forms.sort(key=lambda s: (-len(s), s))
    body = "|".join(re.escape(f) for f in forms)
    return re.compile(r"(?<!\w)(" + body + r")(?!\w)", re.IGNORECASE | re.UNICODE)


_VERB_RE = _compile_verb_pattern()
_SURFACE_TO_CANON: dict[str, str] = {}
for _canon, _surfaces in VERB_LEXICON.items():
    for _s in _surfaces:
        _SURFACE_TO_CANON.setdefault(_s.lower(), _canon)


def normalize_text(text: str) -> str:
    """Colapsa espacios, recorta y unifica saltos de línea. Determinista."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def _strip_prefix(text: str) -> tuple[str, str]:
    """Retira prefijos de intención ('necesita', 'please', ...). Devuelve (resto, prefijo)."""
    low = text.lower()
    for pre in STRIP_PREFIXES:
        if low.startswith(pre + " "):
            return text[len(pre) + 1:].strip(), pre
    return text, ""


def _find_verb(text: str) -> tuple[str | None, str | None, int]:
    """Devuelve (verbo_canonico, forma_superficie, indice) o (None, None, -1)."""
    if not text:
        return None, None, -1
    match = _VERB_RE.search(text)
    if not match:
        return None, None, -1
    surface = match.group(1)
    canon = _SURFACE_TO_CANON.get(surface.lower())
    if canon is None:
        # La forma pudo venir acentuada de otra manera: se busca por raíz sin acentos.
        canon = _SURFACE_TO_CANON.get(_deaccent(surface).lower())
    return canon, surface, match.start()


def _deaccent(text: str) -> str:
    import unicodedata

    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _split_qualifier(remainder: str) -> tuple[str, str]:
    """Separa (sujeto, adjetivo) del resto de la acción.

    Regla: se busca la PREPOSICIÓN más cercana al final cuyo COLA tenga 1..3 tokens
    (si no hay, 1..5 tokens). La cola completa (preposición + cola) es el ADJETIVO;
    lo que queda antes es el SUJETO (sin artículos iniciales).
    """
    remainder = remainder.strip(" .,:;")
    if not remainder:
        return "", ""
    tokens = remainder.split()
    best_primary: tuple[int, int] | None = None  # (indice_prep, tokens_cola)
    best_secondary: tuple[int, int] | None = None
    for idx, tok in enumerate(tokens[:-1]):
        if tok.lower().strip(".,;:") not in PREPOSITIONS:
            continue
        tail = len(tokens) - idx - 1
        if 1 <= tail <= 3:
            if best_primary is None:
                best_primary = (idx, tail)
        elif 1 <= tail <= 5:
            if best_secondary is None:
                best_secondary = (idx, tail)
    chosen = best_primary or best_secondary
    if chosen is None:
        # Sin preposición: si la última palabra es un adjetivo conocido, se extrae.
        toks = tokens
        if len(toks) >= 2 and toks[-1].lower() in ADJECTIVES:
            return " ".join(toks[:-1]), toks[-1]
        return " ".join(toks), ""
    idx, _tail = chosen
    subject_tokens = tokens[:idx]
    qualifier_tokens = tokens[idx:]
    while subject_tokens and subject_tokens[0].lower() in LEADING_ARTICLES and len(subject_tokens) > 1:
        subject_tokens.pop(0)
    subject = " ".join(subject_tokens).strip(" .,:;")
    qualifier = " ".join(qualifier_tokens).strip(" .,:;")
    return subject, qualifier


def decompose(text: str) -> dict[str, Any]:
    """Descomposición gramatical determinista de una acción.

    Devuelve EXACTAMENTE las 6 claves del contrato:
    objetivo, sujeto, verbo, adjetivo, estado, tipo.
    """
    original = normalize_text(text)
    objetivo = original[:240]
    work, _prefix = _strip_prefix(original)

    canon, surface, _pos = _find_verb(work)

    remainder = work
    if surface:
        low = work.lower()
        pos = low.find(surface.lower())
        if pos >= 0:
            remainder = (work[:pos] + " " + work[pos + len(surface):]).strip()

    subject, qualifier = _split_qualifier(remainder)

    if canon is None:
        estado = "AMBIGUA"
    elif not subject:
        estado = "PARCIAL"
    else:
        estado = "DECOMPUESTA"

    tipo = VERB_TYPE.get(canon, "OTRO") if canon else "OTRO"

    return {
        "objetivo": objetivo,
        "sujeto": subject,
        "verbo": canon or "",
        "adjetivo": qualifier,
        "estado": estado,
        "tipo": tipo,
    }


def decompose_verbose(text: str) -> dict[str, Any]:
    """Igual que decompose() + metadatos internos (forma en superficie, preposición)."""
    out = decompose(text)
    work, prefix = _strip_prefix(normalize_text(text))
    canon, surface, pos = _find_verb(work)
    remainder = work
    if surface:
        low = work.lower()
        p = low.find(surface.lower())
        if p >= 0:
            remainder = (work[:p] + " " + work[p + len(surface):]).strip()
    out.update(
        verbo_canonico=canon or "",
        verbo_superficie=surface or "",
        prefijo_intencion=prefix,
        resto=remainder,
        tokens=_tokens(work),
    )
    return out


def lexicon() -> dict[str, Any]:
    """Expone el lexicón (documentación viva del motor)."""
    return {
        "schema": SCHEMA,
        "verbos": {k: list(v) for k, v in VERB_LEXICON.items()},
        "tipos": dict(VERB_TYPE),
        "preposiciones": list(PREPOSITIONS),
        "adjetivos": sorted(ADJECTIVES),
    }


__all__ = [
    "SCHEMA",
    "VERB_LEXICON",
    "VERB_TYPE",
    "decompose",
    "decompose_verbose",
    "lexicon",
    "normalize_text",
]
