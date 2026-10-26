#!/usr/bin/env python3
from __future__ import annotations
import html
import json
import os
import pathlib
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SCHEMA = "yaiwes.router.search.web-domains/v1"
QUERY = os.getenv("QUERY", "").strip()
SOURCES_FILE = pathlib.Path(os.getenv("SOURCES_FILE", "sources.json"))
MAX_RESULTS = int(os.getenv("MAX_RESULTS_PER_SOURCE", "3"))
TIMEOUT = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "8"))
UA = os.getenv("SEARCH_USER_AGENT", "YAIWES-ResearchPrepass/1.0")

class DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.capture_title = False
        self.capture_snippet = False
        self.title = []
        self.snippet = []
        self.url = ""

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        cls = data.get("class", "")
        if tag == "a" and "result__a" in cls:
            self.capture_title = True
            self.title = []
            self.snippet = []
            self.url = data.get("href", "")
        elif tag in {"a", "div"} and "result__snippet" in cls:
            self.capture_snippet = True

    def handle_endtag(self, tag):
        if tag == "a" and self.capture_title:
            self.capture_title = False
            self.results.append({
                "title": " ".join("".join(self.title).split()),
                "url": self.url,
                "snippet": ""
            })
        if tag in {"a", "div"} and self.capture_snippet:
            self.capture_snippet = False
            if self.results and self.snippet:
                self.results[-1]["snippet"] = " ".join("".join(self.snippet).split())

    def handle_data(self, data):
        if self.capture_title:
            self.title.append(data)
        if self.capture_snippet:
            self.snippet.append(data)

def unwrap_ddg(url: str) -> str:
    url = html.unescape(url)
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return query["uddg"][0]
    if url.startswith("//"):
        return "https:" + url
    return url

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read(2_000_000).decode("utf-8", "replace")

def main():
    if not QUERY:
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "QUERY required"
        }))
    cfg = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    results = []
    errors = []

    for source in cfg.get("sources", []):
        if source.get("kind") != "web":
            continue
        site = source["site_query"]
        source_query = f"site:{site} {QUERY}"
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": source_query})
        try:
            parser = DDGParser()
            parser.feed(fetch(url))
            seen = set()
            count = 0
            for row in parser.results:
                target = unwrap_ddg(row.get("url", ""))
                if not target.startswith(("http://", "https://")) or target in seen:
                    continue
                seen.add(target)
                results.append({
                    "source": source["id"],
                    "kind": "web",
                    "priority": int(source.get("priority", 50)),
                    "query": source_query,
                    "title": row.get("title", ""),
                    "url": target,
                    "snippet": row.get("snippet", "")
                })
                count += 1
                if count >= MAX_RESULTS:
                    break
        except Exception as exc:
            errors.append({
                "source": source["id"],
                "error": type(exc).__name__ + ":" + str(exc)[:300]
            })

    print(json.dumps({
        "schema": SCHEMA,
        "query": QUERY,
        "results": results,
        "errors": errors,
        "verdict": "SEARCH_DONE" if results else "NO_RESULTS"
    }, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
