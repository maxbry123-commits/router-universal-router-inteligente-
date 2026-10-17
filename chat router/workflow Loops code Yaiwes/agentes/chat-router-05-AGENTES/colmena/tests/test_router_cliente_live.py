"""Prueba sin SIMULADO: servidor HTTP local que imita POST /chat/send del Router."""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import router_cliente  # noqa: E402
from router_cliente import RouterCliente  # noqa: E402


def _sin_simulado():
    os.environ.pop("SIMULADO", None)


def _serve(status: int, payload: dict):
    seen: list[dict] = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            seen.append({"path": self.path, "body": json.loads(self.rfile.read(n))})
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


def test_envia_provider_auto_y_lee_reply():
    _sin_simulado()
    srv, seen = _serve(200, {"reply": "hola", "provider": "nvidia", "model": "x", "auto": True, "trace": []})
    try:
        url = f"http://127.0.0.1:{srv.server_port}"
        assert RouterCliente(live_url=url).chat("hi", "hermes.plan") == "hola"
    finally:
        srv.shutdown()
    assert seen[0]["path"] == "/chat/send"
    assert seen[0]["body"]["provider"] == "auto"
    assert "hi" in seen[0]["body"]["message"]


def test_error_400_devuelve_detail_plano():
    _sin_simulado()
    srv, seen = _serve(400, {"detail": "MODEL_REQUIRED"})
    orig, router_cliente.time.sleep = router_cliente.time.sleep, lambda s: None
    try:
        RouterCliente(live_url=f"http://127.0.0.1:{srv.server_port}").chat("hi", "x")
        raise AssertionError("debía fallar")
    except RuntimeError as exc:
        assert "HTTP 400: MODEL_REQUIRED" in str(exc)
    finally:
        router_cliente.time.sleep = orig
        srv.shutdown()
    assert len(seen) == 3
