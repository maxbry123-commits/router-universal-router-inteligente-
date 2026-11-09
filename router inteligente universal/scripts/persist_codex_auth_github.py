"""Persist Codex ChatGPT subscription credentials as GitHub Actions secrets.

The auth payload is never printed, committed, uploaded as an artifact, or stored in
Hugging Face. A bootstrap RIU_GITHUB_PAT with Actions Secrets write permission is
required to encrypt and write the secret to the selected repositories.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from propagate_actions_secrets import REPOSITORIES, set_secret


def validated_auth(raw: str) -> str:
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("auth_mode") != "chatgpt":
        raise ValueError("Expected ChatGPT subscription auth")
    tokens = data.get("tokens")
    if not isinstance(tokens, dict) or not all(
        isinstance(tokens.get(key), str) and tokens[key].strip()
        for key in ("access_token", "refresh_token", "id_token")
    ):
        raise ValueError("Incomplete ChatGPT subscription credentials")
    if data.get("OPENAI_API_KEY"):
        raise ValueError("API-key auth is not accepted in this subscription workflow")
    return json.dumps(data, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True, choices=("1", "2"))
    args = parser.parse_args()

    bootstrap = os.environ.get("RIU_GITHUB_PAT", "").strip()
    if not bootstrap:
        print("BOOTSTRAP_BLOCKED=RIU_GITHUB_PAT_ABSENT")
        return 2

    auth_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
    try:
        value = validated_auth(auth_path.read_text())
    except Exception as exc:
        print("CODEX_AUTH_VALIDATION=FAIL type=" + type(exc).__name__)
        return 1

    name = "CODEX_AUTH_JSON_ACCOUNT_" + args.account
    failures = 0
    for repo in REPOSITORIES:
        try:
            set_secret(repo, name, value, bootstrap)
            print(f"CODEX_SECRET repo={repo} name={name} status=PASS")
        except Exception as exc:
            print(f"CODEX_SECRET repo={repo} name={name} status=FAIL type={type(exc).__name__}")
            failures += 1
    if failures:
        print("CODEX_AUTH_PROPAGATION=FAIL")
        return 1
    print("CODEX_AUTH_PROPAGATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
