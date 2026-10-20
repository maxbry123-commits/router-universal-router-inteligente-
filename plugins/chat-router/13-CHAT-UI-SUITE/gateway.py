"""Gateway OpenAI-compatible para exponer Hermes/OpenClaw a UIs externas sin modificar su código."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

AGENT_MODELS = {
    "yaiwes/hermes": "hermes",
    "hermes": "hermes",
    "yaiwes/openclaw": "openclaw",
    "openclaw": "openclaw",
}


def _load_bridge():
    bridge_path = Path(__file__).resolve().parents[1] / "05-AGENTES" / "asistentes" / "puente_asistentes.py"
    if not bridge_path.is_file():
        raise RuntimeError(f"puente_asistentes no existe: {bridge_path}")
    spec = importlib.util.spec_from_file_location("yaiwes_puente_asistentes", bridge_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se pudo cargar puente_asistentes")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BRIDGE = _load_bridge()


def list_models() -> dict[str, Any]:
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {"id": "yaiwes/hermes", "object": "model", "created": now, "owned_by": "yaiwes"},
            {"id": "yaiwes/openclaw", "object": "model", "created": now, "owned_by": "yaiwes"},
        ],
    }


def _messages_to_prompt(messages: Any) -> str:
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages requerido")
    chunks: list[str] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user"))
        content = item.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(str(part.get("text", "")))
            content = "\n".join(text_parts)
        content = str(content).strip()
        if content:
            chunks.append(f"[{role}] {content}")
    if not chunks:
        raise ValueError("messages sin contenido")
    return "\n".join(chunks)


def dispatch_chat(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload inválido")
    model = str(payload.get("model", "")).strip().lower()
    agent = AGENT_MODELS.get(model)
    if not agent:
        raise ValueError("model debe ser yaiwes/hermes o yaiwes/openclaw")
    prompt = _messages_to_prompt(payload.get("messages"))
    answer = BRIDGE.preguntar(agent, prompt)
    now = int(time.time())
    return {
        "id": f"chatcmpl-yaiwes-{now}",
        "object": "chat.completion",
        "created": now,
        "model": f"yaiwes/{agent}",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "YAIWESChatGateway/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.getenv("YAIWES_GATEWAY_LOG", "0") == "1":
            super().log_message(fmt, *args)

    def _json(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = self.path.rstrip("/") or "/"
        if path == "/health":
            self._json(200, {"ok": True, "agents": ["hermes", "openclaw"]})
            return
        if path in {"/v1/models", "/models"}:
            self._json(200, list_models())
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        path = self.path.rstrip("/")
        if path not in {"/v1/chat/completions", "/chat/completions"}:
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._json(200, dispatch_chat(payload))
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(502, {"error": "assistant_bridge_failed", "detail": type(exc).__name__})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("YAIWES_CHAT_GATEWAY_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("YAIWES_CHAT_GATEWAY_PORT", "8099")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"YAIWES chat gateway http://{args.host}:{args.port}/v1")
    server.serve_forever()


if __name__ == "__main__":
    main()
