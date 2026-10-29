"""Minimal FastAPI hot-path: Auth -> Enchufe/Red -> adapter -> verifier."""
from __future__ import annotations
import hashlib
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("security", "red", "adapters", "verifier"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Header, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from api_key_guard import authorize_bearer  # noqa: E402
from api_key_manager import APIKeyManager  # noqa: E402
from github_public import build_github_public_adapter  # noqa: E402
from red_universal import Mensaje, RedUniversal  # noqa: E402
from response_verifier import verify_response  # noqa: E402


class ChatRequest(BaseModel):
    model: str = "github/public"
    messages: list[dict] = Field(default_factory=list)
    path: str = "Handoff router inteligente universal.md"


def _contract() -> dict:
    dt = {"family": "json", "type": "object", "version": 1}
    adapter_path = ROOT / "adapters" / "github_public.py"
    contract_hash = "sha256:" + hashlib.sha256(adapter_path.read_bytes()).hexdigest()
    return {
        "artifact_id": "github.public.adapter",
        "estado": "active",
        "contract_hash": contract_hash,
        "ejecucion": {"kind": "code", "transport": "http"},
        "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 30000, "deadline_ms": 35000}},
        "contrato": {"rol": "service", "consume": {"datatype": dt}, "expone": {"datatype": dt}},
    }


def create_app(manager: APIKeyManager | None = None, repo: str = "maxbry123-commits/router-universal-router-inteligente-") -> FastAPI:
    key_manager = manager or APIKeyManager()
    red = RedUniversal()
    red.conectar("dest.github.public", build_github_public_adapter(repo), _contract())
    red.ruta("hotpath.github", "agent.*", "dest.github.public", cuando="route.github")
    app = FastAPI(title="Router Inteligente Universal")
    app.state.key_manager = key_manager
    app.state.red = red

    @app.get("/v1/models")
    async def models(authorization: str | None = Header(default=None)) -> dict:
        auth = authorize_bearer(authorization, key_manager, scope="route")
        if not auth.ok:
            raise HTTPException(auth.status_code, auth.detail)
        return {"data": [{"id": "github/public", "object": "model"}]}

    @app.post("/v1/chat/completions")
    async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> dict:
        auth = authorize_bearer(authorization, key_manager, scope="route", model_id=req.model)
        if not auth.ok:
            raise HTTPException(auth.status_code, auth.detail)
        task_id = uuid.uuid4().hex
        result = await red.enviar(Mensaje(
            "route.github", f"agent.{auth.principal['agent_id']}",
            {"_accion": "get_file", "path": req.path},
            task_id=task_id, trace_id=task_id,
        ))
        verdict = verify_response(result)
        if not verdict["verified"]:
            raise HTTPException(502, {"verifier": verdict, "destination": result})
        return {
            "id": task_id,
            "object": "chat.completion",
            "route": "FastAPI->APIKeyGuard->EnchufeGate->RedUniversal->GitHubAdapter->Verifier",
            "provider": "github",
            "verified": True,
            "via": result["via"],
            "response": result["output"],
        }

    return app
