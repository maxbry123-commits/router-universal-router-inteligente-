"""Propagate approved runtime secrets to the selected YAIWES repositories.

Never prints secret values. Requires RIU_GITHUB_PAT with repository Secrets write
permission for every target repository.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

from nacl import encoding, public

OWNER = "maxbry123-commits"
REPOSITORIES = [
    "frontend",
    "agentes",
    "Agentes-motores-Wordflow-YAIWES",
    "osquestador-auditor",
    "Maxbry-AGI",
    "nct-core",
    "TAREA-1",
    "router-universal-router-inteligente-",
]

# Only these explicitly approved credentials can be propagated.
SECRET_NAMES = [
    "RIU_GITHUB_PAT",
    "RIU_HF_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CODEX_AUTH_JSON_ACCOUNT_1",
    "CODEX_AUTH_JSON_ACCOUNT_2",
]


def request_json(method: str, url: str, token: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "riu-secret-propagator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def encrypt(public_key_b64: str, value: str) -> str:
    key = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(key)
    return base64.b64encode(sealed.encrypt(value.encode())).decode()


def set_secret(repo: str, name: str, value: str, auth_token: str) -> None:
    base = f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets"
    key = request_json("GET", base + "/public-key", auth_token)
    request_json(
        "PUT",
        base + f"/{name}",
        auth_token,
        {"encrypted_value": encrypt(key["key"], value), "key_id": key["key_id"]},
    )


def main() -> int:
    auth = os.environ.get("RIU_GITHUB_PAT", "").strip()
    if not auth:
        print("BOOTSTRAP_BLOCKED=RIU_GITHUB_PAT_ABSENT")
        return 2

    available = {name: os.environ.get(name, "") for name in SECRET_NAMES}
    present = [name for name, value in available.items() if value]
    print("SECRET_SET_PRESENT=" + ",".join(present))
    print("TARGET_REPOSITORIES=" + str(len(REPOSITORIES)))

    failures = []
    for repo in REPOSITORIES:
        for name in present:
            try:
                set_secret(repo, name, available[name], auth)
                print(f"SECRET_PROPAGATED repo={repo} name={name} status=PASS")
            except urllib.error.HTTPError as exc:
                print(f"SECRET_PROPAGATED repo={repo} name={name} status=FAIL http={exc.code}")
                failures.append((repo, name, exc.code))
            except Exception as exc:  # never print exception body; it can include sensitive payloads
                print(f"SECRET_PROPAGATED repo={repo} name={name} status=FAIL type={type(exc).__name__}")
                failures.append((repo, name, type(exc).__name__))

    if failures:
        print("SECRET_PROPAGATION=FAIL")
        return 1
    print("SECRET_PROPAGATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
