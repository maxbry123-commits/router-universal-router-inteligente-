"""Single FastAPI gateway for certified Hugging Face models.

Routes are intentionally thin. The gateway validates the request, delegates
model execution to the HF adapter, and remains fail-closed until auth/E2E are
completed in P03.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .huggingface_openai_chat import allowed_model_ids, chat_completion

app = FastAPI(title="Router Inteligente Universal HF Gateway", version="0.1.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int = Field(default=256, ge=1, le=4096)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "registry_count": len(allowed_model_ids()), "auth": "P03_PENDING"}


@app.get("/v1/models")
def models() -> dict[str, object]:
    return {"object": "list", "data": [{"id": model_id, "object": "model"} for model_id in sorted(allowed_model_ids())]}


@app.post("/v1/chat/completions")
def chat(req: ChatRequest) -> dict[str, object]:
    try:
        result = chat_completion(
            model_id=req.model,
            messages=[m.model_dump() for m in req.messages],
            max_tokens=req.max_tokens,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "object": "chat.completion",
        "model": result["model"],
        "choices": [{"index": 0, "message": result["message"], "finish_reason": result["finish_reason"]}],
    }
