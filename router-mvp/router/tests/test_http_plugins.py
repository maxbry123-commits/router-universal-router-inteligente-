import json, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from red import http_plugins as hp  # noqa: E402


def _serve(reply, seen):
    class Hd(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            seen.update(path=self.path, key=self.headers.get("X-API-Key"), body=json.loads(self.rfile.read(n)))
            b = json.dumps(reply).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        def log_message(self, *a):
            pass
    s = HTTPServer(("127.0.0.1", 0), Hd)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def test_llamar_ok(monkeypatch):
    seen = {}
    s = _serve({"status": "ok", "result": {"x": 1}}, seen)
    monkeypatch.setenv("RIU_ROUTER_URL", f"http://127.0.0.1:{s.server_port}")
    monkeypatch.setenv("RIU_API_KEY", "k")
    assert hp.llamar("puente_chat", "chat", {"a": 2}) == {"x": 1}
    assert seen == {"path": "/plugins/puente_chat/call/chat", "key": "k", "body": {"a": 2}}
    s.shutdown()


def test_llamar_degradado(monkeypatch):
    s = _serve({"status": "degraded", "reason": "plugin apagado"}, {})
    monkeypatch.setenv("RIU_ROUTER_URL", f"http://127.0.0.1:{s.server_port}")
    assert hp.llamar("p", "a")["error"] == "plugin apagado"
    s.shutdown()


def test_sin_url(monkeypatch):
    monkeypatch.delenv("RIU_ROUTER_URL", raising=False)
    assert "error" in hp.llamar("p", "a")
