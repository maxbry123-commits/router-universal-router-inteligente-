from __future__ import annotations

import base64
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import riu_router_bridge as bridge  # noqa: E402
import ficha_contract_v2 as fables  # noqa: E402


class _MockHandler(BaseHTTPRequestHandler):
    events: list[tuple[str, str, dict[str, str], bytes]] = []

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _respond(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        type(self).events.append(("GET", self.path, dict(self.headers), b""))
        self._respond(200, {"ok": True, "path": self.path})

    def do_POST(self) -> None:  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        type(self).events.append(("POST", self.path, dict(self.headers), body))
        self._respond(200, {"ok": True, "path": self.path})


class PluginBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _MockHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.old_base = os.environ.get("RIU_ROUTER_BASE_URL")
        cls.old_key = os.environ.get("RIU_ROUTER_API_KEY")
        os.environ["RIU_ROUTER_BASE_URL"] = f"http://127.0.0.1:{cls.server.server_port}"
        os.environ["RIU_ROUTER_API_KEY"] = "test-only-not-a-real-secret"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        for name, old in (("RIU_ROUTER_BASE_URL", cls.old_base), ("RIU_ROUTER_API_KEY", cls.old_key)):
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old

    def setUp(self) -> None:
        _MockHandler.events.clear()

    def test_register_exposes_only_expected_tools(self) -> None:
        class Context:
            def __init__(self) -> None:
                self.tools = []

            def register_tool(self, **kwargs: Any) -> None:
                self.tools.append(kwargs)

        ctx = Context()
        bridge.register(ctx)
        names = {row["name"] for row in ctx.tools}
        self.assertEqual(
            names,
            {
                "riu_router_health",
                "riu_storage_status",
                "riu_list_conversations",
                "riu_read_conversation",
                "riu_send_chat_turn",
                "riu_upload_text_document",
                "riu_graph_status",
            },
        )
        self.assertTrue(all(row["toolset"] == "riu_router" for row in ctx.tools))

    def test_manifest_passes_supplied_fables_v2_validator(self) -> None:
        manifest = json.loads((HERE / "ficha_riu_router_bridge_v2.json").read_text(encoding="utf-8"))
        result = fables.validar(manifest)
        self.assertTrue(result.valido, result.errores)

    def test_health_request_sends_router_key_header(self) -> None:
        result = json.loads(bridge.router_health({}))
        self.assertTrue(result["ok"])
        method, path, headers, _ = _MockHandler.events[-1]
        self.assertEqual((method, path), ("GET", "/health"))
        self.assertEqual(headers.get("X-Api-Key"), "test-only-not-a-real-secret")

    def test_send_turn_posts_to_router_and_returns_only_response(self) -> None:
        result = json.loads(bridge.send_chat_turn({"message": "prueba", "model": "model-test"}))
        self.assertTrue(result["ok"])
        method, path, headers, raw = _MockHandler.events[-1]
        self.assertEqual((method, path), ("POST", "/chat/send"))
        payload = json.loads(raw)
        self.assertEqual(payload["message"], "prueba")
        self.assertEqual(payload["model"], "model-test")
        self.assertEqual(payload["mode"], "direct")
        self.assertEqual(headers.get("X-Api-Key"), "test-only-not-a-real-secret")

    def test_text_upload_encodes_text_for_existing_document_api(self) -> None:
        bridge.upload_text_document({"name": "nota.txt", "text": "contenido", "conversation_id": "conv-1"})
        method, path, _headers, raw = _MockHandler.events[-1]
        self.assertEqual((method, path), ("POST", "/chat/documents"))
        payload = json.loads(raw)
        self.assertEqual(base64.b64decode(payload["data_b64"]).decode(), "contenido")
        self.assertEqual(payload["conversation_id"], "conv-1")

    def test_rejects_invalid_conversation_path(self) -> None:
        with self.assertRaises(ValueError):
            bridge.read_conversation({"conversation_id": "../other"})
        self.assertEqual(_MockHandler.events, [])

    def test_non_local_http_is_rejected(self) -> None:
        os.environ["RIU_ROUTER_BASE_URL"] = "http://router.example.com"
        try:
            with self.assertRaisesRegex(RuntimeError, "HTTPS"):
                bridge.router_health({})
            self.assertEqual(_MockHandler.events, [])
        finally:
            os.environ["RIU_ROUTER_BASE_URL"] = f"http://127.0.0.1:{self.server.server_port}"

    def test_missing_key_fails_closed(self) -> None:
        key = os.environ.pop("RIU_ROUTER_API_KEY")
        try:
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                bridge.router_health({})
            self.assertEqual(_MockHandler.events, [])
        finally:
            os.environ["RIU_ROUTER_API_KEY"] = key


if __name__ == "__main__":
    unittest.main()
