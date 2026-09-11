from __future__ import annotations
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = str(ROOT / "integration")
if INTEGRATION not in sys.path:
    sys.path.insert(0, INTEGRATION)

import connectivity_runtime as cr  # noqa: E402


def test_missing_credentials_fail_closed() -> None:
    env = {}
    for resolver in (cr.resolve_github, cr.resolve_huggingface):
        try:
            resolver(env)
        except cr.MissingCredential:
            pass
        else:
            raise AssertionError("missing credential must fail closed")


def test_runtime_resolution_uses_only_authorized_names_and_never_serializes_values() -> None:
    env = {
        "RIU_GITHUB_PAT": "github-secret-value",
        "RIU_HF_TOKEN": "hf-secret-value",
        "UNRELATED_TOKEN": "must-not-be-used",
    }
    gh = cr.resolve_github(env)
    hf = cr.resolve_huggingface(env)
    assert gh.env_name == "RIU_GITHUB_PAT"
    assert hf.env_name == "RIU_HF_TOKEN"
    status = cr.public_runtime_status(env)
    payload = json.dumps(status)
    assert "github-secret-value" not in payload
    assert "hf-secret-value" not in payload
    assert "must-not-be-used" not in payload
    assert status["github"]["status"] == "AVAILABLE"
    assert status["huggingface"]["status"] == "AVAILABLE"


def test_mcp_descriptor_uses_github_runtime_reference_without_secret_value() -> None:
    env = {"GITHUB_TOKEN": "secret"}
    descriptor = cr.mcp_github_descriptor(env)
    assert descriptor["mcp_url"] == cr.GITHUB_MCP
    assert descriptor["resource"] == "github_repository"
    assert descriptor["credential_ref"] == "GITHUB_TOKEN"
    assert "secret" not in json.dumps(descriptor)


def test_decode_json_or_sse() -> None:
    payload = b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"serverInfo":{"name":"github"}}}\n\n'
    body = cr._decode_json_or_sse(payload)
    assert body["result"]["serverInfo"]["name"] == "github"


def test_github_probe_reports_repo_permissions_without_secret() -> None:
    env = {"RIU_GITHUB_PAT": "top-secret"}
    responses = [
        ({"login": "maxbry123-commits"}, {"x-oauth-scopes": "repo"}),
        ({"full_name": "maxbry123-commits/frontend", "private": False, "permissions": {"admin": True, "push": True, "pull": True, "maintain": True}}, {}),
    ]
    with patch.object(cr, "_request_json", side_effect=responses):
        result = cr.probe_github("maxbry123-commits/frontend", env)
    assert result["status"] == "PASS"
    assert result["full_repo_access"] is True
    assert result["oauth_scopes"] == "repo"
    assert "top-secret" not in json.dumps(result)


def test_huggingface_probe_reports_role_without_secret() -> None:
    env = {"HF_TOKEN": "hf-secret"}
    identity = {"name": "COMAND-CENTER-1", "auth": {"accessToken": {"role": "write"}}}
    with patch.object(cr, "_json_get", return_value=identity):
        result = cr.probe_huggingface(env)
    assert result["status"] == "PASS"
    assert result["identity"] == "COMAND-CENTER-1"
    assert result["token_role"] == "write"
    assert "hf-secret" not in json.dumps(result)


def test_github_mcp_initialize_probe_is_read_only_and_hides_secret() -> None:
    env = {"GH_TOKEN": "gh-secret"}
    response = {"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {"name": "github-mcp"}}}
    with patch.object(cr, "_request_json", return_value=(response, {})) as mocked:
        result = cr.probe_github_mcp(env)
    assert result["status"] == "PASS"
    assert result["server_info"]["name"] == "github-mcp"
    assert "gh-secret" not in json.dumps(result)
    kwargs = mocked.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["payload"]["method"] == "initialize"
