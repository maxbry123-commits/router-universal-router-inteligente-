"""Ranking determinista (sin LLM) para T07.

BM25 propio (stdlib) + autoridad de fuente + recencia + coincidencia exacta +
corroboracion - duplicado - penalizacion por antiguedad.
Fusion de motores con Reciprocal Rank Fusion (RRF).
"""
import math
import re
from collections import Counter

_AUTORIDAD = {
    "github": 1.0,
    "docs": 0.9,
    "local": 0.7,
    "url": 0.8,
    "blog": 0.3,
}


def _tokens(texto):
    return re.findall(r"\w+", (texto or "").lower())


def bm25_scores(documentos, consulta, k1=1.5, b=0.75):
    """BM25 implementado con stdlib. documentos: lista de textos."""
    docs_tokens = [_tokens(d) for d in documentos]
    n = len(docs_tokens)
    if n == 0:
        return []
    avgdl = sum(len(d) for d in docs_tokens) / n or 1.0
    df = Counter()
    for dt in docs_tokens:
        for term in set(dt):
            df[term] += 1
    q_terms = _tokens(consulta)
    scores = []
    for dt in docs_tokens:
        tf = Counter(dt)
        dl = len(dt) or 1
        score = 0.0
        for term in q_terms:
            if term not in df:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            f = tf.get(term, 0)
            score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        scores.append(score)
    return scores


def _recencia(fecha, anio_ref=2026):
    try:
        anio = int(str(fecha)[:4])
    except (ValueError, TypeError):
        return 0.3
    edad = max(0, anio_ref - anio)
    return max(0.0, 1.0 - 0.2 * edad)


def puntuar(resultados, consulta):
    """Score compuesto por resultado. Devuelve lista [(score, resultado)]."""
    textos = [(r.get("title", "") + " " + r.get("snippet", "")) for r in resultados]
    bm = bm25_scores(textos, consulta)
    q_terms = set(_tokens(consulta))
    vistos = {}
    salida = []
    for r, texto, s_bm in zip(resultados, textos, bm):
        t_terms = set(_tokens(texto))
        exact = 1.0 if q_terms and q_terms <= t_terms else 0.0
        autoridad = _AUTORIDAD.get(r.get("source_type", ""), 0.4)
        rec = _recencia(r.get("date", ""))
        clave = re.sub(r"\W+", "", texto.lower())[:80]
        duplicado = 1.0 if clave in vistos else 0.0
        vistos[clave] = True
        stale = 1.0 - rec
        score = (2.0 * exact + s_bm + 1.5 * autoridad + 1.0 * rec
                 - 1.0 * duplicado - 0.5 * stale)
        salida.append((score, r))
    salida.sort(key=lambda x: x[0], reverse=True)
    return salida


def corroboracion(resultados):
    """Cuenta cuantas fuentes distintas respaldan terminos compartidos."""
    por_fuente = {}
    for r in resultados:
        por_fuente.setdefault(r.get("source_type", "?"), set()).update(
            _tokens(r.get("snippet", "")))
    comunes = None
    for terms in por_fuente.values():
        comunes = terms if comunes is None else (comunes & terms)
    return len(comunes or set())


def rrf(rankings, k=60):
    """Reciprocal Rank Fusion: fusiona varias listas rankeadas de URLs.

    rankings: lista de listas de resultados (dicts con 'url') ya ordenadas.
    """
    puntos = {}
    items = {}
    for ranking in rankings:
        for pos, r in enumerate(ranking):
            clave = r.get("url") or r.get("title", "")
            puntos[clave] = puntos.get(clave, 0.0) + 1.0 / (k + pos + 1)
            items[clave] = r
    fusion = sorted(puntos.items(), key=lambda x: x[1], reverse=True)
    return [(score, items[clave]) for clave, score in fusion]


def rankear(resultados, consulta, top=10):
    """Pipeline completo: puntua y devuelve los mejores resultados."""
    return puntuar(resultados, consulta)[:top]
