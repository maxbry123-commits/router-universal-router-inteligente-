import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _gate_module():
    path = Path(__file__).parents[1] / "red" / "enchufe_gate.py"
    spec = spec_from_file_location("router_enchufe_gate", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_contract():
    return {
        "artifact_id": "ai.llm.test",
        "estado": "active",
        "contract_hash": "sha256:" + "a" * 64,
        "ejecucion": {"kind": "llm", "transport": "http"},
        "seguridad": {
            "sandbox": "container",
            "limites": {"timeout_ms": 1000, "deadline_ms": 2000},
        },
        "contrato": {
            "rol": "transform",
            "consume": {"datatype": {"family": "text", "type": "prompt", "version": 1}},
            "expone": {"datatype": {"family": "text", "type": "response", "version": 1}},
        },
    }


def test_gate_accepts_valid_v15_contract():
    gate = _gate_module()
    assert gate.validar_contrato_conexion(_valid_contract()).valido is True


def test_gate_rejects_invalid_active_hash():
    gate = _gate_module()
    contract = _valid_contract()
    contract["contract_hash"] = "invalid"
    verdict = gate.validar_contrato_conexion(contract)
    assert verdict.valido is False
    assert "active_requiere_hash_real" in verdict.errores
