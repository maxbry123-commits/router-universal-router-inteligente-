"""
test_queue_manager.py — Cierre Salida 2/3
Ubicacion: router_llm_hf/tests/test_queue_manager.py
"""
import asyncio
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

from router_llm_hf import QueueManager, Priority, OutputContract


def test_prioridad_y_uno_por_modelo():
    async def run():
        qm = QueueManager()
        tid1 = await qm.enqueue("mA", {}, Priority.NORMAL)
        tid2 = await qm.enqueue("mA", {}, Priority.HIGH)
        t1 = await qm.next_task()
        assert t1.task_id == tid2
        assert await qm.next_task() is None
        await qm.complete(tid2)
        t3 = await qm.next_task()
        assert t3.task_id == tid1
        await qm.complete(tid1)
        snap = await qm.snapshot()
        assert snap["running"] == 0 and snap["queued"] == 0
        return True
    assert asyncio.run(run())


def test_output_contract_bloqueado_exige_propuesta():
    ok = OutputContract.quick("t", "r", "COMPLETADO", analisis=["evidencia"])
    assert ok.validate_or_raise().estado == "COMPLETADO"
    fallo = False
    try:
        OutputContract(task="t", respuesta="r", analisis=["e"],
                       conclusion="c", propuesta="", estado="BLOQUEADO")
    except Exception:
        fallo = True
    assert fallo
