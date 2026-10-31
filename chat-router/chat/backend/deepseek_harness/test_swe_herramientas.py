"""Harness: swe_iniciar/avanzar/estado/aprobar/reanudar dentro de la accion `invoke` (status/invoke/llm y herramientas actuales intactas).
Almacen = _router falso en memoria; agentes y servidores Liquid falsos. Ninguna clave real."""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plugins.deepseek_harness import server as h

RAIZ_CHAT_ROUTER = Path(__file__).resolve().parents[3]
CLAVE = "clave-http-solo-prueba"
CONTRATO = {"task_id": "yaiwes-001", "origen": "yaiwes", "mensaje": "Revisar proyecto", "workflow": "swe_code", "modelo_responde": "hf/lfm2.5-350m",
            "modelo_lector": "hf/lfm2.5-350m", "modelo_tool": "hf/qwen2.5-coder-1.5b", "modelo_revisor": "hf/qwen3.5-0.8b", "agente_responde": "openclaw",
            "agente_tool": "swe-agent", "agente_verificador": "openhands", "modo_agentico": True, "aprobacion": True, "sesion": "chat-001", "proyecto": "yaiwes"}


class Almacen:
    def __init__(self):
        self.datos, self.caido = {}, False

    def router(self, accion, datos):
        assert accion == "almacen"
        if self.caido:
            raise RuntimeError("Router HTTP 502: caido")
        if datos["accion"] == "guardar":
            self.datos[datos["nombre"]] = datos["valor"]
            return {"ok": True, "commit": None}
        if datos["nombre"] not in self.datos:
            raise RuntimeError("Router HTTP 404: fallo de lectura HF: no existe " + datos["nombre"])
        return {"ok": True, "valor": self.datos[datos["nombre"]]}


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    (tmp_path / "ws" / "yaiwes").mkdir(parents=True)
    monkeypatch.setenv("RIU_API_KEY", CLAVE)
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", str(tmp_path / "ws"))
    monkeypatch.setenv("RIU_SWE_OPERADORES", "ana,luis")
    a = Almacen()
    llamadas = []
    def agente(agente, tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
        llamadas.append((agente, modelo, permisos))
        return {"ok": True, "agente": agente, "task_id": tarea_id, "resultado": "hecho", "herramientas": [], "evidencias": ["e"], "recibo": "%s:%s:%d" % (agente, tarea_id, len(llamadas)), "exit_code": 0}
    with patch.object(h, "_router", a.router), patch.object(h, "ejecutar_agente", agente):
        yield a, llamadas, TestClient(h.app)


def invocar(cliente, tool, args, clave=CLAVE):
    return cliente.post("/invoke", json={"action": "invoke", "tool": tool, "args": args}, headers={"X-API-Key": clave}).json()


def test_import_del_dispatcher_con_el_pythonpath_del_harness():
    env = {"PATH": os.environ["PATH"], "PYTHONPATH": "%s:%s" % (RAIZ_CHAT_ROUTER, RAIZ_CHAT_ROUTER.parent / "router-mvp")}
    r = subprocess.run([sys.executable, "-c", "from agentes.adaptadores.dispatcher import ejecutar_agente; print('IMPORT_OK')"], env=env, capture_output=True, text=True, timeout=60)
    assert r.stdout.strip() == "IMPORT_OK", r.stderr


def test_boot_del_space_pone_chat_router_en_pythonpath():
    boot = (Path(h.__file__).parent / "space" / "boot.sh").read_text()
    linea = next(l for l in boot.splitlines() if l.startswith("export PYTHONPATH"))
    assert "/tmp/repo/chat-router" in linea and "/tmp/repo/router-mvp" in linea


def test_registro_de_herramientas_amplia_sin_quitar():
    for nombre in ("guardar", "leer", "computar", "swe_iniciar", "swe_avanzar", "swe_estado", "swe_aprobar", "swe_reanudar"):
        assert callable(h.HERRAMIENTAS[nombre])
    assert h.HERRAMIENTAS["guardar"] is h.guardar and h.HERRAMIENTAS["leer"] is h.leer and h.HERRAMIENTAS["computar"] is h.computar
    for nombre in ("swe_iniciar", "swe_avanzar", "swe_estado", "swe_aprobar", "swe_reanudar"):
        assert h.HERRAMIENTAS[nombre].__code__.co_code != h.computar.__code__.co_code  # no son stubs


def test_status_sigue_igual(entorno):
    _, _, c = entorno
    assert c.post("/invoke", json={"action": "status"}, headers={"X-API-Key": CLAVE}).json() == {"status": "ok", "result": {"servicio": "deepseek_harness", "acciones": ["status", "invoke", "llm"]}}
    assert c.post("/invoke", json={"action": "invoke", "tool": "swe_iniciar", "args": CONTRATO}, headers={"X-API-Key": "mala"}).status_code == 401
    assert invocar(c, "no_existe", {})["error"] == "tool no permitida"


def test_flujo_completo_por_invoke_sin_confiar_en_aprobacion_del_contrato(entorno):
    almacen, llamadas, c = entorno
    r = invocar(c, "swe_iniciar", CONTRATO)
    assert r["status"] == "ok" and r["result"]["estado"] == "PENDIENTE" and r["result"]["aprobacion"] is False
    assert any(k.startswith("swe/yaiwes/yaiwes/chat-001/") for k in almacen.datos)
    r = invocar(c, "swe_avanzar", {"task_id": "yaiwes-001"})["result"]
    assert r["estado"] == "REQUIERE_APROBACION" and llamadas == []
    r = invocar(c, "swe_aprobar", {"task_id": "yaiwes-001", "op_id": r["pendiente_aprobacion"]["op_id"], "operador": "intruso"})
    assert r["status"] == "error" and r["error"] == "OPERADOR_NO_AUTORIZADO" and llamadas == []
    r = invocar(c, "swe_estado", {"task_id": "yaiwes-001"})["result"]
    assert invocar(c, "swe_aprobar", {"task_id": "yaiwes-001", "op_id": r["pendiente_aprobacion"]["op_id"], "operador": "ana"})["result"]["estado"] == "CONTINUAR"
    r = invocar(c, "swe_reanudar", {"task_id": "yaiwes-001"})["result"]
    assert r["paso_actual"] == 1 and llamadas[0][0] == "codex" and llamadas[0][1] == "hf/qwen2.5-coder-1.5b"


def test_errores_del_contrato_y_de_persistencia_son_status_error(entorno):
    almacen, llamadas, c = entorno
    assert invocar(c, "swe_iniciar", {**CONTRATO, "agente_tool": "bash"})["error"] == "AGENTE_NO_REGISTRADO"
    assert invocar(c, "swe_estado", {"task_id": "no-existe"})["error"] == "TAREA_NO_ENCONTRADA"
    almacen.caido = True
    r = invocar(c, "swe_iniciar", CONTRATO)
    assert r["status"] == "error" and r["error"].startswith("PERSISTENCIA_FALLIDA")
    assert llamadas == []


def test_swe_usa_las_funciones_del_harness_en_tiempo_de_llamada(entorno):
    almacen, _, c = entorno
    vistos = []
    original = h.guardar
    def espia(args):
        vistos.append(args["nombre"])
        return original(args)
    with patch.object(h, "guardar", espia):
        invocar(c, "swe_iniciar", CONTRATO)
    assert "swe/indice/yaiwes-001.json" in vistos  # guardar() del Harness, no un almacen propio


def test_con_efectos_incluye_swe_agente_y_conserva_lo_anterior():
    assert h.con_efectos("swe_agente", {}) is True
    assert h.con_efectos("github_escribir", {}) and h.con_efectos("agente", {}) and h.con_efectos("llm", {})
    assert not h.con_efectos("github_leer", {}) and not h.con_efectos("almacen", {"accion": "leer"}) and h.con_efectos("almacen", {"accion": "guardar"})


def test_el_modelo_no_puede_invocar_swe_desde_el_bucle_de_herramientas():
    """El bucle llm() solo ejecuta herramientas del catalogo MCP del Router: swe_aprobar no esta ahi, asi que ningun modelo puede aprobar."""
    pedidas = []
    def llamar(plugin, accion, datos=None, timeout=0):
        if accion == "mcp" and datos["method"] == "tools/list":
            return {"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}}
        pedidas.append(datos)
        return {"result": {}}
    turnos = iter([
        {"texto": "", "finish_reason": "tool_calls", "tool_calls": [{"id": "c1", "function": {"name": "swe_aprobar", "arguments": json.dumps({"task_id": "x", "operador": "ana"})}}]},
        {"texto": "listo", "tool_calls": [], "finish_reason": "stop"}])
    mensajes_vistos = []
    def router(accion, datos):
        mensajes_vistos.append(datos["mensajes"])
        return next(turnos)
    with patch.object(h, "llamar", llamar), patch.object(h, "_router", router), patch.object(h, "PAUSA_S", 1e9):
        r = h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "x"})
    assert r["texto"] == "listo" and pedidas == []
    assert "Herramienta no autorizada: swe_aprobar" in json.dumps(mensajes_vistos[-1])
