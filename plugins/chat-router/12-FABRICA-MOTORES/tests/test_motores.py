"""Tests T08: un "dashboard móvil" recorre capability → canvas → layout →
actions → qa → PASS; casos de conflicto y botón muerto."""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from capability_engine import CapabilityEngine
from canvas_engine import CanvasEngine
from layout_engine import LayoutEngine, breakpoint_for
from action_flow_engine import ActionFlowEngine
from sandbox_engine import SandboxEngine
from qa_engine import QAEngine
from registry import ENGINE_REGISTRY, create_engines, ejecutar_en_paralelo

COMPONENTS = [
    {"id": "stat_card", "provides": ["stat"], "runtime": "web"},
    {"id": "line_chart", "provides": ["chart"], "runtime": "web"},
    {"id": "data_table", "provides": ["table"], "runtime": "web"},
    {"id": "refresh_button", "provides": ["action.refresh"],
     "compatible_with": ["stat_card", "line_chart", "data_table"]},
]


def run(coro):
    return asyncio.run(coro)


def build_dashboard():
    cap = CapabilityEngine(components=COMPONENTS)
    comp = run(cap.execute({"capability": "ui.capability",
                            "objective": ["stat", "chart", "table",
                                          "action.refresh"]}))
    assert comp["status"] == "PASS", comp

    canvas = CanvasEngine()
    res = run(canvas.execute({"capability": "ui.canvas", "ops": [
        {"op": "createPage", "args": ["dash", "Dashboard"]},
        {"op": "addSection", "args": ["main"]},
        {"op": "addComponent", "args": ["main", {
            "id": "kpi1", "type": "stat_card",
            "properties": {"span": 1, "height": 120}}]},
        {"op": "addComponent", "args": ["main", {
            "id": "chart1", "type": "line_chart",
            "properties": {"span": 1, "height": 200}}]},
        {"op": "addComponent", "args": ["main", {
            "id": "table1", "type": "data_table",
            "properties": {"span": 1, "height": 240}}]},
        {"op": "addComponent", "args": ["main", {
            "id": "btn_refresh", "type": "button",
            "action_id": "refresh",
            "properties": {"span": 1, "height": 48}}]},
    ]}))
    assert res["status"] == "PASS", res
    page = res["result"]

    layout = LayoutEngine()
    lay = run(layout.execute({"capability": "ui.layout",
                              "viewport_width": 360, "viewport_height": 2000,
                              "elements": [
                                  {"id": "kpi1", "height": 120},
                                  {"id": "chart1", "height": 200},
                                  {"id": "table1", "height": 240},
                                  {"id": "btn_refresh", "height": 48}],
                              "columns": 12, "gap": 8}))
    assert lay["status"] == "PASS", lay
    assert lay["breakpoint"] == "mobile"
    assert lay["overflow"] == []

    actions = ActionFlowEngine()
    actions.register_handler("refresh", lambda payload: {
        "handler": "refresh", "status": "PASS"})
    flow = {"nodes": [
        {"id": "v", "step": "validate"},
        {"id": "s", "step": "serialize"},
        {"id": "p", "step": "persist"},
        {"id": "n", "step": "notify"},
    ], "edges": [{"from": "v", "to": "s"}, {"from": "s", "to": "p"},
                 {"from": "p", "to": "n"}]}
    fres = run(actions.execute({"capability": "ui.actions", "flow": flow}))
    assert fres["status"] == "PASS", fres
    assert [t["handler"] for t in fres["result"]] == [
        "validate", "serialize", "persist", "notify"]

    qa = QAEngine()
    qres = run(qa.execute({"capability": "qa.visual", "page": page,
                           "known_actions": set(actions.handlers)}))
    assert qres["status"] == "PASS", qres
    return page


def test_dashboard_movil_end_to_end():
    build_dashboard()


def test_capability_conflicto():
    cap = CapabilityEngine(components=[
        {"id": "a", "provides": ["x"], "conflicts_with": ["b"]},
        {"id": "b", "provides": ["y"]},
    ])
    res = run(cap.execute({"capability": "ui.capability",
                           "objective": ["x", "y"]}))
    assert res["status"] == "FAIL"
    assert any("conflicto" in (a.get("reason") or "")
               for a in res["audit"] if a.get("discarded"))


def test_capability_sin_candidatos():
    cap = CapabilityEngine(components=COMPONENTS)
    res = run(cap.execute({"capability": "ui.capability",
                           "objective": ["no.existe"]}))
    assert res["status"] == "FAIL"
    assert "sin candidatos" in res["reason"]


def test_componente_invisible(tmp_path):
    (tmp_path / "ghost_component").mkdir()
    cap = CapabilityEngine(components=COMPONENTS,
                           components_dir=str(tmp_path))
    res = run(cap.execute({"capability": "ui.capability",
                           "objective": ["stat"]}))
    assert res["status"] == "FAIL"
    assert "ghost_component" in res["reason"]


