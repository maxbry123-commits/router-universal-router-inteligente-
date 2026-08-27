"""HTTP API del Router Universal NCT.

Contrato mínimo para Vercel/control plane. Los procesadores HF1/HF2/HF3
se configuran exclusivamente mediante variables de entorno; nunca se
persisten credenciales ni endpoints en el frontend.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

PROCESSORS = ("HF1", "HF2", "HF3")


def processor_config():
    return {
        pid: {
            "processor_id": pid,
            "endpoint": os.getenv(f"{pid}_ENDPOINT", "").rstrip("/"),
            "status": "configured" if os.getenv(f"{pid}_ENDPOINT") else "unavailable",
        }
        for pid in PROCESSORS
    }


def processor_health(pid):
    item = processor_config()[pid]
    endpoint = item["endpoint"]
    if not endpoint:
        return {"processor_id": pid, "status": "unavailable", "endpoint": None}
    try:
        req = Request(endpoint + "/health", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as response:
            ok = 200 <= response.status < 300
            return {"processor_id": pid, "status": "healthy" if ok else "degraded", "endpoint": endpoint}
    except Exception:
        return {"processor_id": pid, "status": "unavailable", "endpoint": endpoint}


def select_processor():
    for pid in PROCESSORS:
        state = processor_health(pid)
        if state["status"] == "healthy":
            return state
    return None


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/health":
            states = [processor_health(pid) for pid in PROCESSORS]
            healthy = any(x["status"] == "healthy" for x in states)
            self.send_json(200, {"ok": True, "status": "healthy" if healthy else "degraded", "processors": states})
            return
        if path == "/processors":
            self.send_json(200, {"processors": [processor_health(pid) for pid in PROCESSORS]})
            return
        if path == "/providers":
            self.send_json(200, {"providers": []})
            return
        if path == "/models":
            self.send_json(200, {"models": []})
            return
        self.send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/route/test":
            selected = select_processor()
            if selected is None:
                self.send_json(503, {"ok": False, "status": "FAIL_CLOSED", "selected": None})
            else:
                self.send_json(200, {"ok": True, "selected": selected["processor_id"], "reason": "healthy_capacity"})
            return
        if path in ("/providers/validate", "/providers/register"):
            self.send_json(501, {"ok": False, "error": "provider_registry_not_configured"})
            return
        self.send_json(404, {"ok": False, "error": "not_found"})

    def log_message(self, fmt, *args):
        print("[router-api] " + (fmt % args))


if __name__ == "__main__":
    host = os.getenv("ROUTER_HOST", "0.0.0.0")
    port = int(os.getenv("ROUTER_PORT", "8080"))
    print(f"Router API listening on {host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
