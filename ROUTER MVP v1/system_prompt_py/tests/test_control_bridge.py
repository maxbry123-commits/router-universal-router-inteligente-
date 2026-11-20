"""
test_control_bridge.py — Cierre Salida 1/3
Ubicacion: ROUTER MVP v1/system_prompt_py/tests/test_control_bridge.py
"""
import ast
import asyncio
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))


def test_proxy_parsea():
    src = (BASE / "openai_compatible_proxy.py").read_text(encoding="utf-8")
    ast.parse(src)


def test_bridge_parsea():
    src = (BASE / "control_bridge.py").read_text(encoding="utf-8")
    ast.parse(src)


def test_bridge_run_passthrough():
    import control_bridge

    async def valor():
        return 42

    out = asyncio.run(control_bridge.BRIDGE.run("t-test", valor()))
    assert out == 42


def test_bridge_status_claves():
    import control_bridge

    st = control_bridge.BRIDGE.status()
    assert "control_plane" in st
    assert "watchdog" in st
    assert "recall" in st
