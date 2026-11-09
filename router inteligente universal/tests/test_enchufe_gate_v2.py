import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _gate_module():
    path = Path(__file__).parents[1] / "red" / "enchufe_gate.py"
    spec = spec_from_file_location("router_enchufe_gate_v2", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_v2_contract():
    return {
        "artifact_id": "agent.worker.test",
        "version": "2.0.0",
        "estado": "testing",
        "categoria": "pipeline",
        "etapa": "P",
        "contrato": {
            "rol": "service",
            "consume": {"datatype": {"family": "json", "type": "task", "version": 1}},
            "expone": {"datatype": {"family": "json", "type": "result", "version": 1}},
        },
        "ejecucion": {
            "kind": "agent",
            "transport": "http",
            "runtime_type": "agent",
            "llm_ratio": 0.05,
            "idempotente": False,
            "entry_point": "agent.run",
            "max_steps": 8,
            "allowed_actions": ["read", "route"],
        },
        "seguridad": {
            "sandbox": "container",
            "permisos": [],
            "limites": {"timeout_ms": 1000, "deadline_ms": 2000},
        },
        "firma": {"gpg_key_id": "PENDIENTE"},
    }


def test_gate_accepts_v2_agent_through_shared_validator():
    gate = _gate_module()
    verdict = gate.validar_contrato_conexion(_valid_v2_contract())
    assert verdict.valido is True, verdict.errores


def test_gate_rejects_v2_semantic_violation_fail_closed():
    gate = _gate_module()
    contract = _valid_v2_contract()
    contract["categoria"] = "acelerador"
    contract["etapa"] = "P"
    verdict = gate.validar_contrato_conexion(contract)
    assert verdict.valido is False
    assert "v2:V03_acelerador_etapa_A" in verdict.errores


def test_gate_keeps_v15_public_signature():
    gate = _gate_module()
    contract = {
        "artifact_id": "ai.llm.compat",
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
    verdict = gate.validar_contrato_conexion(contract)
    assert verdict.valido is True
    assert hasattr(verdict, "errores")
