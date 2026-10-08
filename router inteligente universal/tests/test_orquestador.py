"""PUNTO 6: mini-orquestador por chat con interruptor ON/OFF (OFF por defecto). Sin red: el proveedor es falso."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from integration.chat_mvp import memoria_loader, orquestador  # noqa: E402
from integration.chat_mvp.router import _auth, set_store  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402
from plugins.puente_chat import plugin as P  # noqa: E402
from plugins.puente_chat import plugin_long_context as L  # noqa: E402,F401  (instala el envoltorio de contexto largo)

S = "web-00000000000000aa"
IB = "  Orden literal: «revisa A» y luego B\r\n\t— no parafrasear 🧩 \n"


class FakeLLM:
    def __init__(self, plan=None, sleep=0.0):
        self.calls: list[dict] = []
        self.plan = plan if plan is not None else {"nodos": [
            {"id": "a", "agente": "wf-codex", "instrucciones": "Revisa A"},
            {"id": "b", "agente": "orquestador-g0", "instrucciones": "Haz B", "needs": ["a"]}]}
        self.sleep = sleep

    def __call__(self, proveedor, modelo, mensajes, max_tokens, tope, tools):
        system = str(mensajes[0].get("content") or "")
        user = str(mensajes[-1].get("content") or "")
        self.calls.append({"proveedor": proveedor, "modelo": modelo, "mensajes": [dict(m) for m in mensajes], "tools": tools})
        if "Devuelve SOLO JSON" in system:
            text = json.dumps(self.plan, ensure_ascii=False)
        elif "Resume para el usuario" in system:
            text = "RESUMEN-FINAL"
        else:
            m = re.search(r"NODO (n\d)", user)
            if self.sleep and m:
                time.sleep(self.sleep)
            text = "salida-" + (m.group(1) if m else "normal")
        return 200, {"choices": [{"message": {"role": "assistant", "content": text}}], "usage": {}}


@pytest.fixture()
def env(tmp_path, monkeypatch):
    st = Store(tmp_path / "d")
    st.upsert_agent("wf-codex", "Codex (Wordflow)", "auditor técnico", "Eres Codex.", [])
    set_store(st)
    memoria_loader._facade = None
    monkeypatch.setattr(P, "_sentinela", lambda: None)
    app = FastAPI()
    app.include_router(memoria_loader.build_memory_router())
    app.dependency_overrides[_auth] = lambda: "tester"
    yield TestClient(app), st, monkeypatch
    set_store(None)
    memoria_loader._facade = None
    st.close()


def _chat(sesion, text="hola", model="groq-qwen-3-8", **kw):
    return P.handle("chat", {"model": model, "sesion": sesion, "messages": [{"role": "user", "content": text}], **kw})


def _rows(st, sesion):
    return [(r["key"][:6], r["data"]) for r in st._all("SELECT key,data FROM memoria_yaiwes WHERE scope=? AND key LIKE 'turno-%' ORDER BY id",
                                                        ("chat-ui:chat:" + sesion,))]


def test_default_is_off_and_toggle_roundtrip(env):
    c, _, _ = env
    r = c.get("/chat/orquestador/" + S).json()
    assert r["activo"] is False and r["ts"] is None and r["limites"]["max_nodos"] == 3
    assert c.post("/chat/orquestador/" + S, json={"activo": True}).json()["activo"] is True
    assert c.get("/chat/orquestador/" + S).json()["activo"] is True
    assert c.post("/chat/orquestador/" + S, json={"activo": False}).json()["activo"] is False
    assert c.post("/chat/orquestador/" + S, json={"activo": "x"}).status_code == 422
    assert c.get("/chat/orquestador/bad%20s").status_code == 422


def _baseline(tmp_path, monkeypatch, sesion, toggle_dance):
    st = Store(tmp_path)
    set_store(st)
    memoria_loader._facade = None
    if toggle_dance:
        orquestador.poner(sesion, True)
        orquestador.poner(sesion, False)
    fake = FakeLLM()
    monkeypatch.setattr(P, "_llamar_api", fake)
    out = _chat(sesion, IB)
    rows = _rows(st, sesion)
    extra = st._all("SELECT key FROM memoria_yaiwes WHERE key LIKE 'orq:%' OR key LIKE 'hija:%' OR scope LIKE '%:ag:%'")
    st.close()
    return fake.calls, out, [(k, json.loads(d)["pregunta"], json.loads(d)["respuesta"]) for k, d in rows], extra


def test_off_changes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "_sentinela", lambda: None)
    def boom(p):
        raise AssertionError("con OFF nunca se llama al orquestador")
    monkeypatch.setattr(orquestador, "ejecutar", boom)
    never = _baseline(tmp_path / "a", monkeypatch, S, toggle_dance=False)   # interruptor nunca tocado (default)
    off = _baseline(tmp_path / "b", monkeypatch, S, toggle_dance=True)      # ON y luego OFF
    set_store(None)
    memoria_loader._facade = None
    assert never[0] == off[0]                  # mismas llamadas al proveedor, mismo prompt, mismas herramientas
    assert never[0][0]["tools"] is not None    # el chat normal sigue usando herramientas
    assert never[1] == off[1] and off[1]["choices"][0]["message"]["content"] == "salida-normal"
    assert never[2] == off[2] and len(off[2]) == 1
    assert never[3] == off[3] == []            # ni runs, ni hijos


def test_on_runs_two_nodes_in_children_and_summarizes_in_parent(env):
    c, st, mp = env
    fake = FakeLLM()
    mp.setattr(P, "_llamar_api", fake)
    c.post("/chat/orquestador/" + S, json={"activo": True})
    out = _chat(S, IB, orquestador_nodos=2)
    assert out["choices"][0]["message"]["content"] == "RESUMEN-FINAL"
    o = out["orquestador"]
    assert o["estado"] == "HECHO" and [(n["id"], n["agente"], n["estado"]) for n in o["nodos"]] == [
        ("n1", "wf-codex", "HECHO"), ("n2", "orquestador-g0", "HECHO")]
    kids = c.get("/chat/children/" + S).json()["children"]
    assert [k["sesion_hija"] for k in kids] == [n["sesion_hija"] for n in o["nodos"]]
    for k in kids:  # INPUT_BLOCK del padre literal en cada hijo
        assert c.get("/chat/child/" + k["sesion_hija"]).json()["input_block"].encode("utf-8") == IB.encode("utf-8")
    node_calls = [x for x in fake.calls if "NODO n" in x["mensajes"][-1]["content"]]
    assert len(node_calls) == 2 and all(x["tools"] is None for x in node_calls)   # sin herramientas en los nodos
    assert all("<<<INPUT_BLOCK\n" + IB + "\nINPUT_BLOCK>>>" in x["mensajes"][0]["content"] for x in node_calls)
    assert "salida-n1" in node_calls[1]["mensajes"][-1]["content"]                # n2 recibe la salida de n1 (needs)
    h = c.get("/chat/child/" + kids[0]["sesion_hija"]).json()["history"]
    assert [m["content"] for m in h["messages"]][1] == "salida-n1"
    hp = c.get("/chat/history/" + S).json()                                       # el padre guarda solo el resumen
    assert [m["content"] for m in hp["messages"]] == [IB, "RESUMEN-FINAL"]
    runs = c.get("/chat/orquestador/%s/runs" % S).json()["runs"]
    assert len(runs) == 1 and runs[0]["estado"] == "HECHO" and runs[0]["nodos"] == 2
    run = c.get("/chat/orquestador/%s/runs/%s" % (S, o["run_id"])).json()
    assert run["dag"]["schema"] == "riu.dag/v1" and len(run["dag"]["nodes"]) == 2 and run["resumen"] == "RESUMEN-FINAL"
    assert [n["respuesta"] for n in run["nodos"]] == ["salida-n1", "salida-n2"] and run["ts_fin"]
    assert c.get("/chat/orquestador/%s/runs/orq-1-x" % S).status_code == 422
    assert c.get("/chat/orquestador/%s/runs/orq-0000000000000-abcd" % S).status_code == 404


def test_limits_three_nodes_unknown_agent_and_forward_needs(env):
    _, st, mp = env
    plan = {"nodos": [{"id": str(i), "agente": "no-existe" if i == 0 else "wf-codex", "instrucciones": "t%d" % i, "needs": [str(i + 1)]}
                      for i in range(6)]}
    mp.setattr(P, "_llamar_api", FakeLLM(plan=plan))
    orquestador.poner(S, True)
    o = _chat(S, IB)["orquestador"]
    assert len(o["nodos"]) == 3 and o["nodos"][0]["agente"] == "orquestador-g0"
    run = orquestador.leer_run(S, o["run_id"])
    assert all(n["needs"] == [] for n in run["nodos"])  # needs hacia nodos posteriores descartados: sin ciclos


def test_node_timeout_is_enforced(env):
    _, _, mp = env
    mp.setattr(orquestador, "NODE_TIMEOUT_S", 1)
    mp.setattr(P, "_llamar_api", FakeLLM(plan={"nodos": [{"agente": "wf-codex", "instrucciones": "lento"}]}, sleep=2.5))
    orquestador.poner(S, True)
    t = time.time()
    out = _chat(S, IB)
    assert out["orquestador"]["nodos"][0]["estado"] == "TIMEOUT" and out["orquestador"]["estado"] == "PARCIAL"
    assert time.time() - t < 2.4 and out["choices"][0]["message"]["content"] == "RESUMEN-FINAL"
    time.sleep(2.5)  # deja terminar el hilo del nodo lento antes de cerrar el Store del test


def test_no_recursion_and_api_models_only(env):
    c, _, mp = env
    fake = FakeLLM()
    mp.setattr(P, "_llamar_api", fake)
    hija = S + ":ag:wf-codex:1"
    assert c.post("/chat/orquestador/" + hija, json={"activo": True}).json()["detail"] == "ORQUESTADOR_EN_HIJA"
    memoria_loader._memory().save("chat-ui:chat:" + hija, "orquestador", {"activo": True})  # aunque alguien lo fuerce
    assert orquestador.activo(hija) is False
    orquestador.poner(S, True)
    tok = orquestador.EN_RUN.set(True)
    try:
        assert orquestador.activo(S) is False  # dentro de un run nunca se vuelve a orquestar
    finally:
        orquestador.EN_RUN.reset(tok)
    encendido = []
    mp.setattr(P, "_encender", lambda m: encendido.append(m) or {"estado": "encendiendo"})
    respaldo = next(iter(P.RESPALDO))
    assert _chat(S, "x", model=respaldo)["error"] == "ORQUESTADOR_SOLO_FICHAS_API" and encendido == []  # nunca enciende un Job
    especial = next(iter(P.ESPECIALES))
    assert _chat(S, "x", model=especial)["error"] == "ORQUESTADOR_SOLO_FICHAS_API"


def test_routes_require_auth(env):
    c, _, _ = env
    c.app.dependency_overrides.clear()
    assert c.get("/chat/orquestador/" + S).status_code == 401
    assert c.post("/chat/orquestador/" + S, json={"activo": True}).status_code == 401
    assert c.get("/chat/orquestador/%s/runs" % S).status_code == 401


def test_same_thread_can_orchestrate_again(env):
    _, _, mp = env  # los hilos del pool de chat_async se reutilizan: el guardia de recursion debe restaurarse
    mp.setattr(P, "_llamar_api", FakeLLM(plan={"nodos": [{"agente": "wf-codex", "instrucciones": "uno"}]}))
    orquestador.poner(S, True)
    assert _chat(S, IB)["orquestador"]["estado"] == "HECHO"
    assert _chat(S, IB)["orquestador"]["estado"] == "HECHO"
    assert orquestador.EN_RUN.get() is False
    orquestador.poner(S, False)
    assert "orquestador" not in _chat(S, "normal")
