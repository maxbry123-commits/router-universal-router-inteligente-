#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import urllib.parse
import urllib.request

SCHEMA = "yaiwes.router.search.huggingface/v1"
QUERY = os.getenv("QUERY", "").strip()
TOKEN = os.getenv("HF_TOKEN", "").strip()
LIMIT = int(os.getenv("HF_RESULTS_LIMIT", "5"))
TIMEOUT = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "8"))
UA = os.getenv("SEARCH_USER_AGENT", "YAIWES-ResearchPrepass/1.0")

def get(url: str):
    headers = {"User-Agent": UA}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    request = urllib.request.Request(url, headers=headers)
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

    for kind, endpoint, key in [
        ("model", "models", "modelId"),
        ("dataset", "datasets", "id"),
        ("space", "spaces", "id"),
    ]:
        try:
            url = "https://huggingface.co/api/" + endpoint + "?" + urllib.parse.urlencode({
                "search": QUERY,
                "limit": LIMIT
            })
            rows = get(url)
            for item in rows[:LIMIT]:
                ident = item.get(key) or item.get("id") or ""
                if not ident:
                    continue
                prefix = "datasets/" if kind == "dataset" else "spaces/" if kind == "space" else ""
                results.append({
                    "source": "huggingface",
                    "kind": kind,
                    "priority": 96,
                    "title": ident,
                    "url": "https://huggingface.co/" + prefix + ident,
                    "snippet": str(item.get("pipeline_tag") or item.get("sdk") or "")
                })
        except Exception as exc:
            errors.append({
                "kind": kind,
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
