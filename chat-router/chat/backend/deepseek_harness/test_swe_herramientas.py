"""Harness: swe_iniciar/avanzar/estado/aprobar/reanudar dentro de la accion `invoke` (status/invoke/llm y herramientas actuales intactas).
Almacen = _router falso en memoria; agentes y servidores Liquid falsos. Ninguna clave real."""
import json
import os
import shutil
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
NODE = shutil.which("node")
CLAVE = "clave-http-solo-prueba"
CONTRATO = {"task_id": "yaiwes-001", "origen": "yaiwes", "mensaje": "Revisar proyecto", "workflow": "swe_code", "modelo_responde": "hf/lfm2.5-350m",
            "modelo_lector": "hf/lfm2.5-350m", "modelo_tool": "hf/qwen2.5-coder-1.5b", "modelo_revisor": "hf/qwen3.5-0.8b", "agente_responde": "openclaw",
            "agente_tool": "swe-agent", "agente_verificador": "openhands", "modo_agentico": True, "aprobacion": True, "sesion": "chat-001", "proyecto": "yaiwes"}


class Almacen:
    def __init__(self):
        self.datos, self.caido, self.agentes_on, self.control_caido, self.consultas = {}, False, True, False, 0

    def router(self, accion, datos):
        if accion == "tools_lock":  # estado Agentes ON/OFF del Router (solo lectura)
            self.consultas += 1
            if self.control_caido:
                raise RuntimeError("Router error de red")
            return {"tools": [], "ia": True, "agentes_on": self.agentes_on}  # el `result` de /plugins/puente_chat/call/tools_lock
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
    from agentes.adaptadores import workflows as wf
    todos = {x: {"disponible": True, "motivo": ""} for x in ("openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code")}  # el preflight (workflows.py) consulta la disponibilidad REAL: aqui se simulan los seis instalados
    with patch.object(h, "_router", a.router), patch.object(h, "ejecutar_agente", agente), patch.object(wf, "_disponibilidad_real", lambda: todos):
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
    r = c.post("/invoke", json={"action": "status"}, headers={"X-API-Key": CLAVE}).json()
    assert r["status"] == "ok" and r["result"]["servicio"] == "deepseek_harness" and r["result"]["acciones"] == ["status", "invoke", "llm"]  # lo de siempre, mas `swe` (ver test_status_emite_swe_*)
    assert set(r["result"]) == {"servicio", "acciones", "swe"}
    assert c.post("/invoke", json={"action": "invoke", "tool": "swe_iniciar", "args": CONTRATO}, headers={"X-API-Key": "mala"}).status_code == 401
    assert invocar(c, "no_existe", {})["error"] == "tool no permitida"


def test_flujo_completo_por_invoke_sin_confiar_en_aprobacion_del_contrato(entorno):
    almacen, llamadas, c = entorno
    r = invocar(c, "swe_iniciar", CONTRATO)
    assert r["status"] == "ok" and r["result"]["estado"] == "PENDIENTE" and r["result"]["aprobacion"] is False
    assert any(k.startswith("swe/yaiwes/yaiwes/chat-001/") for k in almacen.datos)
    r = invocar(c, "swe_avanzar", {"task_id": "yaiwes-001"})["result"]
    assert r["estado"] != "REQUIERE_APROBACION"
    assert r["pendiente_aprobacion"] is None
    assert r["paso_actual"] == 1
    assert llamadas[0][0] == "codex" and llamadas[0][1] == "hf/qwen2.5-coder-1.5b"
    assert llamadas[0][2]["autorizado_por_chat"] is True
    assert llamadas[0][2]["aprobado_por"] is None
    assert r["aprobacion"] is False


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


# ---------- status: result.swe (disponibilidad real que consume el selector) ----------
def _status(c, clave=CLAVE):
    return c.post("/invoke", json={"action": "status"}, headers={"X-API-Key": clave})


