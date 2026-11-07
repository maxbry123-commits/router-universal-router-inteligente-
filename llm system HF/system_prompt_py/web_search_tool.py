# web_search_tool.py
import json
from typing import List, Dict
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup

class WebSearchTool:
    """
    Motor de búsqueda determinista.
    No usa LLM. Devuelve contexto en Markdown con fuentes.
    """
    def __init__(self, max_results: int = 5, timeout: int = 10):
        self.max_results = max_results
        self.timeout = timeout

    def search(self, query: str) -> str:
        """Busca en DuckDuckGo y extrae el contenido de los resultados."""
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=self.max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
        except Exception as e:
            return f"[ERROR DE BÚSQUEDA: {e}]"

        if not results:
            return "[SIN RESULTADOS]"

        # Extraer contenido de las top 2 URLs
        enriched = []
        for r in results[:2]:
            content = self._fetch_content(r["url"])
            enriched.append({
                "title": r["title"],
                "url": r["url"],
                "content": content[:1500]  # Limitar a 1500 chars por fuente
            })

        return self._format_markdown(enriched)

    def _fetch_content(self, url: str) -> str:
        """Descarga y limpia el texto de una URL."""
        try:
            resp = requests.get(url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return "\n".join([line for line in text.splitlines() if line.strip()])
        except Exception:
            return "[CONTENIDO NO DISPONIBLE]"

    def _format_markdown(self, results: List[Dict]) -> str:
        """Formatea los resultados como Markdown con citas."""
        md = "### CONTEXTO DE INVESTIGACIÓN (GAP RESOLUTION)\n\n"
        for i, r in enumerate(results, 1):
            md += f"**[Fuente {i}]** {r['title']}\n"
            md += f"URL: {r['url']}\n"
            md += f"{r['content']}\n\n---\n\n"
        return md
