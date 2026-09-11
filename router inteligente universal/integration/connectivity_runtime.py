"""Runtime central de conectividad del Router Inteligente Universal.

No persiste credenciales. Solo resuelve referencias de entorno en runtime y
aplica fail-closed antes de cualquier llamada externa.
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


def _json_get(url: str, token: str, *, accept: str = "application/json", timeout: int = 15) -> dict:
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "User-Agent": "router-inteligente-universal/1",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"connectivity probe failed: {type(exc).__name__}") from exc


def probe_github(repo: str, env: Mapping[str, str] | None = None) -> dict:
    cred = resolve_github(env)
    identity = _json_get(f"{GITHUB_API}/user", cred.value)
    repository = _json_get(f"{GITHUB_API}/repos/{repo}", cred.value)
    return {
        "provider": "github",
        "credential_ref": cred.env_name,
        "login": identity.get("login"),
        "repo": repository.get("full_name"),
        "private": repository.get("private"),
        "status": "PASS" if identity.get("login") and repository.get("full_name") == repo else "FAIL",
    }


def probe_huggingface(env: Mapping[str, str] | None = None) -> dict:
    cred = resolve_huggingface(env)
    identity = _json_get(HF_WHOAMI, cred.value)
    name = identity.get("name") or identity.get("fullname") or identity.get("user")
    return {
        "provider": "huggingface",
        "credential_ref": cred.env_name,
        "identity": name,
        "expected_account": HF_ACCOUNT,
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
