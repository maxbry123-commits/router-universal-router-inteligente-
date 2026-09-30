"""Sin red externa: servidor local 127.0.0.1 que imita POST /chat/route del Router."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import puente_asistentes  # noqa: E402
import router_cliente  # noqa: E402


def _serve(status, payload):
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            seen.append({"path": self.path, "body": json.loads(self.rfile.read(n)),
                         "key": self.headers.get("X-API-Key")})
            out = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, seen


def _live(monkeypatch, srv):
    monkeypatch.delenv("SIMULADO", raising=False)
    monkeypatch.setenv("RIU_LIVE_URL", f"http://127.0.0.1:{srv.server_port}")
    monkeypatch.setenv("RIU_ROUTER_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(router_cliente.time, "sleep", lambda s: None)


def test_puente_postea_chat_route_grupo_assistants(monkeypatch):
    srv, seen = _serve(200, {"group": "assistants", "reply": "hola desde el router", "route": {}, "trace": []})
    _live(monkeypatch, srv)
    try:
        assert puente_asistentes.preguntar("hermes", "planifica") == "hola desde el router"
    finally:
        srv.shutdown()
    assert seen[0]["path"] == "/chat/route"
    assert seen[0]["body"]["group"] == "assistants"
    assert "planifica" in seen[0]["body"]["message"] and "planner_supervisor" in seen[0]["body"]["message"]
    assert "model" not in seen[0]["body"] and seen[0]["key"] == "clave-de-prueba"


def test_puente_error_devuelve_detail_plano(monkeypatch):
    srv, seen = _serve(502, {"detail": "ALL_ROUTES_FAILED"})
    _live(monkeypatch, srv)
    try:
        try:
            puente_asistentes.preguntar("openclaw", "vigila")
            raise AssertionError("debía fallar")
        except RuntimeError as exc:
            assert "ALL_ROUTES_FAILED" in str(exc) and "HTTP 502" in str(exc)
    finally:
        srv.shutdown()


def test_cliente_sin_group_sigue_en_chat_send(monkeypatch):
    srv, seen = _serve(200, {"reply": "ok"})
    _live(monkeypatch, srv)
    try:
        assert router_cliente.RouterCliente().chat("x", "hermes.plan") == "ok"
    finally:
        srv.shutdown()
    assert seen[0]["path"] == "/chat/send" and seen[0]["body"]["provider"] == "auto"


def test_simulado_no_usa_red(monkeypatch):
    monkeypatch.setenv("SIMULADO", "1")
    monkeypatch.setenv("RIU_LIVE_URL", "http://127.0.0.1:9")
    assert puente_asistentes.preguntar("hermes", "a").startswith("SIMULADO:hermes:")
