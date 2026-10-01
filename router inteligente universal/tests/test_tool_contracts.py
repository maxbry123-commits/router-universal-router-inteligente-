"""Tests tool_contracts (T11-H): rutas reales verificadas, receipt, sin bypass."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import tool_contracts as tc


def test_todas_las_tools_apuntan_a_ruta_real():
    reg = tc.ToolRegistry()
    for name in ("download_extract", "search", "fables_plug", "rdc_download", "deepseek_harness"):
        assert reg.contract(name)["status"] == "VERIFIED", name


def test_invoke_produce_receipt():
    reg = tc.ToolRegistry()
    r = reg.invoke("search", "hermes", {"q": "x"})
    assert r["receipt"].startswith("rcpt-")
    assert r["caller"] == "hermes" and r["status"] == "DISPATCHED"
    assert len(r["args_sha256"]) == 64


def test_permisos_minimos_y_sin_bypass_sheriff():
    reg = tc.ToolRegistry()
    with pytest.raises(tc.ToolContractError, match="CALLER_UNAUTHORIZED"):
        reg.invoke("search", "random_worker", {})
    with pytest.raises(tc.ToolContractError, match="WRITE_SCOPE_DENIED"):
        reg.invoke("download_extract", "openclaw", {}, write_scope=("/etc/x",))
    r = reg.invoke("download_extract", "openclaw", {},
                   write_scope=("router inteligente universal/Componente open soure router inteligente universal/y",))
    assert r["status"] == "DISPATCHED"


def test_tool_desconocida_y_bloqueada(tmp_path):
    reg = tc.ToolRegistry()
    with pytest.raises(tc.ToolContractError, match="TOOL_UNKNOWN"):
        reg.invoke("inventada", "hermes", {})
    reg2 = tc.ToolRegistry(root=tmp_path)  # engines no existen -> BLOCKED
    assert all(v == "BLOCKED" for v in reg2.status.values())
    with pytest.raises(tc.ToolContractError, match="TOOL_BLOCKED"):
        reg2.invoke("search", "hermes", {})
