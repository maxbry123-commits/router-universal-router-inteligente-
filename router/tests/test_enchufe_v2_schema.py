from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "domain" / "schemas" / "enchufe_v2.py"

spec = importlib.util.spec_from_file_location("enchufe_v2_schema", SCHEMA)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)
EnchufeV2 = module.EnchufeV2


def ficha_minima() -> dict:
    return {
        "artifact_id": "router.test",
        "version": "1.0.0",
        "estado": "testing",
        "contrato": {"rol": "service"},
        "ejecucion": {
            "kind": "code",
            "transport": "importlib",
            "runtime_type": "compute",
        },
        "seguridad": {
            "sandbox": "process",
            "limites": {"timeout_ms": 1000},
        },
    }


def test_v15_compatible_defaults_are_applied() -> None:
    ficha = EnchufeV2.model_validate(ficha_minima())
    assert ficha.categoria == "pipeline"
    assert ficha.etapa == "P"
    assert ficha.firma.gpg_key_id == "PENDIENTE"
    assert set(ficha.perfiles) == {f"n{i}" for i in range(6)}
    assert ficha.repeticion.max == 1


def test_schema_rejects_invalid_patterns_and_enums() -> None:
    bad = ficha_minima()
    bad["artifact_id"] = "INVALID"
    bad["ejecucion"]["kind"] = "unknown"
    with pytest.raises(ValidationError):
        EnchufeV2.model_validate(bad)


def test_alias_and_contract_shape_round_trip() -> None:
    data = ficha_minima()
    data["contrato"] = {
        "rol": "transform",
        "consume": {
            "datatype": {"family": "json", "type": "task", "version": 2}
        },
        "expone": {
            "datatype": {"family": "json", "type": "result", "version": 2}
        },
    }
    ficha = EnchufeV2.model_validate(data)
    dumped = ficha.model_dump(by_alias=True)
    assert dumped["contrato"]["consume"]["datatype"]["type"] == "task"
    assert dumped["contrato"]["expone"]["datatype"]["type"] == "result"


def test_repetition_and_limits_are_fail_closed_structurally() -> None:
    bad = ficha_minima()
    bad["repeticion"] = {"max": 0}
    bad["seguridad"]["limites"]["timeout_ms"] = 0
    with pytest.raises(ValidationError):
        EnchufeV2.model_validate(bad)
