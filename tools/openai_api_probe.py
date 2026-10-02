#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.error

key = os.getenv("OPENAI_API_KEY")
if not key:
    print(json.dumps({"ok": False, "stage": "config", "error": "OPENAI_API_KEY missing"}))
    sys.exit(2)

url = "https://api.openai.com/v1/models"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})

try:
    with urllib.request.urlopen(req, timeout=20) as r:
        body = json.loads(r.read().decode("utf-8"))
        print(json.dumps({
            "ok": True,
            "stage": "auth",
            "http_status": r.status,
            "models_visible": len(body.get("data", []))
        }))
except urllib.error.HTTPError as e:
    raw = e.read().decode("utf-8", errors="replace")
    try:
        err = json.loads(raw)
    except Exception:
        err = {"raw": raw[:500]}
    print(json.dumps({
        "ok": False,
        "stage": "auth",
        "http_status": e.code,
        "error": err
    }))
    sys.exit(1)
except Exception as e:
    print(json.dumps({"ok": False, "stage": "network", "error": str(e)}))
    sys.exit(1)
