"""Pruebas del proxy /web al bridge existente: sin Hugging Face ni credenciales reales."""
import asyncio
import json
from unittest.mock import patch
import httpx
from fastapi import FastAPI
from mvp import bridge_proxy


AsyncClientReal = httpx.AsyncClient


def exercise(handler, ruta, method="GET", payload=None, headers=None):
    seen = []
    def backend(req):
        seen.append(req)
        return handler(req)
    app = FastAPI()
    bridge_proxy.montar(app)
    def crear_backend(*a, **k):
        return AsyncClientReal(transport=httpx.MockTransport(backend), base_url="http://127.0.0.1:7870")
    async def run():
        with patch.object(bridge_proxy.httpx, "AsyncClient", new=crear_backend):
            async with AsyncClientReal(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                return await client.request(method, ruta, json=payload, headers=headers or {})
    return asyncio.run(run()), seen


def test_web_get_catalog_and_forward_auth():
    def handler(req):
        assert req.url.path == "/v1/modelos/disponibilidad"
        assert req.headers["x-api-key"] == "FALSA-CLAVE-PRUEBA"
        assert req.headers["accept-encoding"] == "identity"
        return httpx.Response(200, json={"ok": True, "configurados": {"groq": True}})
    r, seen = exercise(handler, "/web/v1/modelos/disponibilidad", headers={"x-api-key": "FALSA-CLAVE-PRUEBA"})
    assert r.status_code == 200 and r.json()["configurados"]["groq"] is True
    assert len(seen) == 1


def test_web_stream_sse_no_fallback_and_raw_chunks():
    stream = b'data: {"choices":[{"delta":{"content":"OK"}}]}\n\ndata: [DONE]\n\n'
    def handler(req):
        assert req.method == "POST"
        assert req.url.path == "/v1/chat/completions"
        assert json.loads(req.content.decode())["model"] == "nvidia/z-ai/glm-5.3"
        return httpx.Response(200, content=stream, headers={"content-type": "text/event-stream", "cache-control": "no-cache"})
    r, seen = exercise(handler, "/web/v1/chat/completions", method="POST", payload={"model": "nvidia/z-ai/glm-5.3"}, headers={"x-api-key": "FALSA-CLAVE-PRUEBA"})
    assert r.status_code == 200
    assert r.content == stream and "text/event-stream" in r.headers["content-type"]
    assert len(seen) == 1


def test_proxy_rejects_unknown_paths_without_network():
    r, seen = exercise(lambda req: (_ for _ in ()).throw(AssertionError("no upstream")), "/web/plugins/otra-raiz")
    assert r.status_code == 404 and not seen


def test_proxy_fails_closed_when_bridge_is_down():
    def down(req):
        raise httpx.ConnectError("connection refused", request=req)
    r, seen = exercise(down, "/web/v1/models", headers={"x-api-key": "FALSA-CLAVE-PRUEBA"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "BRIDGE_NO_DISPONIBLE"


def test_web_health_is_supported():
    r, seen = exercise(lambda req: httpx.Response(200, json={"ok": True}), "/web/health")
    assert r.status_code == 200 and len(seen) == 1


def test_web_openclaw_provider_alias_reaches_existing_bridge():
    def handler(req):
        assert req.url.path == "/openclaw/v1/models"
        assert req.headers["authorization"] == "Bearer CLAVE-FALSA-PRUEBA"
        return httpx.Response(200, json={"object": "list", "data": [{"id": "web-qwen38max"}]})
    r, seen = exercise(handler, "/web/openclaw/v1/models",
                       headers={"authorization": "Bearer CLAVE-FALSA-PRUEBA"})
    assert r.status_code == 200 and r.json()["data"][0]["id"] == "web-qwen38max"
    assert len(seen) == 1


def test_web_openclaw_provider_completion_preserves_body():
    payload = {"model": "web-qwen38max", "messages": [{"role": "user", "content": "hola"}]}
    def handler(req):
        assert req.url.path == "/openclaw/v1/chat/completions"
        assert json.loads(req.content) == payload
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]})
    r, seen = exercise(handler, "/web/openclaw/v1/chat/completions",
                       method="POST", payload=payload, headers={"x-api-key": "CLAVE-FALSA-PRUEBA"})
    assert r.status_code == 200 and r.json()["choices"][0]["message"]["content"] == "ok"


def test_web_openclaw_only_whitelists_models_and_completions():
    for ruta in ("openclaw/v1/claves", "openclaw/v1/swe/avanzar",
                 "openclaw/admin", "openclaw/v1/models/../../../v1/claves"):
        r, seen = exercise(lambda req: (_ for _ in ()).throw(AssertionError("No upstream")),
                           "/web/" + ruta)
        assert r.status_code in (400, 404) and not seen
