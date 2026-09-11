from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = str(ROOT / "integration")
if INTEGRATION not in sys.path:
    sys.path.insert(0, INTEGRATION)

from connectivity_runtime import (  # noqa: E402
    GITHUB_MCP,
    MissingCredential,
    mcp_github_descriptor,
    public_runtime_status,
    resolve_github,
    resolve_huggingface,
)


def test_missing_credentials_fail_closed() -> None:
    env = {}
    for resolver in (resolve_github, resolve_huggingface):
        try:
            resolver(env)
        except MissingCredential:
            pass
        else:
            raise AssertionError("missing credential must fail closed")


def test_runtime_resolution_uses_only_authorized_names_and_never_serializes_values() -> None:
    env = {
        "RIU_GITHUB_PAT": "github-secret-value",
        "RIU_HF_TOKEN": "hf-secret-value",
        "UNRELATED_TOKEN": "must-not-be-used",
    }
    gh = resolve_github(env)
    hf = resolve_huggingface(env)
    assert gh.env_name == "RIU_GITHUB_PAT"
    assert hf.env_name == "RIU_HF_TOKEN"
    status = public_runtime_status(env)
    payload = json.dumps(status)
    assert "github-secret-value" not in payload
    assert "hf-secret-value" not in payload
    assert "must-not-be-used" not in payload
    assert status["github"]["status"] == "AVAILABLE"
    assert status["huggingface"]["status"] == "AVAILABLE"


def test_mcp_descriptor_uses_github_runtime_reference_without_secret_value() -> None:
    env = {"GITHUB_TOKEN": "secret"}
    descriptor = mcp_github_descriptor(env)
    assert descriptor["mcp_url"] == GITHUB_MCP
    assert descriptor["resource"] == "github_repository"
    assert descriptor["credential_ref"] == "GITHUB_TOKEN"
    assert "secret" not in json.dumps(descriptor)
