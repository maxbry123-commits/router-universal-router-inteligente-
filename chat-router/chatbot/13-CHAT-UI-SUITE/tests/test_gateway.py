import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
os.environ["SIMULADO"] = "1"

import gateway


def test_models_exponen_solo_hermes_y_openclaw():
    ids = [m["id"] for m in gateway.list_models()["data"]]
    assert ids == ["yaiwes/hermes", "yaiwes/openclaw"]


def test_hermes_usa_puente_existente():
    out = gateway.dispatch_chat({"model": "yaiwes/hermes", "messages": [{"role": "user", "content": "plan"}]})
    assert out["model"] == "yaiwes/hermes"
    assert "planner_supervisor" in out["choices"][0]["message"]["content"]


def test_openclaw_usa_puente_existente():
    out = gateway.dispatch_chat({"model": "yaiwes/openclaw", "messages": [{"role": "user", "content": "vigila"}]})
    assert out["model"] == "yaiwes/openclaw"
    assert "guardian_supervisor" in out["choices"][0]["message"]["content"]


def test_modelo_desconocido_falla_cerrado():
    try:
        gateway.dispatch_chat({"model": "otro", "messages": [{"role": "user", "content": "x"}]})
    except ValueError as exc:
        assert "hermes" in str(exc) and "openclaw" in str(exc)
    else:
        raise AssertionError("debía fallar")
