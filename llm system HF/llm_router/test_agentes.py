import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest
import agentes


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n))
        if self.path != "/v1/chat/completions" or self.headers.get("Authorization") != "Bearer k":
            self.send_response(401); self.end_headers(); return
        out = {"choices": [{"message": {"role": "assistant", "content": "eco:" + body["messages"][-1]["content"]}}]}
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(out).encode())

    def do_GET(self):
        self.send_response(200 if self.path == "/healthz" else 404); self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture
def server(monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    monkeypatch.setenv("OPENCLAW_URL", base)
    monkeypatch.setenv("OPENCLAW_API_KEY", "k")
    monkeypatch.delenv("HERMES_URL", raising=False)
    yield base
    srv.shutdown()


def test_llamar_openclaw_ok(server):
    r = asyncio.run(agentes.dispatch({"agente": "openclaw", "messages": [{"role": "user", "content": "hola"}]}))
    assert r == {"status": "ok", "agente": "openclaw", "content": "eco:hola"}


def test_clave_mala_responde_failed(server, monkeypatch):
    monkeypatch.setenv("OPENCLAW_API_KEY", "mala")
    r = asyncio.run(agentes.dispatch({"agente": "openclaw", "messages": [{"role": "user", "content": "x"}]}))
    assert r["status"] == "failed" and r["http"] == 401


def test_sin_url_y_agente_desconocido(server):
    r = asyncio.run(agentes.dispatch({"agente": "hermes", "messages": []}))
    assert r["status"] == "failed" and "HERMES_URL" in r["error"]
    assert asyncio.run(agentes.dispatch({"agente": "rufo", "messages": []}))["status"] == "failed"


def test_health_openclaw(server):
    assert asyncio.run(agentes.health("openclaw"))["ok"] is True
