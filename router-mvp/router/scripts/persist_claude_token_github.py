"""Extract a Claude setup-token from a private local session log and persist it.

The token is never printed. The session log must remain runner-local and should be
shredded by the caller after this program exits.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

from propagate_actions_secrets import REPOSITORIES, set_secret

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
TOKEN = re.compile(r"sk-ant-oat01-[A-Za-z0-9_-]{20,}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session_log")
    args = parser.parse_args()

    bootstrap = os.environ.get("RIU_GITHUB_PAT", "").strip()
    if not bootstrap:
        print("BOOTSTRAP_BLOCKED=RIU_GITHUB_PAT_ABSENT")
        return 2

    raw = Path(args.session_log).read_text(errors="ignore")
    clean = ANSI.sub("", raw)
    match = TOKEN.search(clean)
    if not match:
        print("CLAUDE_SETUP_TOKEN_CAPTURE=FAIL")
        return 1
    token = match.group(0)

    failures = 0
    for repo in REPOSITORIES:
        try:
            set_secret(repo, "CLAUDE_CODE_OAUTH_TOKEN", token, bootstrap)
            print(f"CLAUDE_SECRET repo={repo} status=PASS")
        except Exception as exc:
            print(f"CLAUDE_SECRET repo={repo} status=FAIL type={type(exc).__name__}")
            failures += 1
    if failures:
        print("CLAUDE_AUTH_PROPAGATION=FAIL")
        return 1
    print("CLAUDE_AUTH_PROPAGATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
