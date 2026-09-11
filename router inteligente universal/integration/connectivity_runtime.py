"""Runtime central de conectividad del Router Inteligente Universal.

No persiste credenciales. Solo resuelve referencias de entorno en runtime y
aplica fail-closed antes de cualquier llamada externa. Las respuestas públicas
nunca incluyen valores secretos.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


HF_ENV_REFS = ("RIU_HF_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN")
GITHUB_ENV_REFS = ("RIU_GITHUB_PAT", "GITHUB_TOKEN", "GH_TOKEN")
GITHUB_API = "https://api.github.com"
HF_WHOAMI = "https://huggingface.co/api/whoami-v2"
GITHUB_MCP = "https://api.githubcopilot.com/mcp/"
HF_ACCOUNT = "COMAND-CENTER-1"
MCP_PROTOCOL_VERSION = "2025-06-18"


class MissingCredential(RuntimeError):
    """Señala que ninguna referencia autorizada existe en runtime."""


@dataclass(frozen=True)
class ResolvedCredential:
    provider: str
    env_name: str
    value: str

    def public(self) -> dict[str, str]:
        return {"provider": self.provider, "env_name": self.env_name, "status": "AVAILABLE"}


def resolve_credential(
    provider: str,
    names: Iterable[str],
    env: Mapping[str, str] | None = None,
) -> ResolvedCredential:
    source = os.environ if env is None else env
    for name in names:
        value = source.get(name)
        if value:
            return ResolvedCredential(provider=provider, env_name=name, value=value)
    raise MissingCredential(f"{provider}: runtime credential missing")


def resolve_huggingface(env: Mapping[str, str] | None = None) -> ResolvedCredential:
    return resolve_credential("huggingface", HF_ENV_REFS, env)


def resolve_github(env: Mapping[str, str] | None = None) -> ResolvedCredential:
    return resolve_credential("github", GITHUB_ENV_REFS, env)


def _decode_json_or_sse(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="replace").strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {"value": value}
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            if line.startswith("data:"):
                payload = line[5:].strip()
                try:
                    value = json.loads(payload)
                    return value if isinstance(value, dict) else {"value": value}
                except json.JSONDecodeError:
                    continue
    raise RuntimeError("connectivity probe failed: non_json_response")


def _request_json(
    url: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    accept: str = "application/json",
    timeout: int = 15,
) -> tuple[dict, dict[str, str]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "User-Agent": "router-inteligente-universal/1",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            data = _decode_json_or_sse(response.read())
            safe_headers = {
                key.lower(): value
                for key, value in response.headers.items()
                if key.lower() in {"x-oauth-scopes", "x-accepted-oauth-scopes", "content-type"}
            }
            return data, safe_headers
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"connectivity probe failed: {type(exc).__name__}") from exc


def _json_get(url: str, token: str, *, accept: str = "application/json", timeout: int = 15) -> dict:
    return _request_json(url, token, accept=accept, timeout=timeout)[0]


def probe_github(repo: str, env: Mapping[str, str] | None = None) -> dict:
    cred = resolve_github(env)
    identity, identity_headers = _request_json(f"{GITHUB_API}/user", cred.value)
    repository, _ = _request_json(f"{GITHUB_API}/repos/{repo}", cred.value)
    permissions = repository.get("permissions") or {}
    repo_match = repository.get("full_name") == repo
    full_repo_access = bool(permissions.get("admin") and permissions.get("push") and permissions.get("pull"))
    return {
        "provider": "github",
        "credential_ref": cred.env_name,
        "login": identity.get("login"),
        "repo": repository.get("full_name"),
        "private": repository.get("private"),
        "repository_permissions": {
            "admin": bool(permissions.get("admin")),
            "push": bool(permissions.get("push")),
            "pull": bool(permissions.get("pull")),
            "maintain": bool(permissions.get("maintain")),
        },
        "oauth_scopes": identity_headers.get("x-oauth-scopes"),
        "full_repo_access": full_repo_access,
        "status": "PASS" if identity.get("login") and repo_match else "FAIL",
    }


def probe_huggingface(env: Mapping[str, str] | None = None) -> dict:
    cred = resolve_huggingface(env)
    identity = _json_get(HF_WHOAMI, cred.value)
    name = identity.get("name") or identity.get("fullname") or identity.get("user")
    auth = identity.get("auth") if isinstance(identity.get("auth"), dict) else {}
    access_token = auth.get("accessToken") if isinstance(auth.get("accessToken"), dict) else {}
    return {
        "provider": "huggingface",
        "credential_ref": cred.env_name,
        "identity": name,
        "expected_account": HF_ACCOUNT,
        "token_role": access_token.get("role"),
        "status": "PASS" if name else "FAIL",
    }


def mcp_github_descriptor(env: Mapping[str, str] | None = None) -> dict:
    cred = resolve_github(env)
    return {
        "provider": "anthropic_managed_agents",
        "resource": "github_repository",
        "mcp_url": GITHUB_MCP,
        "credential_ref": cred.env_name,
        "auth_boundary": "runtime_or_vault",
        "status": "CONFIGURED",
    }


def probe_github_mcp(env: Mapping[str, str] | None = None) -> dict:
    """Hace solo el handshake MCP initialize. No ejecuta herramientas mutantes."""
    cred = resolve_github(env)
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "router-inteligente-universal", "version": "1"},
        },
    }
    response, _ = _request_json(
        GITHUB_MCP,
        cred.value,
        method="POST",
        payload=request,
        accept="application/json, text/event-stream",
        timeout=20,
    )
    result = response.get("result") if isinstance(response, dict) else None
    return {
        "provider": "github_mcp",
        "credential_ref": cred.env_name,
        "mcp_url": GITHUB_MCP,
        "protocol_requested": MCP_PROTOCOL_VERSION,
        "server_info": result.get("serverInfo") if isinstance(result, dict) else None,
        "status": "PASS" if isinstance(result, dict) else "FAIL",
    }


def public_runtime_status(env: Mapping[str, str] | None = None) -> dict:
    """Devuelve solo nombres de referencias y estado, nunca valores secretos."""
    result: dict[str, dict[str, str]] = {}
    for provider, resolver in (("github", resolve_github), ("huggingface", resolve_huggingface)):
        try:
            result[provider] = resolver(env).public()
        except MissingCredential:
            result[provider] = {"provider": provider, "status": "MISSING"}
    result["mcp"] = {"provider": "github", "url": GITHUB_MCP, "status": "DECLARED"}
    return result
