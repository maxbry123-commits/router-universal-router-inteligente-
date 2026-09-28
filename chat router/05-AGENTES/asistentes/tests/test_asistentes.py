import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
os.environ["SIMULADO"] = "1"

import heartbeat
import puente_asistentes


def test_preguntar_hermes_y_openclaw_simulado(monkeypatch):
    def no_red(*args, **kwargs):
        raise AssertionError("SIMULADO no debe usar red")
    monkeypatch.setattr(puente_asistentes.request, "urlopen", no_red)
    assert "planner_supervisor" in puente_asistentes.preguntar("hermes", "plan")
    assert "guardian_supervisor" in puente_asistentes.preguntar("openclaw", "vigila")


def test_emit_simulado_no_escribe(tmp_path, monkeypatch):
    monkeypatch.setattr(puente_asistentes, "BITACORA", tmp_path / "BITACORA.jsonl")
    result = puente_asistentes.emit({"type": "TEST"})
    assert result["status"] == "SIMULADO"
    assert not (tmp_path / "BITACORA.jsonl").exists()


def test_heartbeat_detecta_tarea_parada(monkeypatch):
    emitted = []
    monkeypatch.setattr(heartbeat, "emit", emitted.append)
    now = datetime(2026, 9, 27, 23, 0, tzinfo=timezone.utc)
    tareas = [{"id": "T06", "status": "ACTIVE", "heartbeat": (now - timedelta(minutes=31)).isoformat()}]
    assert heartbeat.vigilar(tareas, ahora=now) == "ALERTA:T06"
    assert emitted and emitted[0]["type"] == "ALERTA"


def test_heartbeat_normal_no_reply(monkeypatch):
    monkeypatch.setattr(heartbeat, "emit", lambda event: (_ for _ in ()).throw(AssertionError("no debe emitir")))
    now = datetime(2026, 9, 27, 23, 0, tzinfo=timezone.utc)
    tareas = [{"id": "T06", "status": "ACTIVE", "heartbeat": (now - timedelta(minutes=5)).isoformat()}]
    assert heartbeat.vigilar(tareas, ahora=now) == "NO_REPLY"


def test_configs_roles_router_y_sin_anthropic():
    hermes = (HERE / "hermes_config.yaml").read_text(encoding="utf-8")
    claw = (HERE / "openclaw_config.yaml").read_text(encoding="utf-8")
    assert "planner_supervisor" in hermes
    assert "guardian_supervisor" in claw
    assert "integrate.api.nvidia.com" in hermes + claw
    forbidden = "ANTHROPIC_" + "API_KEY"
    assert forbidden not in hermes + claw


def test_script_refs_y_gateways():
    script = (HERE / "arrancar_asistentes.sh").read_text(encoding="utf-8")
    assert "HERMES_REF" in script and "OPENCLAW_REF" in script
    assert "pnpm" in script
    assert "hermes gateway" in script
    assert "openclaw gateway" in script
    assert "v2026.9.24" not in script
    assert "v2026.9.6" not in script
