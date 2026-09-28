#!/usr/bin/env python3
"""T10: diagnóstico de OmniRoute sin API de terceros, solo contra el localhost del gateway.

Sin argumentos de --modelo NO hace inferencias. Con --modelo, como máximo 5
peticiones de texto, exactamente 1 por nombre solicitado, sin reintentos.
No inspecciona ni publica claves ni modifica ajustes.
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


PROMPT = "Responde exactamente OMNI_OK."
KNOWN_STOP = {
    "oc/big-pickle",       # prueba anterior: acceso OpenCode Free restringido
    "felo/felo-chat",      # prueba anterior: 400/429
    "felo/felo-search",    # prueba anterior: 400/429
}


def local_base(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "http" or p.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Solo se permite OmniRoute local (http://127.0.0.1:PUERTO)")
    if p.username or p.password or p.query or p.fragment or (p.path not in ("", "/")):
        raise ValueError("URL debe ser solo origen local, sin rutas, token ni query")
    return url.rstrip("/")


def fetch_json(base, endpoint, timeout=12, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        base + endpoint,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read(1_000_000)
            return res.status, parse_json(raw)
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, parse_json(exc.read(8192))
        finally:
            exc.close()
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, {}


def parse_json(raw):
    try:
        return json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}


def models_from_response(payload):
    if not isinstance(payload, dict):
        return set()
    rows = payload.get("data")
    if not isinstance(rows, list):
        return set()
    return {
        item["id"] for item in rows
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def has_assistant_text(payload):
    """HTTP 200 sin contenido real NO es éxito."""
    if not isinstance(payload, dict):
        return False
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return False
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return True
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text")
                    if isinstance(text, str) and text.strip():
                        return True
    return False


def classify(status, payload):
    if 200 <= status < 300:
        return "PASS" if has_assistant_text(payload) else "EMPTY_RESPONSE"
    if status == 0:
        return "CONNECTION_ERROR"
    if status in (401, 403):
        return "ACCESS_DENIED"
    if status in (418, 429):
        return "RATE_OR_ANTIABUSE_LIMIT"
    if status in (400, 404, 406, 422):
        return "INVALID_MODEL_OR_REQUEST"
    if status >= 500:
        return "UPSTREAM_OR_GATEWAY_ERROR"
    return "HTTP_ERROR"


def audit(base, requested, timeout=12, include_known_failures=False):
    base = local_base(base)
    health_code, _ = fetch_json(base, "/api/monitoring/health", timeout)
    model_code, model_payload = fetch_json(base, "/v1/models", timeout)
    available = models_from_response(model_payload) if model_code == 200 else set()
    result = {
        "gateway_health_http": health_code,
        "catalog_http": model_code,
        "catalog_count": len(available),
        "probe_count": 0,
        "results": [],
    }
    if not (200 <= health_code < 300 and model_code == 200):
        return result
    for model in requested:
        if model in KNOWN_STOP and not include_known_failures:
            result["results"].append({"model": model, "classification": "SKIPPED_PREVIOUS_ACCESS_ERROR"})
            continue
        if model not in available:
            result["results"].append({"model": model, "classification": "NOT_IN_CATALOG"})
            continue
        status, payload = fetch_json(base, "/v1/chat/completions", timeout, {
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": 32,
            "stream": False,
        })
        result["probe_count"] += 1
        result["results"].append({
            "model": model,
            "http": status,
            "classification": classify(status, payload),
            "assistant_text": has_assistant_text(payload),
        })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:20128")
    parser.add_argument("--modelo", action="append", default=[],
                        help="ID exacto anunciado en /v1/models (máximo 5)")
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--reprobar-fallidos", action="store_true",
                        help="Permitir una única prueba manual de fallos ya observados")
    args = parser.parse_args(argv)
    if len(args.modelo) > 5 or len(args.modelo) != len(set(args.modelo)):
        parser.error("Máximo 5 modelos distintos por ejecución")
    if not 1 <= args.timeout <= 20:
        parser.error("--timeout debe estar entre 1 y 20 s")
    try:
        result = audit(args.url, args.modelo, args.timeout, args.reprobar_fallidos)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not (200 <= result["gateway_health_http"] < 300 and result["catalog_http"] == 200):
        return 2
    if args.modelo and not any(x.get("classification") == "PASS" for x in result["results"]):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
