"""T10 — pruebas de plan/rollback y compare-and-swap sin hacer PATCH externo."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).parents[1]
sys.path.insert(0, str(BASE))
spec = importlib.util.spec_from_file_location("yaiwes_autofree_bloqueos", BASE / "bloqueos.py")
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)


def test_plan_preserva_bloqueados_anteriores_y_es_idempotente():
    assert block.proposed(["otro", "opencode"], ["opencode"]) == ["otro", "opencode"]
    assert block.proposed(["otro", "opencode"], ["felo-web"]) == [
        "otro", "opencode", "felo-web"
    ]


def test_rollback_elimina_solo_seleccionado():
    assert block.proposed(["otro", "opencode", "felo-web"],
                          ["opencode"], undo=True) == ["otro", "felo-web"]


def test_dry_run_jamas_parchea():
    with patch.object(block, "_request",
                      return_value=(200, {"settingsRevision": 3,
                                          "blockedProviders": ["otro"]})) as req:
        assert block.main(["--proveedor", "opencode"]) == 0
    assert req.call_count == 1
    assert req.call_args[0][0].endswith("/api/settings")


def test_apply_usa_compare_and_swap():
    with patch.object(block, "_request",
                      side_effect=[(200, {"settingsRevision": 7,
                                          "blockedProviders": ["otro"]}),
                                   (200, {})]) as req:
        assert block.main(["--proveedor", "opencode", "--aplicar"]) == 0
    assert req.call_count == 2
    assert req.call_args[1]["revision"] == 7
    assert req.call_args[1]["data"] == {
        "blockedProviders": ["otro", "opencode"], "expectedRevision": 7
    }


def test_conflicto_revision_falla_cerrado():
    with patch.object(block, "_request",
                      side_effect=[(200, {"settingsRevision": 7,
                                          "blockedProviders": []}),
                                   (409, {})]) as req:
        assert block.main(["--proveedor", "opencode", "--aplicar"]) == 3
    assert req.call_count == 2


def test_proveedor_invalidado():
    import pytest
    with pytest.raises(SystemExit):
        block.main(["--proveedor", "http://example.com"])
