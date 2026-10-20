"""GitHub public adapter for a real no-secret E2E destination."""
from __future__ import annotations
import sys
from pathlib import Path

RED = Path(__file__).resolve().parents[1] / "red"
if str(RED) not in sys.path:
    sys.path.insert(0, str(RED))

from conectores import ConectorGitHub  # noqa: E402


def build_github_public_adapter(repo: str) -> ConectorGitHub:
    """Reuse the canonical GitHub connector; public GET works without a token."""
    return ConectorGitHub("github.public", repo)
