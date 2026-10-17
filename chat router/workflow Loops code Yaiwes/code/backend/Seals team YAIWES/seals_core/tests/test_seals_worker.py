"""S-02/S-05: SealsWorker.execute(TaskContract) -> NodeResult, tipado."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seals_worker import NodeResult, SealsWorker, TaskContract


def test_execute_devuelve_noderesult_tipado_pass():
    w = SealsWorker()
    r = w.execute(TaskContract(tipo="verificar_existencia", nombre="ejecutor.py"))
    assert isinstance(r, NodeResult)
    assert r.status == "PASS"
    assert r.evidencia["existe"] is True
    assert r.mission_id


def test_execute_gap_tipado_archivo_inexistente():
    w = SealsWorker()
    r = w.execute(TaskContract(tipo="verificar_existencia", nombre="no_existe_zzz.bin"))
    assert r.status == "GAP"
    assert r.evidencia["existe"] is False


def test_replay_idempotente_mismo_command_id():
    w = SealsWorker()
    c = TaskContract(tipo="verificar_existencia", nombre="ejecutor.py", command_id="cmd-42")
    r1 = w.execute(c)
    r2 = w.execute(c)
    assert r2.idempotencia == "REPLAY_RESULTADO_PREVIO"
    assert r2.mission_id == r1.mission_id


def test_tipo_desconocido_es_gap_no_silencio():
    w = SealsWorker()
    r = w.execute(TaskContract(tipo="tipo_inexistente_xxx"))
    assert r.status == "GAP"