def test_boton_muerto():
    actions = ActionFlowEngine()
    canvas = CanvasEngine()
    res = run(canvas.execute({"capability": "ui.canvas", "ops": [
        {"op": "createPage", "args": ["p"]},
        {"op": "addSection", "args": ["s"]},
        {"op": "addComponent", "args": ["s", {
            "id": "btn_dead", "type": "button",
            "properties": {"height": 48}}]},
    ]}))
    page = res["result"]
    dead = actions.check_dead_buttons(page)
    assert dead == ["btn_dead"]
    res2 = run(actions.execute({"capability": "ui.actions", "page": page}))
    assert res2["status"] == "FAIL"
    qa = QAEngine()
    qres = run(qa.execute({"capability": "qa.visual", "page": page,
                           "known_actions": set(actions.handlers)}))
    assert qres["status"] == "FAIL"
    assert any("btn_dead" in i for i in qres["issues"])


def test_flujo_con_ciclo():
    actions = ActionFlowEngine()
    flow = {"nodes": [{"id": "a", "step": "validate"},
                      {"id": "b", "step": "persist"}],
            "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]}
    res = actions.compile_flow(flow)
    assert res["status"] == "FAIL"
    assert "ciclo" in res["reason"]


def test_layout_breakpoints_y_snap():
    assert breakpoint_for(360) == "mobile"
    assert breakpoint_for(800) == "tablet"
    assert breakpoint_for(1400) == "desktop"
    layout = LayoutEngine()
    res = layout.compute(1024, 768,
                         [{"id": "a", "span": 6, "height": 100},
                          {"id": "b", "span": 6, "height": 100}],
                         columns=12, gap=8, snap_grid=4)
    assert res["status"] == "PASS"
    for p in res["result"]:
        assert p["x"] % 4 == 0 and p["y"] % 4 == 0


def test_layout_solape_detectado_por_qa():
    qa = QAEngine()
    overlaps = qa.check_overlaps([
        {"id": "a", "x": 0, "y": 0, "width": 100, "height": 100},
        {"id": "b", "x": 50, "y": 50, "width": 100, "height": 100},
    ])
    assert overlaps


def test_sandbox_python():
    sb = SandboxEngine(timeout=10)
    res = run(sb.execute({"capability": "code.sandbox", "lang": "python",
                          "code": "print('hola')"}))
    assert res["status"] == "PASS"
    assert res["rc"] == 0
    assert "hola" in res["stdout"]
    assert run(sb.verify(res))


def test_sandbox_timeout():
    sb = SandboxEngine(timeout=1)
    res = run(sb.run_python("import time; time.sleep(5)"))
    assert res["status"] == "FAIL"
    assert res["reason"] == "timeout"


def test_sandbox_limite_salida():
    sb = SandboxEngine(timeout=10, max_output=128)
    res = run(sb.run_python("print('x' * 10000)"))
    assert res["status"] == "PASS"
    assert res["truncated"]
    assert len(res["stdout"]) <= 128


def test_registry_y_paralelo():
    assert set(ENGINE_REGISTRY) == {"ui.capability", "ui.canvas", "ui.layout",
                                    "ui.actions", "code.sandbox", "qa.visual"}
    engines = create_engines(capability_components=COMPONENTS)
    results = run(ejecutar_en_paralelo([
        {"engine": engines["ui.layout"],
         "task": {"viewport_width": 360, "viewport_height": 500,
                  "elements": [{"id": "x", "height": 60}]}},
        {"engine": engines["code.sandbox"],
         "task": {"lang": "python", "code": "print(1+1)"}},
    ]))
    assert all(r["status"] == "PASS" for r in results)
    assert "2" in results[1]["stdout"]


def test_canvas_move_y_set_property():
    canvas = CanvasEngine()
    res = run(canvas.execute({"capability": "ui.canvas", "ops": [
        {"op": "createPage", "args": ["p"]},
        {"op": "addSection", "args": ["s1"]},
        {"op": "addSection", "args": ["s2"]},
        {"op": "addComponent", "args": ["s1", {"id": "c1", "type": "stat_card"}]},
        {"op": "moveComponent", "args": ["c1", "s2"]},
        {"op": "setProperty", "args": ["c1", "span", 2]},
    ]}))
    assert res["status"] == "PASS"
    page = res["result"]
    assert page["sections"][0]["components"] == []
    comp = page["sections"][1]["components"][0]
    assert comp["id"] == "c1" and comp["properties"]["span"] == 2


def test_canvas_errores():
    canvas = CanvasEngine()
    res = run(canvas.execute({"capability": "ui.canvas", "ops": [
        {"op": "addSection", "args": ["s"]},
    ]}))
    assert res["status"] == "FAIL"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
