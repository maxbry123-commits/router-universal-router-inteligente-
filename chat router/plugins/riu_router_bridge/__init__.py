"""Hermes tools that call the existing RIU Router HTTP API; never imports Router code."""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PLUGIN_ID = "riu-router-bridge"
MAX_DOCUMENT_BYTES = 2_800_000
MAX_RESPONSE_BYTES = 1_000_000


def _json_result(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    """Call only the configured Router origin; never accept an origin from tool input."""
    base = os.environ.get("RIU_ROUTER_BASE_URL", "").strip().rstrip("/")
    key = os.environ.get("RIU_ROUTER_API_KEY", "")
    if not base or not key:
        raise RuntimeError("RIU_ROUTER_BASE_URL or RIU_ROUTER_API_KEY is not configured")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.username or parsed.password:
        raise RuntimeError("RIU_ROUTER_BASE_URL must be an http(s) origin without embedded credentials")
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("RIU_ROUTER_BASE_URL must use HTTPS outside localhost")
    url = base + path
    headers = {"Accept": "application/json", "X-API-Key": key}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise RuntimeError("Router response exceeds the plugin limit")
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not include response bodies: they may contain prompts, messages or other user data.
        raise RuntimeError(f"RIU Router returned HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"RIU Router connection failed ({type(exc.reason).__name__})") from None


def router_health(_params: dict[str, Any], **_kwargs: Any) -> str:
    return _json_result(_request("GET", "/health"))


def storage_status(_params: dict[str, Any], **_kwargs: Any) -> str:
    return _json_result(_request("GET", "/chat/storage"))


def list_conversations(_params: dict[str, Any], **_kwargs: Any) -> str:
    return _json_result(_request("GET", "/chat/conversations"))


def read_conversation(params: dict[str, Any], **_kwargs: Any) -> str:
    conversation_id = str(params.get("conversation_id", "")).strip()
    if not conversation_id or len(conversation_id) > 160 or "/" in conversation_id or "\\" in conversation_id:
        raise ValueError("conversation_id is invalid")
    path = "/chat/conversations/" + urllib.parse.quote(conversation_id, safe="")
    return _json_result(_request("GET", path))


def send_chat_turn(params: dict[str, Any], **_kwargs: Any) -> str:
    message = str(params.get("message", ""))
    model = str(params.get("model", ""))
    if not message.strip() or len(message) > 20_000:
        raise ValueError("message must contain 1–20000 characters")
    if not model or len(model) > 200:
        raise ValueError("model is required and must be <=200 characters")
    payload: dict[str, Any] = {
        "message": message,
        "provider": str(params.get("provider") or "hf"),
        "model": model,
        "mode": str(params.get("mode") or "direct"),
        "cache": True,
    }
    if params.get("conversation_id"):
        payload["conversation_id"] = str(params["conversation_id"])
    if payload["mode"] == "agent":
        agent_id = str(params.get("agent_id") or "")
        if not agent_id:
            raise ValueError("agent_id is required in agent mode")
        payload["agent_id"] = agent_id
    elif payload["mode"] != "direct":
        raise ValueError("mode must be direct or agent")
    doc_ids = params.get("doc_ids") or []
    if not isinstance(doc_ids, list) or len(doc_ids) > 20:
        raise ValueError("doc_ids must be a list of at most 20 ids")
    payload["doc_ids"] = [str(doc_id)[:160] for doc_id in doc_ids]
    return _json_result(_request("POST", "/chat/send", payload))


def upload_text_document(params: dict[str, Any], **_kwargs: Any) -> str:
    name = str(params.get("name", "document.txt")).strip()
    text = str(params.get("text", ""))
    conversation_id = str(params.get("conversation_id") or "")
    if not name or len(name) > 200 or "/" in name or "\\" in name:
        raise ValueError("name must be a filename, not a path")
    if not text:
        raise ValueError("text is required")
    raw = text.encode("utf-8")
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds the 2.8 MB plugin limit")
    payload = {
        "name": name,
        "mime": "text/plain; charset=utf-8",
        "data_b64": base64.b64encode(raw).decode("ascii"),
        "conversation_id": conversation_id or None,
    }
    return _json_result(_request("POST", "/chat/documents", payload))


def graph_status(_params: dict[str, Any], **_kwargs: Any) -> str:
    return _json_result(_request("GET", "/chat/graph"))


_TOOL_SPECS = [
    ("riu_router_health", "Read health of the configured RIU Router.", {"type": "object", "properties": {}, "additionalProperties": False}, router_health),
    ("riu_storage_status", "Read SQLite, document, graph and bucket configuration counts from the Router. Does not write or sync.", {"type": "object", "properties": {}, "additionalProperties": False}, storage_status),
    ("riu_list_conversations", "List conversations visible to this Router API key.", {"type": "object", "properties": {}, "additionalProperties": False}, list_conversations),
    ("riu_read_conversation", "Read one conversation and its saved messages.", {"type": "object", "properties": {"conversation_id": {"type": "string", "maxLength": 160}}, "required": ["conversation_id"], "additionalProperties": False}, read_conversation),
    ("riu_send_chat_turn", "Send a user-requested chat turn through the existing Router; it is saved by the Router's normal conversation store.", {"type": "object", "properties": {"message": {"type": "string", "minLength": 1, "maxLength": 20000}, "provider": {"type": "string"}, "model": {"type": "string", "maxLength": 200}, "conversation_id": {"type": "string"}, "mode": {"type": "string", "enum": ["direct", "agent"]}, "agent_id": {"type": "string"}, "doc_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 20}}, "required": ["message", "model"], "additionalProperties": False}, send_chat_turn),
    ("riu_upload_text_document", "Upload a user-provided text document to the Router's existing document store. Does not sync it to Hugging Face.", {"type": "object", "properties": {"name": {"type": "string", "maxLength": 200}, "text": {"type": "string"}, "conversation_id": {"type": "string"}}, "required": ["name", "text"], "additionalProperties": False}, upload_text_document),
    ("riu_graph_status", "Read the Router's existing graph/provenance view; does not write to it.", {"type": "object", "properties": {}, "additionalProperties": False}, graph_status),
]


def register(ctx: Any) -> None:
    """Register read/write tools in Hermes. The Hermes admin must explicitly enable this plugin."""
    for name, description, parameters, handler in _TOOL_SPECS:
        ctx.register_tool(
            name=name,
            toolset="riu_router",
            schema={"name": name, "description": description, "parameters": parameters},
            handler=handler,
        )
