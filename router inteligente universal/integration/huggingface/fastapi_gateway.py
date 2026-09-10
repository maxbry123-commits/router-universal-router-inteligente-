"""Single FastAPI gateway for certified Hugging Face models.

Routes are intentionally thin. The gateway validates the request and sends it
through the persisted Enchufe Gate + RedUniversal before the HF adapter.
Authentication remains fail-closed/pending until P03.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .huggingface_openai_chat import allowed_model_ids
from .router_hot_path import route_chat_completion

app = FastAPI(title="Router Inteligente Universal HF Gateway", version="0.2.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int = Field(default=256, ge=1, le=4096)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "registry_count": len(allowed_model_ids()),
        "route": "FastAPI->EnchufeGate->RedUniversal->HFAdapter",
        "auth": "P03_PENDING",
    }


@app.get("/v1/models")
def models() -> dict[str, object]:
    return {
        "object": "list",
        "data": [{"id": model_id, "object": "model"} for model_id in sorted(allowed_model_ids())],
    }


@app.post("/v1/chat/completions")
async def chat(req: ChatRequest) -> dict[str, object]:
    try:
        result = await route_chat_completion(
            model_id=req.model,
            messages=[m.model_dump() for m in req.messages],
            max_tokens=req.max_tokens,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "object": "chat.completion",
        "model": result["model"],
        "choices": [
            {
                "index": 0,
                "message": result["message"],
                "finish_reason": result["finish_reason"],
            }
        ],
    }
