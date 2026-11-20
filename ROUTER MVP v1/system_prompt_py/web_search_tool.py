import asyncio
import re
import httpx

FETCH_TIMEOUT = 10.0
SEARCH_TIMEOUT = 15.0
MAX_BYTES = 300_000
MAX_TEXT = 4000

def _ddg_sync(query: str, max_results: int) -> list:
    from ddgs import DDGS
    with DDGS() as ddgs:
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in ddgs.text(query, max_results=max_results)
        ]

async def search(query: str, max_results: int = 8) -> list:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_ddg_sync, query, max_results), timeout=SEARCH_TIMEOUT)
    except Exception:
        return []

def _clean(html: str) -> str:
    text = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_TEXT]

async def fetch_text(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = await client.get(url)
            r.raise_for_status()
            raw = r.text[:MAX_BYTES]
    except Exception:
        return ""
    return _clean(raw)
