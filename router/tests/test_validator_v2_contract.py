from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "enchufe" / "validator_v2.py"
spec = importlib.util.spec_from_file_location("validator_v2", MODULE_PATH)
assert spec and spec.loader
validator_v2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator_v2
spec.loader.exec_module(validator_v2)


def ficha_base() -> dict:
    return {
        "artifact_id": "router.test",
        "version": "1.5.0",
        "estado": "testing",
        "contrato": {"rol": "service"},
        "ejecucion": {
            "kind": "code",
            "transport": "importlib",
            "runtime_type": "compute",
            "llm_ratio": 0.0,
            "idempotente": True,
        },
        "seguridad": {
            "sandbox": "process",
            "permisos": [],
            "limites": {"timeout_ms": 1000, "deadline_ms": 1000},
        },
    }


def test_v15_valida_bajo_v20() -> None:
    resultado = validator_v2.validar(ficha_base())
    assert resultado.valido, resultado.errores
    assert resultado.ficha_normalizada["categoria"] == "pipeline"
    assert resultado.ficha_normalizada["etapa"] == "P"


def test_acelerador_fuera_de_A_falla() -> None:
    ficha = ficha_base()
    ficha["categoria"] = "acelerador"
    ficha["etapa"] = "P"
    resultado = validator_v2.validar(ficha)
    assert not resultado.valido
    assert "V03_acelerador_etapa_A" in resultado.errores


def test_repetible_sin_idempotencia_falla() -> None:
    ficha = ficha_base()
    ficha["repeticion"] = {"max": 2, "condicion": "si_falla_verificacion"}
    ficha["ejecucion"]["idempotente"] = False
    resultado = validator_v2.validar(ficha)
    assert not resultado.valido
    assert "V09_repetible_debe_ser_idempotente" in resultado.errores


def test_agent_sin_whitelist_falla() -> None:
    ficha = ficha_base()
    ficha["ejecucion"].update({"kind": "agent", "runtime_type": "agent"})
    resultado = validator_v2.validar(ficha)
    assert not resultado.valido
    assert "V14_agent_requiere_max_steps_y_whitelist" in resultado.errores


def test_presupuesto_negativo_falla() -> None:
    ficha = ficha_base()
    ficha["presupuesto"] = {"n0": {"max_ms": -1, "max_tokens": 100}}
    resultado = validator_v2.validar(ficha)
    assert not resultado.valido
    assert "V12_presupuesto_positivo:n0" in resultado.errores


def test_compatibles_datatype() -> None:
    datatype = {"family": "router", "type": "payload", "version": 2}
    a = {"contrato": {"expone": {"datatype": copy.deepcopy(datatype)}}}
    b = {"contrato": {"consume": {"datatype": copy.deepcopy(datatype)}}}
    assert validator_v2.compatibles(a, b)
    b["contrato"]["consume"]["datatype"]["version"] = 3
    assert not validator_v2.compatibles(a, b)
