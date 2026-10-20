"""Buscadores (fan-out) para T07.

Motores:
- GitHub Search API (token por env GITHUB_TOKEN; nunca en codigo).
- Documentacion por URL (urllib).
- Busqueda local en el repo.
- Modo SIMULADO=1: sin red, fuentes deterministas.

Resultados normalizados:
{query, source, url, title, date, snippet, source_type, retrieved_at}
"""
import os
import re
import json
import datetime
import urllib.request
import urllib.parse

SIMULADO = os.environ.get("SIMULADO", "") == "1"

# Corpus simulado determinista: sin red, reproducible.
_CORPUS_SIMULADO = [
    {
        "source": "simulado/github",
        "url": "https://github.com/ejemplo/proyecto/releases",
        "title": "Releases - proyecto v2.3.1",
        "date": "2026-08-15",
        "snippet": "Latest release v2.3.1. Changelog: fix deploy, tests pass, exit 0.",
        "source_type": "github",
    },
    {
        "source": "simulado/docs",
        "url": "https://docs.ejemplo.dev/proyecto",
        "title": "Documentacion oficial del proyecto",
        "date": "2026-07-01",
        "snippet": "Guia oficial: instalacion, configuracion, integracion y ejecucion. "
                   "Version vigente 2.3.1. Tests con pytest.",
        "source_type": "docs",
    },
    {
        "source": "simulado/local",
        "url": "repo://README.md",
        "title": "README local del repo",
        "date": "2026-09-01",
        "snippet": "Uso: python -m pytest -q. Aceptacion exit 0. Prohibido escribir fuera del alcance.",
        "source_type": "local",
    },
    {
        "source": "simulado/blog",
        "url": "https://blog.ejemplo.dev/nota",
        "title": "Nota de comunidad (no oficial)",
        "date": "2024-01-10",
        "snippet": "La version 1.0 es la recomendada segun este blog antiguo.",
        "source_type": "blog",
    },
]


def _ahora():
    ahora = datetime.datetime.now(datetime.timezone.utc)
    return ahora.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalizar(query, item):
    return {
        "query": query,
        "source": item.get("source", ""),
        "url": item.get("url", ""),
        "title": item.get("title", ""),
        "date": item.get("date", ""),
        "snippet": item.get("snippet", ""),
        "source_type": item.get("source_type", ""),
        "retrieved_at": _ahora(),
    }


def buscar_simulado(query):
    """Busqueda determinista sin red: filtra el corpus por terminos."""
    terminos = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 3]
    resultados = []
    for item in _CORPUS_SIMULADO:
        texto = (item["title"] + " " + item["snippet"]).lower()
        if not terminos or any(t in texto for t in terminos):
            resultados.append(_normalizar(query, item))
    if not resultados:
        # Siempre devolver al menos la fuente oficial simulada para cobertura.
        resultados.append(_normalizar(query, _CORPUS_SIMULADO[1]))
    return resultados


def buscar_github(query, token=None):
    """GitHub Search API. Requiere red; token por env GITHUB_TOKEN."""
    if SIMULADO:
        return buscar_simulado(query)
    token = token or os.environ.get("GITHUB_TOKEN")
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    out = []
    for it in data.get("items", [])[:5]:
        out.append(_normalizar(query, {
            "source": "github",
            "url": it.get("html_url", ""),
            "title": it.get("full_name", ""),
            "date": it.get("updated_at", "")[:10],
            "snippet": it.get("description") or "",
            "source_type": "github",
        }))
    return out


def buscar_url(query, url):
    """Descarga una URL de documentacion con urllib. Requiere red."""
    if SIMULADO:
        return buscar_simulado(query)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            cuerpo = resp.read(200_000).decode("utf-8", "replace")
    except Exception:
        return []
    texto = re.sub(r"<[^>]+>", " ", cuerpo)
    texto = re.sub(r"\s+", " ", texto).strip()
    return [_normalizar(query, {
        "source": "url",
        "url": url,
        "title": url,
        "date": "",
        "snippet": texto[:500],
        "source_type": "docs",
    })]


def buscar_local(query, raiz="."):
    """Busqueda local en archivos de texto del repo."""
    terminos = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 3]
    if not terminos:
        return []
    out = []
    for dirpath, _dirs, files in os.walk(raiz):
        if ".git" in dirpath:
            continue
        for fn in files:
            if not fn.endswith((".md", ".py", ".txt")):
                continue
            ruta = os.path.join(dirpath, fn)
            try:
                with open(ruta, "r", encoding="utf-8", errors="replace") as f:
                    contenido = f.read(50_000)
            except OSError:
                continue
            low = contenido.lower()
            if any(t in low for t in terminos):
                idx = min(low.find(t) for t in terminos if t in low)
                snippet = contenido[max(0, idx - 80): idx + 200].replace("\n", " ")
                out.append(_normalizar(query, {
                    "source": "local",
                    "url": "repo://" + ruta,
                    "title": ruta,
                    "date": "",
                    "snippet": snippet,
                    "source_type": "local",
                }))
            if len(out) >= 5:
                return out
    return out


def fanout(queries, raiz="."):
    """Ejecuta el fan-out sobre la lista de consultas compiladas."""
    resultados = []
    for q in queries:
        query = q["query"] if isinstance(q, dict) else q
        if SIMULADO:
            resultados.extend(buscar_simulado(query))
        else:
            resultados.extend(buscar_github(query))
            resultados.extend(buscar_local(query, raiz))
    return resultados
