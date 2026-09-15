"""Single FastAPI gateway for certified Hugging Face models.

Routes stay thin: authentication is enforced at the HTTP boundary and valid
requests continue through the persisted Enchufe Gate + RedUniversal.
"""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .api_key_auth import authenticate_api_key
from .huggingface_openai_chat import allowed_model_ids
from .router_hot_path import route_chat_completion

app = FastAPI(title="Router Inteligente Universal HF Gateway", version="0.3.0")


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
        "auth": "RIU_AGENT_API_KEYS",
    }


@app.get("/v1/models")
def models() -> dict[str, object]:
    return {
        "object": "list",
        "data": [{"id": model_id, "object": "model"} for model_id in sorted(allowed_model_ids())],
    }


@app.post("/v1/chat/completions")
async def chat(
    req: ChatRequest,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, object]:
    candidate = x_api_key
    if not candidate and authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:].strip()
    try:
        agent_id = authenticate_api_key(candidate)
        result = await route_chat_completion(
            model_id=req.model,
            messages=[m.model_dump() for m in req.messages],
            max_tokens=req.max_tokens,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        detail = str(exc)
        status = 401 if detail.startswith("RIU_API_KEY_") else 503
        raise HTTPException(status_code=status, detail=detail) from exc
    return {
        "object": "chat.completion",
        "model": result["model"],
        "agent_id": agent_id,
        "choices": [
            {
                "index": 0,
                "message": result["message"],
                "finish_reason": result["finish_reason"],
            }
        ],
    }
