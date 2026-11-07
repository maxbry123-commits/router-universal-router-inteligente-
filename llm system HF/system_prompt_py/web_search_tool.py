# web_search_tool.py
import httpx
from bs4 import BeautifulSoup

class AsyncWebSearchTool:
    def __init__(self, max_results: int = 5, timeout: int = 10):
        self.max_results = max_results
        self.timeout = timeout

    async def search(self, query: str) -> str:
        from ddgs import DDGS
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

        enriched = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for r in results[:2]:
                try:
                    resp = await client.get(r["url"], headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                    content = "\n".join([line for line in text.splitlines() if line.strip()])
                    enriched.append({"title": r["title"], "url": r["url"], "content": content[:1500]})
                except Exception:
                    enriched.append({"title": r["title"], "url": r["url"], "content": "[CONTENIDO NO DISPONIBLE]"})

        md = "### CONTEXTO DE INVESTIGACIÓN (GAP RESOLUTION)\n\n"
        for i, r in enumerate(enriched, 1):
            md += f"**[Fuente {i}]** {r['title']}\nURL: {r['url']}\n{r['content']}\n\n---\n\n"
        return md
