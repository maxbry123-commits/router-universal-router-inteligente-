#!/usr/bin/env python3
# Probe version: 1
import json, os, sys, urllib.request, urllib.error

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_PROBE_MODEL", "gpt-6-luna")

def request(url, *, method="GET", payload=None):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8")
        return r.status, json.loads(raw) if raw else {}

def emit(obj):
    print(json.dumps(obj, ensure_ascii=False))

if not API_KEY:
    emit({"ok": False, "stage": "config", "error": "OPENAI_API_KEY missing"})
    sys.exit(2)

try:
    status, models = request("https://api.openai.com/v1/models")
    emit({
        "ok": status == 200,
        "stage": "auth",
        "http_status": status,
        "models_visible": len(models.get("data", []))
    })
except urllib.error.HTTPError as e:
    raw = e.read().decode("utf-8", errors="replace")
    try:
        err = json.loads(raw)
    except Exception:
        err = {"raw": raw[:500]}
    emit({"ok": False, "stage": "auth", "http_status": e.code, "error": err})
    sys.exit(1)
except Exception as e:
    emit({"ok": False, "stage": "network", "error": str(e)})
    sys.exit(1)

try:
    status, response = request(
        "https://api.openai.com/v1/responses",
        method="POST",
        payload={
            "model": MODEL,
            "input": "Reply exactly: OK",
            "max_output_tokens": 8
        },
    )
    emit({
        "ok": status == 200,
        "stage": "billable_request",
        "http_status": status,
        "model": response.get("model", MODEL),
        "response_id_present": bool(response.get("id")),
        "usage_present": bool(response.get("usage"))
    })
except urllib.error.HTTPError as e:
    raw = e.read().decode("utf-8", errors="replace")
    try:
        err = json.loads(raw)
    except Exception:
        err = {"raw": raw[:500]}
    error_obj = err.get("error", err) if isinstance(err, dict) else err
    emit({
        "ok": False,
        "stage": "billable_request",
        "http_status": e.code,
        "model": MODEL,
        "error": error_obj
    })
    sys.exit(1)
except Exception as e:
    emit({"ok": False, "stage": "network", "error": str(e)})
    sys.exit(1)
