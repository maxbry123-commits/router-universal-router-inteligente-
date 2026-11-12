"""test_cierre.py — Tests de integracion del cierre-v1 (C4-03).
Solo sondas de archivo/import/contrato; sin red, sin servidor levantado.
Ejecutar: python -m pytest engine/tests/test_cierre.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_memoria_status():
    from plugins.memoria.plugin import handle
    r = handle("status", {})
    assert r["status"] == "ok"
    assert "total_entries" in r


def test_memoria_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_MEMORIA_DIR", str(tmp_path))
    from plugins.memoria.plugin import handle
    s = handle("save", {"key": "t1", "data": {"x": 1}})
    assert s["status"] == "ok"
    l = handle("load", {"key": "t1"})
    assert l["status"] == "ok" and l["data"] == {"x": 1}
    q = handle("search", {"query": "t1"})
    assert q["status"] == "ok" and q["count"] >= 1


def test_memoria_key_traversal_rechazada(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_MEMORIA_DIR", str(tmp_path))
    from plugins.memoria.plugin import handle
    r = handle("save", {"key": "../escape", "data": {}})
    assert r["status"] == "degraded"


def test_swe_schema():
    from engine.swe_code_free_tool import handle
    r = handle("schema", {})
    assert r["status"] == "ok"
    assert r["tool"]["name"] == "swe_code_free"
    assert "issue" in r["tool"]["inputSchema"]["required"]


def test_swe_status_estructura():
    from engine.swe_code_free_tool import handle
    r = handle("status", {})
    assert r["status"] == "ok"
    assert isinstance(r["agent_present"], bool)
    assert isinstance(r["listo_para_run"], bool)


def test_swe_run_sin_issue_degraded():
    from engine.swe_code_free_tool import handle
    r = handle("run", {})
    assert r["status"] == "degraded"


def test_wiring_registry_parse():
    yaml = pytest.importorskip("yaml")
    p = ROOT / "connections" / "wiring_registry.yaml"
    assert p.is_file(), "falta connections/wiring_registry.yaml (C2-01)"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert len(data.get("services", {})) >= 10


@pytest.mark.parametrize("panel,marca", [
    ("loop-panel.html", 'panel:"loop"'),
    ("watchdog-panel.html", 'panel:"watchdog"'),
    ("cola-panel.html", 'panel:"cola"'),
])
def test_paneles_existen(panel, marca):
    p = ROOT / "chat-router" / "chat" / "ui" / panel
    assert p.is_file(), f"falta {panel} (C1-0x)"
    txt = p.read_text(encoding="utf-8")
    assert "capa:ready" in txt
    assert marca in txt
    assert "ALLOWED" in txt


def test_orchestrator_stages():
    from engine.orchestrator import STAGES
    assert len(STAGES) == 9
    assert [n for n, _ in STAGES] == ["F1", "F2", "F3", "F4", "F5",
                                      "F6", "F7", "F8", "F9"]


def test_probe_sondas_importable():
    import engine.probe_sondas as ps
    assert callable(ps.run_probes)
