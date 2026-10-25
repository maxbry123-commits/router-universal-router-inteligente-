#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import urllib.parse
import urllib.request

SCHEMA = "yaiwes.router.search.github/v1"
QUERY = os.getenv("QUERY", "").strip()
TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
LIMIT = int(os.getenv("GITHUB_RESULTS_LIMIT", "5"))
TIMEOUT = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "8"))
UA = os.getenv("SEARCH_USER_AGENT", "YAIWES-ResearchPrepass/1.0")

def api(path: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    if not QUERY:
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "QUERY required"
        }))

    results = []
    errors = []

    try:
        query = urllib.parse.quote_plus(QUERY)
        data = api(f"/search/repositories?q={query}&sort=stars&order=desc&per_page={LIMIT}")
        for item in data.get("items", [])[:LIMIT]:
            results.append({
                "source": "github",
                "kind": "repository",
                "priority": 100,
                "title": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "snippet": item.get("description") or "",
                "stars": item.get("stargazers_count", 0)
            })
    except Exception as exc:
        errors.append({
            "kind": "repositories",
            "error": type(exc).__name__ + ":" + str(exc)[:300]
        })

    try:
        query = urllib.parse.quote_plus(QUERY + " is:issue")
        data = api(f"/search/issues?q={query}&sort=updated&order=desc&per_page={LIMIT}")
        for item in data.get("items", [])[:LIMIT]:
            results.append({
                "source": "github",
                "kind": "issue",
                "priority": 98,
                "title": item.get("title", ""),
                "url": item.get("html_url", ""),
                "snippet": (item.get("body") or "")[:800]
            })
    except Exception as exc:
        errors.append({
            "kind": "issues",
            "error": type(exc).__name__ + ":" + str(exc)[:300]
        })

    if TOKEN:
        try:
            query = urllib.parse.quote_plus(QUERY)
            data = api(f"/search/code?q={query}&per_page={LIMIT}")
            for item in data.get("items", [])[:LIMIT]:
                results.append({
                    "source": "github",
                    "kind": "code",
                    "priority": 100,
                    "title": item.get("name", ""),
                    "url": item.get("html_url", ""),
                    "snippet": item.get("path", "")
                })
        except Exception as exc:
            errors.append({
                "kind": "code",
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
