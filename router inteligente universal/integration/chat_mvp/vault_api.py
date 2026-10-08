"""HTTP surface of the Secret Bank inside the chat: /vault (page), /vault/status|unlock|lock|credentials|rotate|import,
DELETE /vault/credentials/{provider}/{account} and POST /vault/credentials/{provider}/{account}/enabled.

Every endpoint needs a Router API key. The passphrase is only used to open the bank in server memory; no endpoint returns a secret.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .router import _auth
from .vault_bridge import BankError, bridge

PAGE = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Banco secreto</title><style>body{font:16px system-ui;max-width:640px;margin:24px auto;padding:0 14px}input,button{font:inherit;padding:8px;margin:4px 0;width:100%;box-sizing:border-box}
button{width:auto;margin-right:8px}pre{background:#0001;padding:10px;border-radius:8px;white-space:pre-wrap}</style></head><body>
<h2>Banco secreto</h2><input id="k" type="password" placeholder="API key del Router (MAXBRY-…)" autocomplete="off">
<input id="p" type="password" placeholder="Contraseña maestra (solo abre el banco en memoria)" autocomplete="off">
<div><button id="u">Desbloquear</button><button id="l">Bloquear</button><button id="s">Estado</button></div><pre id="o"></pre>
<script>var $=function(i){return document.getElementById(i)};function call(m,p,b){return fetch(p,{method:m,headers:{'Content-Type':'application/json','X-API-Key':$('k').value},body:b?JSON.stringify(b):undefined}).then(function(r){return r.json().then(function(j){return {s:r.status,b:j}})})}
function show(r){$('o').textContent=r.s+' '+JSON.stringify(r.b,null,1)}
$('u').onclick=function(){call('POST','/vault/unlock',{passphrase:$('p').value}).then(function(r){$('p').value='';show(r)})};
$('l').onclick=function(){call('POST','/vault/lock').then(show)};$('s').onclick=function(){call('GET','/vault/status').then(show)};</script></body></html>"""


class UnlockReq(BaseModel):
    passphrase: str = Field(min_length=1, max_length=256)


class PutReq(BaseModel):
    ref: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]*/[a-z0-9][a-z0-9_.-]*$")
    secret: str = Field(min_length=1, max_length=4096)
    scope: str = "inference"


class EnabledReq(BaseModel):
    enabled: bool


_PART = r"^[a-z0-9][a-z0-9_.-]*$"


def _ref(provider: str, account: str) -> str:
    import re
    if not (re.match(_PART, provider) and re.match(_PART, account)):
        raise HTTPException(status_code=422, detail="INVALID_REF")
    return provider + "/" + account


class ImportReq(BaseModel):
    b64gz: str = Field(min_length=20, max_length=2_000_000)


def _run(fn: Any, *args: Any) -> Any:
    try:
        return fn(*args)
    except BankError as exc:
        code = str(exc)
        status = {"INVALID_PASSPHRASE": 401, "TOO_MANY_ATTEMPTS": 429, "VAULT_LOCKED": 423, "VAULT_MISSING": 404, "VAULT_EXISTS": 409, "CREDENTIAL_NOT_FOUND": 404}.get(code, 400)
        raise HTTPException(status_code=status, detail=code) from exc
    except Exception as exc:  # noqa: BLE001 - vault errors are reported by code only, never with values
        raise HTTPException(status_code=400, detail=type(exc).__name__) from exc


def _persisted(out: dict[str, Any]) -> dict[str, Any]:
    """Write-through to HF storage after every bank change; adds "persisted" only when storage is configured."""
    status = bridge.persist()
    if status != "SKIPPED_NOT_CONFIGURED":
        out["persisted"] = status
    return out


def build_vault_router() -> APIRouter:
    r = APIRouter()

    @r.get("/vault", response_class=HTMLResponse)
    def page() -> HTMLResponse:
        return HTMLResponse(PAGE)

    @r.get("/vault/status")
    def status(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return bridge.status()

    @r.post("/vault/unlock")
    def unlock(req: UnlockReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        count = _run(bridge.unlock, req.passphrase)
        return {"unlocked": True, "credentials": count}

    @r.post("/vault/lock")
    def lock(_owner: str = Depends(_auth)) -> dict[str, Any]:
        bridge.lock()
        return {"unlocked": False}

    @r.post("/vault/credentials")
    def put(req: PutReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        _run(bridge.put, req.ref, req.secret, req.scope)
        return _persisted({"stored": req.ref})

    @r.post("/vault/rotate")
    def rotate(req: PutReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        _run(bridge.rotate, req.ref, req.secret)
        return _persisted({"rotated": req.ref})

    @r.delete("/vault/credentials/{provider}/{account}")
    def delete(provider: str, account: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        ref = _ref(provider, account)
        _run(bridge.delete, ref)
        return _persisted({"deleted": ref})

    @r.post("/vault/credentials/{provider}/{account}/enabled")
    def set_enabled(provider: str, account: str, req: EnabledReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        ref = _ref(provider, account)
        _run(bridge.set_enabled, ref, req.enabled)
        return _persisted({"ref": ref, "enabled": req.enabled})

    @r.post("/vault/import")
    def import_vault(req: ImportReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"imported_bytes": _run(bridge.import_b64gz, req.b64gz)}

    return r