def test_status_emite_swe_con_el_formato_del_contrato(entorno, monkeypatch, tmp_path):
    _, _, c = entorno
    for v in ("RIU_CODEX_BIN", "RIU_CODEX_BASE_URL", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_DOCKER_BIN", "RIU_CLAUDE_BIN", "RIU_CLAUDE_PASARELA_URL", "RIU_CLAUDE_PASARELA_MODELO",
              "OPENCLAW_GATEWAY_TOKEN", "SWECODE_URL_S1", "SWECODE_URL_S2", "SWECODE_URL_S3", "GROQ_API_KEY", "NVIDIA_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    for s in ("S1", "S2", "S3"):  # sin variable ahora rigen las URLs publicas por defecto: vacia = "sin servidor configurado"
        monkeypatch.setenv("SWECODE_URL_" + s, "")
    monkeypatch.setenv("PATH", str(tmp_path / "sin-binarios"))
    monkeypatch.setenv("RIU_SWE_SONDA_MODELOS", "0")
    opencode = tmp_path / "opencode"; opencode.write_text("#!/bin/sh\nexit 0\n"); opencode.chmod(0o755)
    monkeypatch.setenv("RIU_OPENCODE_BIN", str(opencode))
    monkeypatch.setenv("SWECODE_URL_S1", "http://127.0.0.1:9101/v1")
    swe = _status(c).json()["result"]["swe"]
    assert set(swe) == {"agentes", "workflows", "modelos"}
    assert {k: swe["agentes"]["opencode"][k] for k in ("disponible", "motivo")} == {"disponible": True, "motivo": ""} and swe["agentes"]["opencode"]["estado"] == "DISPONIBLE"  # R6: campos nuevos (estado, veredicto...) ademas del contrato antiguo
    assert swe["agentes"]["codex"]["disponible"] is False and swe["agentes"]["codex"]["motivo"]
    assert swe["workflows"]["individual"]["disponible"] is True and swe["workflows"]["liquid_mirror"]["disponible"] is False
    assert swe["modelos"]["hf/lfm2.5-350m"]["disponible"] is False and swe["modelos"]["hf/lfm2.5-350m"]["estado"] == "SIN VERIFICAR"  # R6: URL configurada pero sin sonda = SIN VERIFICAR, no DISPONIBLE
    assert swe["modelos"]["groq/qwen/qwen3.8-27b"]["disponible"] is False and swe["modelos"]["groq/qwen/qwen3.8-27b"]["estado"] == "NO CONFIGURADO"
    assert not (tmp_path / "opencode.lanzado").exists()


def test_status_sigue_exigiendo_clave_y_no_revela_claves(entorno, monkeypatch):
    _, _, c = entorno
    assert _status(c, "mala").status_code == 401
    monkeypatch.setenv("GROQ_API_KEY", "gsk_clave-falsa-de-prueba-1234567890"); monkeypatch.setenv("NVIDIA_API_KEY_2", "nvapi-clave-falsa-de-prueba-1234567890")
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "token-gateway-falso"); monkeypatch.setenv("RIU_SWE_SONDA_MODELOS", "0")
    cuerpo = _status(c).text
    assert "gsk_" not in cuerpo and "nvapi-" not in cuerpo and "token-gateway-falso" not in cuerpo and CLAVE not in cuerpo
    m = json.loads(cuerpo)["result"]["swe"]["modelos"]["groq/qwen/qwen3.8-27b"]
    assert m["disponible"] is False and m["estado"] == "SIN VERIFICAR" and m["intentable"] is True  # R6: clave presente sin verificar GET /models no es DISPONIBLE


def test_si_la_disponibilidad_falla_el_status_responde_igual_sin_swe_inventado(entorno):
    _, _, c = entorno
    def rota(**k): raise RuntimeError("boom")
    with patch("agentes.adaptadores.disponibilidad.capacidades", rota):
        r = _status(c).json()
    assert r["status"] == "ok" and r["result"]["servicio"] == "deepseek_harness" and r["result"]["swe"] == {"error": "DISPONIBILIDAD_NO_COMPROBADA"}


