#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse

SCHEMA = "yaiwes.router.context-packet/v1"
HERE = pathlib.Path(__file__).resolve().parent
INPUT_BLOCK_FILE = pathlib.Path(os.getenv("INPUT_BLOCK_FILE", "INPUT_BLOCK.txt"))
OUTPUT_JSON = pathlib.Path(os.getenv("CONTEXT_PACKET_JSON", "context_packet.json"))
OUTPUT_MD = pathlib.Path(os.getenv("CONTEXT_PACKET_MD", "context_packet.md"))
RESULT_LIMIT = int(os.getenv("CONTEXT_RESULT_LIMIT", "30"))
CHAR_BUDGET = int(os.getenv("CONTEXT_CHAR_BUDGET", "12000"))

STOPWORDS = {
    "the","and","for","with","from","that","this","into","then","when","what","where","which",
    "que","para","con","del","las","los","una","uno","como","esto","esta","este","hacer","luego",
    "por","más","mas","pero","sin","sobre","cada","debe","deben","quiero","necesito","agente",
    "agentes","input","block","verbatim","verbatin"
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+"),
    re.compile(r"\b(?:ghp_|github_pat_|hf_|sk-|nvapi-)[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+\b", re.I),
]

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def sanitize(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED_SECRET]", result)
    return result

def derive_query(verbatim: str) -> str:
    clean = sanitize(verbatim)
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9_.\-/]{3,}", clean)
    order = []
    counts = {}
    for token in tokens:
        low = token.lower()
        if low in STOPWORDS or low == "[redacted_secret]":
            continue
        counts[low] = counts.get(low, 0) + 1
        if low not in order:
            order.append(low)
    position = {token: index for index, token in enumerate(order)}
    ranked = sorted(order, key=lambda value: (-counts[value], position[value]))
    return " ".join(ranked[:18]).strip()[:700]

def run_motor(filename: str, query: str):
    env = dict(os.environ)
    env["QUERY"] = query
    env["SOURCES_FILE"] = str(HERE / "sources.json")
    try:
        process = subprocess.run(
            [sys.executable, str(HERE / filename)],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"results": [], "errors": [{"motor": filename, "error": "TIMEOUT"}]}

    if process.returncode:
        return {
            "results": [],
            "errors": [{
                "motor": filename,
                "error": "EXIT_" + str(process.returncode),
                "stderr": process.stderr[-500:]
            }]
        }

    try:
        return json.loads(process.stdout)
    except Exception:
        return {
            "results": [],
            "errors": [{
                "motor": filename,
                "error": "INVALID_JSON",
                "stdout": process.stdout[-500:]
            }]
        }

def canonical_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        pairs = [(key, value) for key, value in pairs if not key.lower().startswith("utm_")]
        return urllib.parse.urlunsplit((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            urllib.parse.urlencode(pairs),
            ""
        ))
    except Exception:
        return url

def score(row, keywords):
    text = ((row.get("title") or "") + " " + (row.get("snippet") or "")).lower()
    overlap = sum(1 for keyword in keywords if keyword in text)
    stars_bonus = min(int(row.get("stars", 0) or 0) // 1000, 20)
    return int(row.get("priority", 50)) + overlap * 4 + stars_bonus

def write_markdown(packet):
    lines = [
        "# YAIWES RESEARCH CONTEXT PACKET",
        "",
        "Input SHA256: " + packet["input_sha256"],
        "Query: " + packet["query"],
        "Results: " + str(packet["result_count"]),
        ""
    ]
    used = sum(len(line) + 1 for line in lines)

    for index, row in enumerate(packet["results"], 1):
        chunk = (
            str(index) + ". [" + row["source"] + "/" + row["kind"] + "] " + row["title"] + "\n"
            + "   " + row["url"] + "\n"
            + "   " + row.get("snippet", "")[:700] + "\n"
        )
        if used + len(chunk) > CHAR_BUDGET:
            break
        lines.append(chunk)
        used += len(chunk)

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return used

def main():
    if not INPUT_BLOCK_FILE.is_file():
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "INPUT_BLOCK_FILE not found"
        }))

    verbatim = INPUT_BLOCK_FILE.read_text(encoding="utf-8")
    query = derive_query(verbatim)

    if not query:
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "No searchable terms after deterministic sanitization"
        }))

    outputs = [
        run_motor("motor_1_web_domains.py", query),
        run_motor("motor_2_github_search.py", query),
        run_motor("motor_3_huggingface_search.py", query),
    ]

    rows = []
    errors = []
    for output in outputs:
        rows.extend(output.get("results", []))
        errors.extend(output.get("errors", []))

    keywords = query.lower().split()
    deduplicated = {}

    for row in rows:
        url = canonical_url(row.get("url", ""))
        if not url:
            continue
        item = dict(row)
        item["url"] = url
        item["score"] = score(item, keywords)
        if url not in deduplicated or item["score"] > deduplicated[url]["score"]:
            deduplicated[url] = item

    ranked = sorted(
        deduplicated.values(),
        key=lambda item: (-item["score"], item["source"], item["url"])
    )[:RESULT_LIMIT]

    packet = {
        "schema": SCHEMA,
        "input_sha256": sha256_text(verbatim),
        "input_path": str(INPUT_BLOCK_FILE),
        "query": query,
        "queries": [query],
        "sources": sorted({row.get("source", "") for row in ranked if row.get("source")}),
        "results": ranked,
        "result_count": len(ranked),
        "context_chars": 0,
        "errors": errors,
        "verdict": "CONTEXT_READY" if ranked else "NO_NEW_EVIDENCE"
    }

    packet["context_chars"] = write_markdown(packet)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    print(json.dumps({
        "schema": SCHEMA,
        "input_sha256": packet["input_sha256"],
        "query": query,
        "result_count": len(ranked),
        "context_packet_json": str(OUTPUT_JSON),
        "context_packet_md": str(OUTPUT_MD),
        "verdict": packet["verdict"]
    }, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
