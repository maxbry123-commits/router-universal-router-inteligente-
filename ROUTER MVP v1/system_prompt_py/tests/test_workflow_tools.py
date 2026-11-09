import os
import tempfile
from semantic_checkpoint import SemanticCheckpoint
from workflow_tools import WorkflowTools, TOOL_SCHEMAS


def _wt(tmp):
    os.chdir(tmp)
    return WorkflowTools(SemanticCheckpoint("plan-wf", {"env": "t"}))


def test_flujo_dividir_entregar_recuperar():
    with tempfile.TemporaryDirectory() as d:
        wt = _wt(d)
        assert wt.dispatch("dividir_tarea", {"task_id": "T", "partes": [{"id": "p1", "desc": "a"}, {"id": "p2", "desc": "b"}]})["status"] == "ok"
        assert wt.dispatch("continuar_cola", {"task_id": "T"})["siguiente"] == "p1"
        assert wt.dispatch("entregar_parte", {"task_id": "T", "part_id": "p1", "code": "def f():\n    return 1\n"})["status"] == "ok"
        assert wt.dispatch("continuar_cola", {"task_id": "T"})["siguiente"] == "p2"
        assert wt.dispatch("checkpoint_guardar", {"task_id": "T", "part_id": "p2", "text": "def g():"})["status"] == "ok"
        r = wt.dispatch("recuperar_checkpoint", {"task_id": "T"})
        assert r["hechas"] == ["p1"] and r["pendientes"] == ["p2"] and r["parciales"] == {"p2": "def g():"}
        wt.dispatch("entregar_parte", {"task_id": "T", "part_id": "p2", "code": "def g():\n    return 2\n"})
        assert wt.dispatch("continuar_cola", {"task_id": "T"})["siguiente"] == "DONE"


def test_rechaza_parte_mayor_200_y_parte_inexistente():
    with tempfile.TemporaryDirectory() as d:
        wt = _wt(d)
        wt.dispatch("dividir_tarea", {"task_id": "T", "partes": [{"id": "p1", "desc": "a"}]})
        big = "\n".join(f"v{i} = {i}" for i in range(260))
        assert wt.dispatch("entregar_parte", {"task_id": "T", "part_id": "p1", "code": "def big():\n" + "\n".join(f"    v{i} = {i}" for i in range(260)) + "\n"})["status"] == "error"
        assert wt.dispatch("entregar_parte", {"task_id": "T", "part_id": "zz", "code": "x = 1\n"})["status"] == "error"


def test_persistencia_entre_instancias():
    with tempfile.TemporaryDirectory() as d:
        wt = _wt(d)
        wt.dispatch("dividir_tarea", {"task_id": "T", "partes": [{"id": "p1", "desc": "a"}, {"id": "p2", "desc": "b"}]})
        wt.dispatch("entregar_parte", {"task_id": "T", "part_id": "p1", "code": "x = 1\n"})
        wt2 = WorkflowTools(SemanticCheckpoint("plan-wf", {"env": "t"}))
        assert wt2.dispatch("continuar_cola", {"task_id": "T"})["siguiente"] == "p2"


def test_schemas_y_herramienta_desconocida():
    assert {s["function"]["name"] for s in TOOL_SCHEMAS} == {"dividir_tarea", "entregar_parte", "checkpoint_guardar", "recuperar_checkpoint", "continuar_cola"}
    with tempfile.TemporaryDirectory() as d:
        assert _wt(d).dispatch("nope", {})["status"] == "error"


def test_tool_executor_enruta_workflow(monkeypatch):
    import asyncio
    import tempfile
    monkeypatch.setenv("AGENT_HARNESS_URL", "http://127.0.0.1:9/none")
    from tool_executor import ToolExecutor
    with tempfile.TemporaryDirectory() as d:
        ex = ToolExecutor()
        ex.workflow = _wt(d)
        r = asyncio.run(ex.execute("dividir_tarea", {"task_id": "T", "partes": [{"id": "p1", "desc": "a"}]}))
        assert r["status"] == "ok"
        assert asyncio.run(ex.execute("continuar_cola", {"task_id": "T"}))["siguiente"] == "p1"