def test_el_selector_deja_de_marcar_no_disponible_lo_conectado_y_lo_sigue_marcando_si_no_esta(entorno, monkeypatch, tmp_path):
    """Cadena real: status del Harness -> harness_client.swe_capacidades (saneo del backend YAIWES) -> estadoOpcion de swe-directo.js (el selector)."""
    _, _, c = entorno
    for v in ("RIU_CODEX_BIN", "RIU_CODEX_BASE_URL", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_DOCKER_BIN", "RIU_CLAUDE_BIN", "RIU_CLAUDE_PASARELA_URL", "RIU_CLAUDE_PASARELA_MODELO",
              "OPENCLAW_GATEWAY_TOKEN", "SWECODE_URL_S1", "SWECODE_URL_S2", "SWECODE_URL_S3", "GROQ_API_KEY", "NVIDIA_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    for s in ("S1", "S2", "S3"):  # vacia = sin servidor (sin variable rigen las URLs publicas por defecto)
        monkeypatch.setenv("SWECODE_URL_" + s, "")
    monkeypatch.setenv("PATH", str(tmp_path / "sin-binarios")); monkeypatch.setenv("RIU_SWE_SONDA_MODELOS", "0")
    exe = tmp_path / "opencode"; exe.write_text("#!/bin/sh\nexit 0\n"); exe.chmod(0o755)
    monkeypatch.setenv("RIU_OPENCODE_BIN", str(exe)); monkeypatch.setenv("SWECODE_URL_S1", "http://127.0.0.1:9101/v1")
    from mvp import harness_client
    cap = harness_client.swe_capacidades(_status(c).json())
    cap["harness"] = "ok"
    js = """import * as S from %r; const cap = S.normalizarCapacidades(JSON.parse(process.argv[1]));
      const e = (t, id, m) => S.estadoOpcion(cap, t, id, m).ok;
      console.log(JSON.stringify({opencode: e('agente','opencode','hf/qwen3.5-0.8b'), codex: e('agente','codex'), claude: e('agente','claude-code'), openclaw: e('agente','openclaw'),
        individual: e('workflow','individual'), swe_code: e('workflow','swe_code'), liquid: e('workflow','liquid_mirror'), hf: e('modelo','hf/lfm2.5-350m'), groq: e('modelo','groq/qwen/qwen3.8-27b')}));""" % str(RAIZ_CHAT_ROUTER / "chat" / "frontend" / "swe-directo.js")
    r = subprocess.run([NODE, "--input-type=module", "-e", js, json.dumps(cap)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    vista = json.loads(r.stdout)
    assert vista == {"opencode": True, "codex": False, "claude": False, "openclaw": False, "individual": True, "swe_code": False, "liquid": False, "hf": True, "groq": False}  # R6: hf con URL pero sin sonda = SIN VERIFICAR (disponible False, intentable True): harness_client ya reenvia estado/intentable y el selector lo deja INTENTAR mostrando su estado real
    hf = cap["modelos"]["hf/lfm2.5-350m"]
    assert hf["disponible"] is False and hf["estado"] == "SIN VERIFICAR" and hf["intentable"] is True and hf["verificado"] is False, hf  # desconocido jamas se presenta como verificado
    assert cap["agentes"]["codex"]["estado"] == "NO INSTALADO" and cap["agentes"]["codex"]["disponible"] is False


def test_el_harness_reenvia_tarea_id_al_router_para_el_parcial_en_streaming():
    """Chat -> Harness -> Router: el Router fija _TAREA_PARCIAL con el tarea_id de la peticion; sin el, el texto parcial no llega al chat."""
    vistos = []
    def llamar(plugin, accion, datos=None, timeout=0):
        return {"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}}
    def router(accion, datos):
        vistos.append((accion, datos))
        return {"texto": "listo", "tool_calls": [], "finish_reason": "stop"}
    with patch.object(h, "llamar", llamar), patch.object(h, "_router", router):
        h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "x", "tarea_id": "chat-tarea_1/../x"})
        h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "x"})
    chats = [d for a, d in vistos if a == "chat"]
    assert chats[0]["tarea_id"] == "chat-tarea_1x"  # el mismo identificador saneado que usa el diario de la tarea
    assert chats[1]["tarea_id"] == ""  # sin tarea no se inventa una


