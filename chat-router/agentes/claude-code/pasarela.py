"""Pasarela local Anthropic-compatible -> NVIDIA OpenAI-compatible.

Expone /v1/messages (stream y no stream), /v1/messages/count_tokens y
/v1/models en :8082 para que Claude Code use modelos del catálogo NVIDIA.
"""
import hmac
import json
import os
import uuid

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from normalizar import (anthropic_a_openai, estimar_tokens, modelo_destino,
                        openai_a_anthropic)

# Reutilizar el bridge del MISMO Space si el Router arranca esta pasarela.
# El bridge ya tiene el banco cifrado y la ruta NVIDIA; no requiere claves nuevas.
# Si no se activa este modo, el comportamiento NVIDIA directo sigue intacto.
MODO_BRIDGE = os.environ.get("RIU_CLAUDE_PASARELA_BRIDGE") == "1"
_PUERTO_BRIDGE = os.environ.get("BRIDGE_PORT", "7870")
if not _PUERTO_BRIDGE.isdecimal() or not (1 <= int(_PUERTO_BRIDGE) <= 65535):
    _PUERTO_BRIDGE = "7870"
UPSTREAM = ("http://127.0.0.1:" + _PUERTO_BRIDGE + "/v1/chat/completions"
            if MODO_BRIDGE else os.environ.get(
                "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1/chat/completions"))
PUERTO = int(os.environ.get("PUERTO_PASARELA", "8082"))

app = FastAPI(title="pasarela-claude-code-nvidia")


def _clave():
    return (os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("NVIDIA_API_KEY_1") or "")


def _cabeceras():
    if MODO_BRIDGE:
        # Auth exclusivamente loopback: la clave permanece dentro del backend.
        clave = os.environ.get("RIU_API_KEY", "").strip()
        if not clave:
            raise RuntimeError("CLAVE_BRIDGE_AUSENTE")
        return {"X-API-Key": clave, "Content-Type": "application/json"}
    return {"Authorization": f"Bearer {_clave()}", "Content-Type": "application/json"}

def _autenticado(request):
    """La pasarela solo acepta la clave del Router cuando usa el bridge con banco."""
    if not MODO_BRIDGE:
        return True  # respetar el uso directo legado del servicio local
    esperado = os.environ.get("RIU_API_KEY", "").strip()
    bearer = request.headers.get("authorization", "")
    ofrecido = bearer[7:].strip() if bearer.lower().startswith("bearer ") else request.headers.get("x-api-key", "")
    return bool(esperado) and hmac.compare_digest(ofrecido, esperado)


def _sse(evento, datos):
    return f"event: {evento}\ndata: {json.dumps(datos)}\n\n"


def _eventos_desde_respuesta(respuesta_openai, modelo):
    """Genera la secuencia SSE Anthropic a partir de una respuesta completa."""
    msg = openai_a_anthropic(respuesta_openai, modelo)
    eventos = []
    eventos.append(_sse("message_start", {
        "type": "message_start",
        "message": {**msg, "content": [], "stop_reason": None},
    }))
    for indice, bloque in enumerate(msg["content"]):
        if bloque["type"] == "text":
            eventos.append(_sse("content_block_start", {
                "type": "content_block_start", "index": indice,
                "content_block": {"type": "text", "text": ""}}))
            eventos.append(_sse("content_block_delta", {
                "type": "content_block_delta", "index": indice,
                "delta": {"type": "text_delta", "text": bloque["text"]}}))
        else:
            eventos.append(_sse("content_block_start", {
                "type": "content_block_start", "index": indice,
                "content_block": {"type": "tool_use", "id": bloque["id"],
                                  "name": bloque["name"], "input": {}}}))
            eventos.append(_sse("content_block_delta", {
                "type": "content_block_delta", "index": indice,
                "delta": {"type": "input_json_delta",
                          "partial_json": json.dumps(bloque["input"])}}))
        eventos.append(_sse("content_block_stop",
                            {"type": "content_block_stop", "index": indice}))
    eventos.append(_sse("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": msg["stop_reason"], "stop_sequence": None},
        "usage": {"output_tokens": msg["usage"]["output_tokens"]}}))
    eventos.append(_sse("message_stop", {"type": "message_stop"}))
    return eventos


@app.post("/v1/messages")
async def mensajes(request: Request):
    if not _autenticado(request):
        return JSONResponse(status_code=401, content={"type": "error", "error": {"type": "authentication_error", "message": "NO_AUTORIZADO"}})
    peticion = await request.json()
    modelo_original = peticion.get("model", "")
    cuerpo = anthropic_a_openai(peticion)
    quiere_stream = bool(peticion.get("stream"))
    cuerpo["stream"] = False  # upstream simple; el SSE se sintetiza local

    async with httpx.AsyncClient(timeout=120) as cliente:
        resp = await cliente.post(UPSTREAM, headers=_cabeceras(), json=cuerpo)
    if resp.status_code != 200:
        return JSONResponse(status_code=resp.status_code, content={
            "type": "error",
            "error": {"type": "api_error", "message": resp.text[:500]},
        })
    datos = resp.json()

    if not quiere_stream:
        return JSONResponse(content=openai_a_anthropic(datos, modelo_original))

    async def generar():
        for evento in _eventos_desde_respuesta(datos, modelo_original):
            yield evento

    return StreamingResponse(generar(), media_type="text/event-stream")


@app.post("/v1/messages/count_tokens")
async def contar_tokens(request: Request):
    if not _autenticado(request):
        return JSONResponse(status_code=401, content={"type": "error", "error": {"type": "authentication_error", "message": "NO_AUTORIZADO"}})
    peticion = await request.json()
    return {"input_tokens": estimar_tokens(peticion)}


@app.get("/v1/models")
async def modelos():
    modelo = modelo_destino(None)
    return {
        "data": [
            {"id": "claude-opus-4-1", "type": "model",
             "display_name": f"Opus -> {modelo}"},
            {"id": "claude-sonnet-4-5", "type": "model",
             "display_name": f"Sonnet -> {modelo}"},
            {"id": "claude-haiku-4-5", "type": "model",
             "display_name": f"Haiku -> {modelo}"},
        ],
        "has_more": False,
    }


@app.get("/")
async def raiz():
    return {"estado": "ok", "upstream": UPSTREAM, "id": uuid.uuid4().hex[:6]}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PUERTO)