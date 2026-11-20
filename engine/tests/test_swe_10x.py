"""test_swe_10x.py — Tests del parche SWE 10x (S5). Sin red, sin servidor."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIFF_OK = "--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-a\n+b\n"


def test_sandbox_binario_permitido():
    from engine.swe_sandbox import run
    r = run(["git", "--version"])
    assert r["status"] == "ok" and r["rc"] == 0


def test_sandbox_binario_prohibido():
    from engine.swe_sandbox import run
    r = run(["curl", "http://x"])
    assert r["status"] == "degraded" and "allowlist" in r["reason"]


def test_sandbox_token_prohibido():
    from engine.swe_sandbox import run
    r = run(["git", "status", "&&", "rm", "-rf", "/"])
    assert r["status"] == "degraded"


def test_sandbox_argv_vacio():
    from engine.swe_sandbox import run
    assert run([])["status"] == "degraded"


def test_extract_diff_fence():
    from engine.swe_patch import extract_diff
    d = extract_diff("texto\n```diff\n" + DIFF_OK + "```\nfin")
    assert d.startswith("--- a/f.py")


def test_extract_diff_sin_diff():
    from engine.swe_patch import extract_diff
    assert extract_diff("solo prose, sin diff") == ""


def test_check_diff_vacio():
    from engine.swe_patch import check
    assert check("")["status"] == "degraded"


def test_apply_sin_aprobacion():
    from engine.swe_patch import apply
    r = apply(DIFF_OK)
    assert r["status"] == "degraded"


def test_touched_y_tests_for():
    from engine.swe_patch import touched_files, tests_for
    assert touched_files(DIFF_OK) == ["f.py"]
    assert isinstance(tests_for(DIFF_OK), list)


def test_keywords_determinista():
    from engine.swe_context import keywords
    k = keywords("fix the login bug in authentication module")
    assert "login" in k and "the" not in k and "fix" not in k
    assert keywords("fix the login bug") == keywords("fix the login bug")


def test_issue_id_estable():
    from engine.swe_context import issue_id
    assert issue_id("abc") == issue_id("abc")
    assert issue_id("abc") != issue_id("abd")


def test_liga_no_sobrescribe(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_MEMORIA_DIR", str(tmp_path))
    from engine.swe_context import save_liga
    a = save_liga("issue x", {"veredicto": "uno"})
    b = save_liga("issue x", {"veredicto": "dos"})
    assert a and b and a != b


def test_tool_schema():
    from engine.swe_code_free_tool import handle
    r = handle("schema", {})
    assert r["tool"]["name"] == "swe_code_free"
    assert "approved_by" in r["tool"]["inputSchema"]["properties"]


def test_tool_run_sin_issue():
    from engine.swe_code_free_tool import handle
    r = handle("run", {})
    assert r["status"] == "degraded" and r["reason_code"] == "sin_issue"


def test_tool_verified_sin_gate():
    from engine.swe_code_free_tool import handle
    r = handle("run_verified", {"issue": "x"})
    assert r["status"] == "degraded" and r["reason_code"] == "gate_rechazado"


def test_tool_status_estructura():
    from engine.swe_code_free_tool import handle
    r = handle("status", {})
    assert r["status"] == "ok" and r["version"] == "2.0.0"
    assert isinstance(r["listo_para_run"], bool)