# ---- Agentes ON/OFF decidido en el servidor TAMBIEN para quien llega por el bridge de OpenClaw (no solo por mvp/app.py) ----
def test_agentes_off_bloquea_avanzar_reanudar_aprobar_e_iniciar_agentico_antes_de_tocar_nada(entorno):
    almacen, llamadas, c = entorno
    assert invocar(c, "swe_iniciar", CONTRATO)["status"] == "ok"  # con Agentes ON todo sigue igual
    almacen.agentes_on = False
    antes = dict(almacen.datos)
    for tool, args in (("swe_avanzar", {"task_id": "yaiwes-001"}), ("swe_reanudar", {"task_id": "yaiwes-001"}),
                       ("swe_aprobar", {"task_id": "yaiwes-001", "op_id": "op-1", "operador": "ana"}),
                       ("swe_iniciar", {**CONTRATO, "task_id": "yaiwes-002"})):
        r = invocar(c, tool, args)
        assert r["status"] == "error" and r["error"] == "AGENTES_APAGADOS", tool
    assert llamadas == [] and almacen.datos == antes, "con Agentes OFF no se ejecuta ni se guarda nada"
    assert invocar(c, "swe_estado", {"task_id": "yaiwes-001"})["status"] == "ok", "estado es solo lectura"
    assert invocar(c, "swe_iniciar", {**CONTRATO, "task_id": "yaiwes-003", "modo_agentico": False})["status"] == "ok", "modo agentico OFF no pide agentes"


def test_si_no_se_puede_comprobar_agentes_on_la_operacion_con_efectos_no_se_ejecuta(entorno):
    almacen, llamadas, c = entorno
    invocar(c, "swe_iniciar", CONTRATO)
    almacen.control_caido = True
    r = invocar(c, "swe_avanzar", {"task_id": "yaiwes-001"})
    assert r["status"] == "error" and r["error"] == "AGENTES_ESTADO_NO_COMPROBADO" and llamadas == []
    almacen.control_caido, almacen.agentes_on = False, "true"  # solo el booleano True cuenta
    assert invocar(c, "swe_avanzar", {"task_id": "yaiwes-001"})["error"] == "AGENTES_APAGADOS"


def test_tools_lock_viaja_por_puente_chat_porque_router_mvp_responde_404(monkeypatch):
    """El Router sirve las acciones de control por /plugins/puente_chat/call/<accion>; /plugins/router_mvp/... es 404 (comprobado contra mvp/app.py)."""
    vistos = []
    monkeypatch.setenv("RIU_ROUTER_URL", "http://127.0.0.1:9")
    monkeypatch.setattr(h, "llamar", lambda plugin, accion, datos, timeout=None: vistos.append((plugin, accion)) or {"tools": [], "ia": True, "agentes_on": True})
    h._exigir_agentes_on()
    assert vistos == [("puente_chat", "tools_lock")]


# ---- metricas extendidas (A5): el Harness las reenvia (TTFT, tokens reales vs estimados, parametros, contexto recortado, tools invalidas) sin secretos ni basura ----
def test_el_harness_reenvia_las_metricas_extendidas_saneadas(monkeypatch):
    metricas = {"stream": True, "ttft_s": 0.4, "ttft_origen": "primer_token", "duracion_s": 2.0, "tokens": 120, "tokens_estimados": False, "origen_tokens": "proveedor", "tokens_tps": None,
                "tokens_por_s": 60.0, "tools_invalidas": 1, "lineas_invalidas": 0, "parametros": {"temperature": 0.2, "ignorados": ["top_k"]}, "contexto_compactado": {"antes": 9000, "despues": 4000},
                "clave": "gsk_" + "a" * 20, "extra_raro": {"x": [1, 2, 3]}}
    monkeypatch.setattr(h, "_router", lambda accion, datos: {"texto": "hola", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "nvidia/z-ai/glm-5.3", "metricas": metricas})
    monkeypatch.setattr(h, "_bridge_url", lambda: "")
    monkeypatch.setattr(h, "llamar", lambda plugin, accion, datos, timeout=None: {"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}})
    r = h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "nvidia/z-ai/glm-5.3"})
    m = r["metricas"]
    assert (m["origen_tokens"], m["ttft_origen"], m["tokens_estimados"], m["tools_invalidas"]) == ("proveedor", "primer_token", False, 1)
    assert m["parametros"] == {"temperature": 0.2, "ignorados": ["top_k"]} and m["contexto_compactado"] == {"antes": 9000, "despues": 4000}
    assert "clave" not in m and "extra_raro" not in m, "solo claves conocidas; nada de campos arbitrarios ni secretos"
    assert "gsk_" not in json.dumps(r)
    monkeypatch.setattr(h, "_router", lambda accion, datos: {"texto": "hola", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "m"})
    assert "metricas" not in h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "m"}), "sin metricas del Router no se inventan"
