"""Multi-account GitHub tools for the chat MVP (stdlib only, REST).

Accounts are labels mapped to ENV VAR NAMES (RIU_GITHUB_ACCOUNTS='{"cuenta-1":"GITHUB_TOKEN_1"}'), or a
per-request BYOK token. Tokens are never returned, logged or stored.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Mapping

API = "https://api.github.com"
MAX_FILE_BYTES = 200_000
DEFAULT_ENV_TOKENS = ("GITHUB_TOKEN_1", "GITHUB_TOKEN_2", "GITHUB_TOKEN_3", "RIU_GITHUB_TOKEN")


class GitHubError(RuntimeError):
    def __init__(self, status: int | str, message: str) -> None:
        super().__init__(f"GITHUB_ERROR:{status}:{message}")
        self.status = status


def accounts_from_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ if env is None else env
    raw = env.get("RIU_GITHUB_ACCOUNTS", "")
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
    return {name: name for name in DEFAULT_ENV_TOKENS if env.get(name)}


def token_for(account: str, byok: str | None = None, env: Mapping[str, str] | None = None) -> str | None:
    if byok:
        return byok
    env = os.environ if env is None else env
    var = accounts_from_env(env).get(account)
    return env.get(var) if var else None


def _http(method: str, url: str, token: str, body: dict[str, Any] | None) -> tuple[int, Any]:
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "riu-chat-mvp"}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310 fixed https API host
            return resp.status, json.loads(resp.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as exc:
        return exc.code, {"message": exc.read().decode("utf-8", errors="replace")[:160]}
    except Exception as exc:  # noqa: BLE001
        raise GitHubError(type(exc).__name__, "request failed") from exc


def _call(http: Callable[..., tuple[int, Any]] | None, method: str, path: str, token: str, body: dict[str, Any] | None = None) -> Any:
    status, data = (http or _http)(method, API + path, token, body)
    if status >= 400:
        raise GitHubError(status, str((data or {}).get("message", ""))[:120])
    return data


def whoami(token: str, http: Callable[..., tuple[int, Any]] | None = None) -> str:
    return str(_call(http, "GET", "/user", token).get("login", ""))


def list_repos(token: str, http: Callable[..., tuple[int, Any]] | None = None, per_page: int = 50) -> list[dict[str, Any]]:
    data = _call(http, "GET", f"/user/repos?per_page={per_page}&sort=updated", token)
    return [{"full_name": r["full_name"], "private": r["private"], "default_branch": r.get("default_branch", "main")} for r in data]


def get_file(token: str, repo: str, path: str, ref: str | None = None, http: Callable[..., tuple[int, Any]] | None = None) -> dict[str, Any]:
    q = f"?ref={urllib.parse.quote(ref)}" if ref else ""
    data = _call(http, "GET", f"/repos/{repo}/contents/{urllib.parse.quote(path)}{q}", token)
    if isinstance(data, list) or data.get("type") != "file":
        raise GitHubError("NOT_A_FILE", path)
    if data.get("size", 0) > MAX_FILE_BYTES:
        raise GitHubError("FILE_TOO_LARGE", f"{data.get('size')} bytes")
    text = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    return {"path": data["path"], "sha": data["sha"], "size": data["size"], "text": text}


def put_file(token: str, repo: str, path: str, text: str, message: str, branch: str | None = None,
             http: Callable[..., tuple[int, Any]] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"message": message, "content": base64.b64encode(text.encode("utf-8")).decode("ascii")}
    if branch:
        body["branch"] = branch
    try:
        body["sha"] = get_file(token, repo, path, branch, http)["sha"]
    except GitHubError as exc:
        if exc.status != 404:
            raise
    data = _call(http, "PUT", f"/repos/{repo}/contents/{urllib.parse.quote(path)}", token, body)
    return {"path": data["content"]["path"], "content_sha": data["content"]["sha"], "commit": data["commit"]["sha"]}
