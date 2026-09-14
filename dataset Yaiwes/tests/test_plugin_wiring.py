from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "plugin" / "yaiwes_dataset_plugin.py"
MANIFEST_PATH = ROOT / "plugin" / "ficha_yaiwes_dataset_v2.json"

spec = importlib.util.spec_from_file_location("yaiwes_dataset_plugin", PLUGIN_PATH)
assert spec and spec.loader
plugin_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin_mod)


def test_plugin_manifest_shadow_shape():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["artifact_id"] == "yaiwes.dataset.router"
    assert manifest["estado"] == "testing"
    assert plugin_mod.validate_manifest_shape(manifest) == []


def test_plugin_health_exact_dataset():
    health = plugin_mod.DatasetYaiwesPlugin().health()
    assert health["ok"]
    assert health["methods"] == 107
    assert health["indexed_records"] == 1139


def test_plugin_tier_a_retrieve_y26():
    rows = plugin_mod.DatasetYaiwesPlugin().retrieve("Y26")
    assert len(rows) == 20
    assert all(r["method_id"] == "Y26" for r in rows)


def test_plugin_shadow_passes():
    report = plugin_mod.shadow_validate()
    assert report.passed, report
    assert all(report.checks.values())


def test_plugin_activation_fail_closed_without_signature():
    result = plugin_mod.activation_preflight()
    assert not result["ready"]
    assert "tribunal_approval_required" in result["blockers"]
    assert "signed_ficha_required" in result["blockers"]


def test_plugin_activation_preflight_ready_only_with_approval_and_signature():
    result = plugin_mod.activation_preflight("YAIWES-TRIBUNAL-SIGNED-KEY", tribunal_approved=True)
    assert result["ready"]
    assert result["manifest"]["estado"] == "active"
    assert result["manifest"]["firma"]["gpg_key_id"] == "YAIWES-TRIBUNAL-SIGNED-KEY"
