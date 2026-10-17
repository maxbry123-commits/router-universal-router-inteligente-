"""MCP Streamable HTTP (/mcp): auth por token, initialize, tools/list, tools/call por el harness; + fichas nuevas validas en el PluginHost."""
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from integration.plugin_host import mcp_http as M
from integration.plugin_host.host import PluginHost

ROOT = Path(__file__).resolve().parents[1]


class FakeHost:
    def __init__(self):
        self.calls = []
        self.polls = 0

    def call(self, pid, action, payload=None, timeout_s=None):
        self.calls.append((pid, action, payload))
        if (pid, action) == ("puente_chat", "chat_async"):
            return {"status": "ok", "result": {"estado": "procesando", "proceso_id": "p1"}}
        if (pid, action) == ("puente_chat", "resultado"):
            self.polls += 1
            if self.polls < 2:
                return {"status": "ok", "result": {"estado": "procesando", "proceso_id": "p1"}}
            return {"status": "ok", "result": {"choices": [{"message": {"content": "hola desde la ficha"}}], "memoria_guardada": True}}
        if (pid, action) == ("puente_chat", "modelos"):
            return {"status": "ok", "result": {"modelos": [{"id": "nv-muse-glimmer"}]}}
        if (pid, action) == ("fichas_qwen", "fichas"):
            return {"status": "ok", "result": {"fichas": [{"n": 1, "id": "ficha1-modelos"}]}}
        if (pid, action) == ("secretos", "listar"):
            return {"status": "ok", "result": {"ok": True, "secretos": [{"nombre": "groq-1", "mascara": "gsk…6789"}]}}
        if (pid, action) == ("watchdog", "status"):
            return {"status": "ok", "result": {"ok": True, "caidos": []}}
        return {"status": "degraded", "reason": "x"}


class FakeMem:
    def __init__(self):
        self.saved = []

    def save(self, scope, key, data):
        self.saved.append((scope, key, data))
        return {"id": len(self.saved)}

    def search(self, scope, q, k):
        return {"sqlite": [{"key": k2, "data": d} for s, k2, d in reversed(self.saved) if s == scope and q in json.dumps(d)][:k]}


TOKEN = "riu-mcp-test"
H = {"Authorization": "Bearer " + TOKEN, "Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


@pytest.fixture()
def cli():
    host, mem = FakeHost(), FakeMem()
    M.set_deps(host=host, memory=mem, verificar=lambda t: t == TOKEN)
    app = FastAPI()
    app.include_router(M.build_mcp_router())
    yield TestClient(app), host, mem
    M.set_deps()


def rpc(c, method, params=None, mid=1, headers=H):
    body = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        body["params"] = params
    return c.post("/mcp", json=body, headers=headers)


def test_auth(cli):
    c, *_ = cli
    assert rpc(c, "ping", headers={"Content-Type": "application/json"}).status_code == 401
    assert rpc(c, "ping", headers={"Authorization": "Bearer malo"}).status_code == 401
    r = rpc(c, "ping")
    assert r.status_code == 200 and r.json()["result"] == {}
    assert c.get("/mcp", headers=H).status_code == 405


def test_initialize_y_lista(cli):
    c, *_ = cli
    r = rpc(c, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}).json()
    assert r["result"]["protocolVersion"] == "2025-03-26" and "tools" in r["result"]["capabilities"]
    n = c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=H)
    assert n.status_code == 202
    nombres = [t["name"] for t in rpc(c, "tools/list").json()["result"]["tools"]]
    assert {"chat", "listar_fichas", "memoria_buscar", "memoria_guardar"} <= set(nombres)


def test_chat_por_el_harness(cli):
    c, host, _ = cli
    r = rpc(c, "tools/call", {"name": "chat", "arguments": {"modelo": "nv-muse-glimmer", "mensaje": "hola"}}).json()["result"]
    assert not r["isError"] and r["content"][0]["text"] == "hola desde la ficha"
    assert host.calls[0][0:2] == ("puente_chat", "chat_async") and host.calls[0][2]["sesion"] == "mcp-general"
    falta = rpc(c, "tools/call", {"name": "chat", "arguments": {"mensaje": "x"}}).json()["result"]
    assert falta["isError"]


def test_memoria_scope_acotado(cli):
    c, _, mem = cli
    rpc(c, "tools/call", {"name": "memoria_guardar", "arguments": {"clave": "k0", "datos": 1, "scope": "../../chat-ui:secretos"}})
    assert mem.saved[0][0] == "chat-ui:mcp:chat-ui:secretos"  # siempre bajo chat-ui:mcp, nunca el almacen real de secretos
    rpc(c, "tools/call", {"name": "memoria_guardar", "arguments": {"clave": "k1", "datos": {"t": "dato-mcp"}, "scope": "notas"}})
    r = rpc(c, "tools/call", {"name": "memoria_buscar", "arguments": {"consulta": "dato-mcp", "scope": "chat-ui:mcp:notas"}}).json()["result"]
    assert r["structuredContent"]["resultados"][0]["datos"] == {"t": "dato-mcp"}
    r = rpc(c, "tools/call", {"name": "memoria_buscar", "arguments": {"consulta": "", "scope": "chat-ui:secretos"}}).json()["result"]
    assert r["structuredContent"]["scope"] != "chat-ui:secretos"  # el almacen de secretos no se puede leer
    r = rpc(c, "tools/call", {"name": "memoria_buscar", "arguments": {"consulta": "", "scope": "chat-ui:chat:web-general"}}).json()["result"]
    assert r["structuredContent"]["scope"] == "chat-ui:chat:web-general"  # la memoria del chat si


def test_batch_y_errores(cli):
    c, *_ = cli
    r = c.post("/mcp", json=[{"jsonrpc": "2.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "method": "notifications/x"},
                             {"jsonrpc": "2.0", "id": 2, "method": "nada"}], headers=H).json()
    assert len(r) == 2 and r[1]["error"]["code"] == -32601
    assert c.post("/mcp", content=b"{no", headers=H).status_code == 400
    assert rpc(c, "tools/call", {"name": "inexistente"}).json()["error"]["code"] == -32602


def test_fichas_nuevas_validas_en_el_host(tmp_path):
    h = PluginHost(state_path=tmp_path / "s.json")
    for pid in ("secretos", "watchdog"):
        rec = h.get(pid)
        assert rec and rec["status"] == "ready", rec
    assert h.call("secretos", "obtener", {})["reason"] == "accion no permitida por la ficha"
