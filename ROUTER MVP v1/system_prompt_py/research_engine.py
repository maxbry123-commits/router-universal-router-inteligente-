import re
from urllib.parse import urlsplit
from loc_limits import MAX_PACK_CHARS

TRUSTED = frozenset({
    "github.com", "huggingface.co", "stackoverflow.com", "docs.python.org",
    "developer.mozilla.org", "fastapi.tiangolo.com", "docs.pytest.org",
    "pypi.org", "owasp.org", "sqlite.org",
})
SCORE_MIN = 0.2
TOP_K = 3
MAX_CANDIDATES = 8
STOPWORDS = frozenset({
    "the", "and", "for", "with", "que", "los", "las", "del", "una", "con", "para", "por", "como", "este", "esta",
})

def tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9_áéíóúñ]{3,}", text.lower()) if w not in STOPWORDS}

def trusted(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in TRUSTED)

def score(query: str, title: str, snippet: str, content: str) -> float:
    q = tokens(query)
    if not q:
        return 0.0
    d = tokens(f"{title} {snippet} {content}")
    return round(len(q & d) / len(q), 3)

def variants(query: str) -> list:
    base = query.strip()
    words = [w for w in re.findall(r"\w+", base) if len(w) > 3][:6]
    out = [base]
    short = " ".join(words)
    if short and short != base:
        out.append(short)
    return out

def build_pack(query: str, docs: list) -> str:
    parts = [f"CONSULTA: {query}"]
    for i, d in enumerate(docs, 1):
        parts.append(f"[Fuente {i}] {d['title']} | {d['url']} | score={d['score']}\n{d['content'][:1000]}")
    return "\n\n".join(parts)[:MAX_PACK_CHARS]

class ResearchEngine:
    def __init__(self, search_fn, fetch_fn):
        self.search_fn = search_fn
        self.fetch_fn = fetch_fn

    async def run(self, query: str, seen_urls: set) -> dict:
        last = "NO_RESULTS"
        for q in variants(query):
            results = await self.search_fn(q)
            if not results:
                last = "NO_RESULTS"
                continue
            fresh = [r for r in results if trusted(r.get("url", "")) and r.get("url") not in seen_urls]
            if not fresh:
                last = "NO_NEW_TRUSTED"
                continue
            docs = []
            for r in fresh[:MAX_CANDIDATES]:
                content = await self.fetch_fn(r["url"])
                s = score(q, r.get("title", ""), r.get("snippet", ""), content)
                docs.append({**r, "content": content, "score": s})
            docs.sort(key=lambda d: d["score"], reverse=True)
            top = [d for d in docs[:TOP_K] if d["score"] >= SCORE_MIN]
            if not top:
                last = "NO_SCORE"
                continue
            return {"status": "OK", "query": q, "pack": build_pack(q, top), "sources": [d["url"] for d in top]}
        return {"status": last, "query": query, "pack": "", "sources": []}
