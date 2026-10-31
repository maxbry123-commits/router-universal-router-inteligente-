"""Maquina de estados SWE (swe_iniciar/avanzar/estado/aprobar/reanudar) con almacen en memoria y agentes/servidores FALSOS.
Estados: PENDIENTE|EJECUTANDO|REQUIERE_APROBACION|RECONCILIAR|CONTINUAR|VERIFICANDO|DONE|GAP."""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from agentes.adaptadores import workflows as wf
from agentes.adaptadores.dispatcher import AgenteError

SECRETO = re.compile(r"(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,})")
ESTADOS = {"PENDIENTE", "EJECUTANDO", "REQUIERE_APROBACION", "RECONCILIAR", "CONTINUAR", "VERIFICANDO", "DONE", "GAP"}


class Mundo:
    """Almacen en memoria + doble de agentes/servidores. Registra todo lo que pasa para afirmar sobre efectos."""
    def __init__(self):
        self.almacen, self.diarios = {}, {}
        self.falla_guardar = lambda nombre: False
        self.guardados, self.agentes, self.servidores = [], [], []
        self.respuesta_agente = None
        self.respuesta_servidor = None
        self.llm_llamadas = []

    def guardar(self, args):
        if self.falla_guardar(args["nombre"]):
            raise RuntimeError("Router no confirmo almacenamiento HF")
        assert not SECRETO.search(args["valor"]), "se intento guardar una credencial"
        self.almacen[args["nombre"]] = args["valor"]
        self.guardados.append(args["nombre"])
        return {"nombre": args["nombre"], "destino": "hf", "commit": None}

    def leer(self, args):
        if args["nombre"] not in self.almacen:
            raise RuntimeError("Router HTTP 404: fallo de lectura HF: no existe " + args["nombre"])
        return {"nombre": args["nombre"], "valor": self.almacen[args["nombre"]]}

    def agente(self, agente, tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
        self.agentes.append({"agente": agente, "tarea_id": tarea_id, "modelo": modelo, "objetivo": objetivo, "contexto": contexto, "permisos": permisos, "checkpoint": checkpoint})
        if self.respuesta_agente:
            r = self.respuesta_agente(agente, len(self.agentes))
            if isinstance(r, Exception):
                raise r
            if r is not None:
                return r
        return {"ok": True, "agente": agente, "task_id": tarea_id, "resultado": "hecho por " + agente, "herramientas": ["t"], "evidencias": ["e:" + agente],
                "recibo": "%s:%s:r%d" % (agente, tarea_id, len(self.agentes)), "exit_code": 0}

    def servidor(self, servidor, modelo, mensajes):
        self.servidores.append((servidor, modelo, mensajes))
        if self.respuesta_servidor:
            r = self.respuesta_servidor(servidor)
            if isinstance(r, Exception):
                raise r
            return r
        return {"texto": "texto de %s" % servidor, "servidor": servidor, "url": "https://%s.example.test/v1" % servidor.lower(), "host": "%s.example.test" % servidor.lower(),
                "modelo_respuesta": modelo}

    def llm(self, cuerpo):
        self.llm_llamadas.append(cuerpo)
        return {"texto": "respuesta individual", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": [], "modelo_respuesta": "lfm2.5-350m"}

    def ctx(self):
        efectos = []
        self.efectos = efectos
        def con_efectos(nombre, args):
            efectos.append(nombre)
            return nombre in ("swe_agente", "llm")
        return wf.Contexto(
            guardar=self.guardar, leer=self.leer, llm=self.llm, router=lambda *a, **k: {}, con_efectos=con_efectos,
            diario=lambda t: json.loads(self.diarios.get(t, "{}")),
            anotar=lambda t, d: self.diarios.__setitem__(t, json.dumps(d)),
            llave=lambda nombre, args: nombre + ":" + json.dumps(args, sort_keys=True),
            secreto=SECRETO, ejecutar_agente=self.agente, servidor_llm=self.servidor, operadores=lambda: {"ana", "luis"})


@pytest.fixture
def mundo(monkeypatch, tmp_path):
    (tmp_path / "ws" / "yaiwes").mkdir(parents=True)
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", str(tmp_path / "ws"))
    return Mundo()


def contrato(**kw):
    base = {"task_id": "yaiwes-001", "origen": "yaiwes", "mensaje": "Revisar proyecto", "workflow": "swe_code", "modelo_responde": "hf/lfm2.5-350m",
            "modelo_lector": "hf/lfm2.5-350m", "modelo_tool": "hf/qwen2.5-coder-1.5b", "modelo_revisor": "hf/qwen3.5-0.8b", "agente_responde": "openclaw",
            "agente_tool": "swe-agent", "agente_verificador": "openhands", "modo_agentico": True, "aprobacion": False, "sesion": "chat-001", "proyecto": "yaiwes"}
    base.update(kw)
    return base


def estado_guardado(m, task="yaiwes-001"):
    ruta = json.loads(m.almacen["swe/indice/%s.json" % task])["ruta"]
    return json.loads(m.almacen[ruta])


def aprobar_y_avanzar(m, c, task="yaiwes-001"):
    r = wf.swe_avanzar({"task_id": task}, c)
    assert r["estado"] == "REQUIERE_APROBACION", r
    op = r["pendiente_aprobacion"]["op_id"]
    a = wf.swe_aprobar({"task_id": task, "op_id": op, "operador": "ana"}, c)
    assert a["estado"] in ("CONTINUAR", "VERIFICANDO")
    return wf.swe_avanzar({"task_id": task}, c)


# ---------- constantes de workflow ----------
def test_workflows_exactos():
    assert wf.WORKFLOW_SWE_CODE == [
        {"paso": "escribe", "agente": "codex", "modelo": "hf/qwen2.5-coder-1.5b"}, {"paso": "revisa", "agente": "opencode", "modelo": "hf/qwen3.5-0.8b"},
        {"paso": "ejecuta", "agente": "seleccionado", "modelo": "hf/lfm2.5-350m"}, {"paso": "verifica", "agente": "openhands", "modelo": "hf/lfm2.5-350m"}]
    assert wf.WORKFLOW_LIQUID_MIRROR == [
        {"paso": "liquid1", "modelo": "hf/lfm2.5-350m", "servidor": "S2", "funcion": "lee_analiza"}, {"paso": "handoff", "funcion": "transferir_contexto"},
        {"paso": "liquid2", "modelo": "hf/lfm2.5-350m", "servidor": "S3", "funcion": "ejecutar"}, {"paso": "verifica", "funcion": "verificar"}]


# ---------- iniciar ----------
def test_iniciar_guarda_pendiente_con_todos_los_campos_y_no_confia_en_aprobacion(mundo):
    r = wf.swe_iniciar(contrato(aprobacion=True), mundo.ctx())
    assert r["ok"] is True and r["estado"] == "PENDIENTE" and r["task_id"] == "yaiwes-001"
    e = estado_guardado(mundo)
    for campo in ("task_id", "origen", "workflow", "modelo_responde", "modelo_lector", "modelo_tool", "agente_responde", "agente_tool", "paso_actual",
                  "pasos_terminados", "handoff", "resultado_tool", "evidencia", "estado", "aprobacion", "fecha"):
        assert campo in e, campo
    assert e["estado"] in ESTADOS and e["aprobacion"] is False and e["paso_actual"] == 0 and e["pasos_terminados"] == []
    assert json.loads(mundo.almacen["swe/indice/yaiwes-001.json"])["ruta"] == "swe/yaiwes/yaiwes/chat-001/yaiwes-001.json"


def test_iniciar_acepta_el_contrato_dentro_de_tarea_y_valida(mundo):
    wf.swe_iniciar({"tarea": contrato()}, mundo.ctx())
    with pytest.raises(ValueError, match="AGENTE_NO_REGISTRADO"):
        wf.swe_iniciar(contrato(task_id="otro", agente_tool="bash"), mundo.ctx())
    with pytest.raises(ValueError, match="CAMPOS_DESCONOCIDOS"):
        wf.swe_iniciar(contrato(task_id="otro2", estado="DONE"), mundo.ctx())


def test_iniciar_es_idempotente_y_no_pisa_otra_identidad(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    n = len(mundo.guardados)
    r = wf.swe_iniciar(contrato(), c)
    assert r["estado"] == "PENDIENTE" and r["ya_existia"] is True and len(mundo.guardados) == n
    with pytest.raises(ValueError, match="TASK_ID_EN_USO"):
        wf.swe_iniciar(contrato(origen="openclaw"), c)
    with pytest.raises(ValueError, match="TASK_ID_EN_USO"):
        wf.swe_iniciar(contrato(sesion="chat-002"), c)


def test_iniciar_con_fallo_de_guardado_devuelve_error_de_persistencia(mundo):
    mundo.falla_guardar = lambda n: True
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_iniciar(contrato(), mundo.ctx())


def test_iniciar_si_el_indice_no_se_puede_leer_no_adivina(mundo):
    c = mundo.ctx()
    def leer(args):
        raise RuntimeError("Router HTTP 502: fallo de lectura HF")
    c.leer = leer
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_iniciar(contrato(), c)
    assert mundo.almacen == {}


# ---------- SWE CODE: cuatro pasos con aprobacion ----------
def test_swe_code_cuatro_pasos_hasta_done(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "REQUIERE_APROBACION" and mundo.agentes == []  # nada con efectos sin operador
    assert r["pendiente_aprobacion"]["paso"] == "escribe" and r["pendiente_aprobacion"]["agente"] == "codex"
    op = wf.swe_estado({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "CONTINUAR" and r["paso_actual"] == 1
    assert mundo.agentes[0]["agente"] == "codex" and mundo.agentes[0]["modelo"] == "hf/qwen2.5-coder-1.5b"
    assert mundo.agentes[0]["permisos"]["escritura"] is True and mundo.agentes[0]["permisos"]["aprobado_por"] == "ana"
    assert mundo.agentes[0]["permisos"]["directorio"].endswith("/ws/yaiwes")
    assert mundo.agentes[0]["objetivo"].startswith("Revisar proyecto") and "RIU" not in json.dumps(mundo.agentes[0]["checkpoint"])
    for esperado in ("opencode", "swe-agent", "openhands"):
        r = aprobar_y_avanzar(mundo, c)
        assert mundo.agentes[-1]["agente"] == esperado, (esperado, r)
    assert r["estado"] == "DONE" and [a["agente"] for a in mundo.agentes] == ["codex", "opencode", "swe-agent", "openhands"]
    assert [a["modelo"] for a in mundo.agentes] == ["hf/qwen2.5-coder-1.5b", "hf/qwen3.5-0.8b", "hf/lfm2.5-350m", "hf/lfm2.5-350m"]
    # cada etapa recibe el resultado confirmado de la anterior
    assert "hecho por codex" in mundo.agentes[1]["contexto"] and "hecho por opencode" in mundo.agentes[2]["contexto"]
    e = estado_guardado(mundo)
    assert e["estado"] == "DONE" and len(e["pasos_terminados"]) == 4 and all(p["recibo"] for p in e["pasos_terminados"])
    assert all(o["estado"] == "CONFIRMADA" for o in e["operaciones"].values()) and e["resultado_tool"] == "hecho por swe-agent"
    n = len(mundo.agentes)
    assert wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["estado"] == "DONE" and len(mundo.agentes) == n  # no se repite nada


def test_aprobacion_requiere_operador_identificado(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    for args, codigo in [({"task_id": "yaiwes-001", "op_id": op}, "OPERADOR_REQUERIDO"), ({"task_id": "yaiwes-001", "op_id": op, "operador": "intruso"}, "OPERADOR_NO_AUTORIZADO"),
                         ({"task_id": "yaiwes-001", "op_id": op, "operador": "x y"}, "OPERADOR_REQUERIDO"), ({"task_id": "yaiwes-001", "op_id": "otra", "operador": "ana"}, "OP_NO_PENDIENTE"),
                         ({"task_id": "yaiwes-001", "op_id": op, "operador": "ana", "aprobacion": True}, None)]:
        if codigo is None:
            continue
        with pytest.raises(ValueError, match=codigo):
            wf.swe_aprobar(args, c)
    assert wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["estado"] == "REQUIERE_APROBACION" and mundo.agentes == []


def test_sin_lista_de_operadores_nadie_aprueba(mundo):
    c = mundo.ctx()
    c.operadores = lambda: set()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    with pytest.raises(ValueError, match="APROBADORES_NO_CONFIGURADOS"):
        wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)


def test_aprobar_fuera_de_estado_de_aprobacion(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    with pytest.raises(ValueError, match="ESTADO_NO_APROBABLE"):
        wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": "x", "operador": "ana"}, c)


def test_modo_agentico_apagado_no_activa_agentes(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(modo_agentico=False), c)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "MODO_AGENTICO_APAGADO" and mundo.agentes == []


def test_agente_no_instalado_es_gap_sin_ejecucion_y_se_reintenta_sin_repetir_aprobacion(mundo):
    c = mundo.ctx()
    no = {"ok": False, "agente": "codex", "codigo": "AGENTE_NO_INSTALADO", "error": "falta codex", "efectos_posibles": False}
    mundo.respuesta_agente = lambda a, n: AgenteError("EJECUCION_AGENTE_FALLIDA", no) if n == 1 else None
    wf.swe_iniciar(contrato(), c)
    r = aprobar_y_avanzar(mundo, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "AGENTE_NO_INSTALADO" and r["paso_actual"] == 0
    e = estado_guardado(mundo)
    assert list(e["operaciones"].values())[0]["estado"] == "FALLIDA" and e["pasos_terminados"] == []
    r = wf.swe_reanudar({"task_id": "yaiwes-001"}, c)  # ya se instalo: reintenta el mismo paso
    assert r["estado"] == "CONTINUAR" and r["paso_actual"] == 1 and len(mundo.agentes) == 2


def test_fallo_con_efectos_posibles_pasa_a_reconciliar_y_no_reintenta(mundo):
    c = mundo.ctx()
    mal = {"ok": False, "agente": "codex", "codigo": "AGENTE_TIMEOUT", "error": "timeout", "efectos_posibles": True}
    mundo.respuesta_agente = lambda a, n: AgenteError("EJECUCION_AGENTE_FALLIDA", mal)
    wf.swe_iniciar(contrato(), c)
    r = aprobar_y_avanzar(mundo, c)
    assert r["estado"] == "RECONCILIAR" and len(mundo.agentes) == 1
    assert wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["estado"] == "RECONCILIAR"
    assert wf.swe_reanudar({"task_id": "yaiwes-001"}, c)["estado"] == "RECONCILIAR"
    assert len(mundo.agentes) == 1  # NO se repitio el commit/despliegue
    op = r["pendiente_reconciliacion"]["op_id"]
    with pytest.raises(ValueError, match="OPERADOR_REQUERIDO"):
        wf.swe_reanudar({"task_id": "yaiwes-001", "reconciliacion": {"op_id": op, "resultado": "no_ejecutada", "evidencia": "git log limpio"}}, c)
    with pytest.raises(ValueError, match="RECONCILIACION_INVALIDA"):
        wf.swe_reanudar({"task_id": "yaiwes-001", "operador": "ana", "reconciliacion": {"op_id": op, "resultado": "quiza", "evidencia": "x"}}, c)
    with pytest.raises(ValueError, match="RECONCILIACION_INVALIDA"):
        wf.swe_reanudar({"task_id": "yaiwes-001", "operador": "ana", "reconciliacion": {"op_id": op, "resultado": "confirmada", "evidencia": ""}}, c)
    r = wf.swe_reanudar({"task_id": "yaiwes-001", "operador": "ana", "reconciliacion": {"op_id": op, "resultado": "no_ejecutada", "evidencia": "git log sin commits nuevos"}}, c)
    assert r["estado"] == "REQUIERE_APROBACION"  # vuelve a pedir aprobacion antes de repetir
    mundo.respuesta_agente = None
    r = aprobar_y_avanzar(mundo, c)
    assert r["estado"] == "CONTINUAR" and len(mundo.agentes) == 2


def test_reconciliar_confirmada_avanza_sin_reejecutar(mundo):
    c = mundo.ctx()
    mal = {"ok": False, "agente": "codex", "codigo": "AGENTE_TIMEOUT", "error": "timeout", "efectos_posibles": True}
    mundo.respuesta_agente = lambda a, n: AgenteError("EJECUCION_AGENTE_FALLIDA", mal)
    wf.swe_iniciar(contrato(), c)
    r = aprobar_y_avanzar(mundo, c)
    op = r["pendiente_reconciliacion"]["op_id"]
    r = wf.swe_reanudar({"task_id": "yaiwes-001", "operador": "luis", "reconciliacion": {"op_id": op, "resultado": "confirmada", "evidencia": "commit abc123 presente en main"}}, c)
    assert r["paso_actual"] == 1 and r["estado"] == "REQUIERE_APROBACION" and len(mundo.agentes) == 1  # sigue con el paso 2, pero pide aprobacion
    paso = estado_guardado(mundo)["pasos_terminados"][0]
    assert paso["reconciliado_por"] == "luis" and paso["recibo"] is None and "abc123" in paso["resultado"]


def test_si_falla_guardar_la_confirmacion_se_detiene_y_luego_reconcilia(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    estado_antes = mundo.almacen[json.loads(mundo.almacen["swe/indice/yaiwes-001.json"])["ruta"]]
    cuenta = {"n": 0}
    def falla_segunda(nombre):
        if nombre.endswith("yaiwes-001.json") and "indice" not in nombre:
            cuenta["n"] += 1
            return cuenta["n"] == 2  # 1: INICIADA ok; 2: confirmacion falla
        return False
    mundo.falla_guardar = falla_segunda
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert len(mundo.agentes) == 1
    mundo.falla_guardar = lambda n: False
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)  # el diario tiene la confirmacion real: se adopta, no se reejecuta
    assert len(mundo.agentes) == 1 and r["paso_actual"] == 1 and r["estado"] == "CONTINUAR"
    assert estado_guardado(mundo)["pasos_terminados"][0]["recibo"].startswith("codex:")


def test_si_falla_guardar_antes_de_ejecutar_no_se_ejecuta(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    mundo.falla_guardar = lambda n: True
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert mundo.agentes == []


def test_operacion_iniciada_sin_confirmacion_ni_diario_va_a_reconciliar(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    ruta = json.loads(mundo.almacen["swe/indice/yaiwes-001.json"])["ruta"]
    e = json.loads(mundo.almacen[ruta]); e["estado"] = "EJECUTANDO"  # el proceso murio a mitad, con la operacion ya marcada INICIADA
    e["operaciones"][op] = {"estado": "INICIADA", "idx": 0, "paso": "escribe", "agente": "codex", "modelo": "hf/qwen2.5-coder-1.5b", "llave": "k", "intentos": 1}
    mundo.almacen[ruta] = json.dumps(e)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "RECONCILIAR" and mundo.agentes == []


def test_la_aprobacion_no_sirve_si_cambia_el_objetivo(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    r1 = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    ruta = json.loads(mundo.almacen["swe/indice/yaiwes-001.json"])["ruta"]
    e = json.loads(mundo.almacen[ruta]); e["mensaje"] = "Borrar todo"; mundo.almacen[ruta] = json.dumps(e)
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": r1["pendiente_aprobacion"]["op_id"], "operador": "ana"}, c)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "REQUIERE_APROBACION" and mundo.agentes == [] and r["pendiente_aprobacion"]["op_id"] != r1["pendiente_aprobacion"]["op_id"]


def test_resultados_se_guardan_sin_credenciales(mundo):
    c = mundo.ctx()
    mundo.respuesta_agente = lambda a, n: {"ok": True, "agente": a, "task_id": "yaiwes-001", "resultado": "token sk-abcdefghijklmnop1234 listo", "herramientas": [], "evidencias": [], "recibo": "r1", "exit_code": 0}
    wf.swe_iniciar(contrato(), c)
    aprobar_y_avanzar(mundo, c)  # el almacen falso afirma que no llego ninguna credencial
    assert "[REDACTADO]" in json.dumps(estado_guardado(mundo)) and "sk-abcdefghijklmnop1234" not in json.dumps(estado_guardado(mundo))


def test_la_ejecucion_se_anota_en_el_diario_con_con_efectos(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    aprobar_y_avanzar(mundo, c)
    assert "swe_agente" in mundo.efectos
    diario = json.loads(mundo.diarios["yaiwes-001"])
    assert len(diario) == 1 and list(diario.values())[0]["estado"] == "CONFIRMADA"


def test_workspace_no_configurado_es_gap_antes_de_pedir_aprobacion(mundo, monkeypatch):
    monkeypatch.delenv("RIU_SWE_WORKSPACE_RAIZ")
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "WORKSPACE_NO_CONFIGURADO" and mundo.agentes == []


def test_workspace_no_puede_escapar_de_la_raiz(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(proyecto="../../etc"), c)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] in ("PROYECTO_INVALIDO", "WORKSPACE_NO_CONFIGURADO") and mundo.agentes == []


# ---------- estado / identidad de sesion ----------
def test_estado_lee_del_almacen_y_respeta_la_identidad(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    s = wf.swe_estado({"task_id": "yaiwes-001"}, c)
    assert s["estado"] == "PENDIENTE" and s["workflow"] == "swe_code" and [p["paso"] for p in s["plan"]] == ["escribe", "revisa", "ejecuta", "verifica"]
    assert wf.swe_estado({"task_id": "yaiwes-001", "origen": "yaiwes", "proyecto": "yaiwes", "sesion": "chat-001"}, c)["estado"] == "PENDIENTE"
    with pytest.raises(ValueError, match="TAREA_NO_COINCIDE"):
        wf.swe_estado({"task_id": "yaiwes-001", "sesion": "otra-sesion"}, c)
    with pytest.raises(ValueError, match="TAREA_NO_COINCIDE"):
        wf.swe_estado({"task_id": "yaiwes-001", "origen": "openclaw"}, c)
    with pytest.raises(ValueError, match="TAREA_NO_ENCONTRADA"):
        wf.swe_estado({"task_id": "no-existe"}, c)
    with pytest.raises(ValueError, match="TASK_ID_INVALIDO"):
        wf.swe_estado({"task_id": "../x"}, c)


def test_estado_con_almacen_caido_es_error_de_persistencia(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    def leer(args):
        raise RuntimeError("Router HTTP 502: caido")
    c.leer = leer
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_estado({"task_id": "yaiwes-001"}, c)


def test_mismo_contrato_para_openclaw_usa_su_propio_espacio(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(task_id="openclaw-001", origen="openclaw", sesion="openclaw-001", proyecto="swe-code"), c)
    assert json.loads(mundo.almacen["swe/indice/openclaw-001.json"])["ruta"] == "swe/openclaw/swe-code/openclaw-001/openclaw-001.json"


# ---------- Liquid Mirror ----------
def lm(**kw):
    return contrato(workflow="liquid_mirror", task_id="openclaw-001", origen="openclaw", sesion="openclaw-001", proyecto="yaiwes", modelo_tool="hf/lfm2.5-350m", **kw)


def test_liquid_mirror_s2_lee_handoff_confirmado_s3_ejecuta_y_verifica(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)  # liquid1 en S2 (solo lectura: sin aprobacion)
    assert mundo.servidores[0][0] == "S2" and mundo.servidores[0][1] == "lfm2.5-350m" and r["estado"] == "CONTINUAR"
    assert r["pasos_terminados"][0]["recibo"].startswith("liquid:S2:s2.example.test:")
    assert not any(n.endswith("openclaw-001.handoff.json") for n in mundo.almacen)  # aun no hay handoff
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)  # handoff
    h = r["handoff"]
    assert h["confirmado"] is True and h["servidor_origen"] == "S2" and h["servidor_destino"] == "S3" and len(h["sha256"]) == 64
    assert "swe/openclaw/yaiwes/openclaw-001/openclaw-001.handoff.json" in mundo.almacen
    assert len(mundo.servidores) == 1  # el handoff no llama a ningun modelo
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)  # liquid2 en S3, con el handoff como unico contexto
    assert mundo.servidores[1][0] == "S3" and "texto de S2" in json.dumps(mundo.servidores[1][2]) and r["pasos_terminados"][2]["recibo"].startswith("liquid:S3:s3.example.test:")
    assert mundo.agentes == []
    r = aprobar_y_avanzar(mundo, c, "openclaw-001")  # ejecuta con el agente elegido (swe-agent): efectos -> aprobacion
    assert mundo.agentes[0]["agente"] == "swe-agent" and "texto de S3" in mundo.agentes[0]["contexto"]
    r = aprobar_y_avanzar(mundo, c, "openclaw-001")  # verifica con openhands
    assert mundo.agentes[1]["agente"] == "openhands" and r["estado"] == "DONE"
    assert r["ejecucion_s2_s3"] == "secuencial"  # no se afirma paralelismo


def test_liquid2_no_ejecuta_sin_handoff_confirmado(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c); wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    ruta = "swe/openclaw/yaiwes/openclaw-001/openclaw-001.handoff.json"
    mundo.almacen[ruta] = json.dumps({"resumen": "manipulado"})  # el handoff guardado ya no coincide con el confirmado
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "HANDOFF_NO_CONFIRMADO" and len(mundo.servidores) == 1


def test_handoff_falla_si_no_se_puede_releer(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    mundo.falla_guardar = lambda n: n.endswith(".handoff.json")
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert estado_guardado(mundo, "openclaw-001")["handoff"] is None


def test_liquid_servidor_no_configurado_o_caido_no_cambia_de_servidor(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    mundo.respuesta_servidor = lambda s: ValueError("LIQUID_SERVIDOR_NO_CONFIGURADO")
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "LIQUID_SERVIDOR_NO_CONFIGURADO" and [s[0] for s in mundo.servidores] == ["S2"]
    mundo.respuesta_servidor = None
    r = wf.swe_reanudar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "CONTINUAR" and r["pasos_terminados"][0]["recibo"].startswith("liquid:S2:")


def test_liquid_modo_agentico_apagado_termina_en_gap_sin_verificacion_de_agente(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(lm(modo_agentico=False), c)
    for _ in range(3):
        wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "MODO_AGENTICO_APAGADO" and mundo.agentes == []


# ---------- individual ----------
def test_individual_usa_llm_del_harness_y_guarda(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(workflow="individual", task_id="ind-1", modo_agentico=False, modelo_responde="groq/qwen/qwen3.8-27b"), c)
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert r["estado"] == "DONE" and mundo.agentes == []
    cuerpo = mundo.llm_llamadas[0]
    assert cuerpo["modelo"] == "groq/qwen/qwen3.8-27b" and cuerpo["tarea_id"] == "ind-1" and cuerpo["messages"][-1]["content"] == "Revisar proyecto"
    assert estado_guardado(mundo, "ind-1")["pasos_terminados"][0]["resultado"] == "respuesta individual"


# ---------- servidores S2/S3 reales (HTTP local) ----------
class Falso(BaseHTTPRequestHandler):
    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).visto.append((self.server.server_port, self.path, cuerpo))
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"model": cuerpo["model"], "choices": [{"message": {"role": "assistant", "content": "puerto %d" % self.server.server_port}, "finish_reason": "stop"}]}).encode())
    def log_message(self, *a): pass


@pytest.fixture
def servidores(monkeypatch):
    Falso.visto = []
    ss = []
    for n in ("S2", "S3"):
        s = HTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=s.serve_forever, daemon=True).start(); ss.append(s)
        monkeypatch.setenv("SWECODE_URL_" + n, "http://127.0.0.1:%d/v1" % s.server_port)
    monkeypatch.delenv("SWECODE_URL_S1", raising=False)
    yield ss
    for s in ss: s.shutdown(); s.server_close()


def test_llamar_servidor_identifica_el_servidor_real(servidores):
    a = wf.llamar_servidor("S2", "lfm2.5-350m", [{"role": "user", "content": "hola"}])
    b = wf.llamar_servidor("S3", "lfm2.5-350m", [{"role": "user", "content": "hola"}])
    assert a["servidor"] == "S2" and a["host"] == "127.0.0.1:%d" % servidores[0].server_port and a["texto"] == "puerto %d" % servidores[0].server_port
    assert b["host"] == "127.0.0.1:%d" % servidores[1].server_port and a["host"] != b["host"]
    assert [v[0] for v in Falso.visto] == [servidores[0].server_port, servidores[1].server_port] and Falso.visto[0][1] == "/v1/chat/completions"


def test_llamar_servidor_sin_url_no_usa_otro(monkeypatch, servidores):
    monkeypatch.delenv("SWECODE_URL_S2")
    monkeypatch.setenv("SWECODE_URL_S1", "http://127.0.0.1:%d/v1" % servidores[1].server_port)
    with pytest.raises(ValueError, match="LIQUID_SERVIDOR_NO_CONFIGURADO"):
        wf.llamar_servidor("S2", "lfm2.5-350m", [{"role": "user", "content": "x"}])
    assert Falso.visto == []


def test_llamar_servidor_exige_servidores_independientes(monkeypatch, servidores):
    monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:%d/v1" % servidores[0].server_port)
    with pytest.raises(ValueError, match="LIQUID_SERVIDORES_NO_INDEPENDIENTES"):
        wf.llamar_servidor("S3", "lfm2.5-350m", [{"role": "user", "content": "x"}])


def test_llamar_servidor_url_insegura(monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://ejemplo.invalid/v1")
    monkeypatch.setenv("SWECODE_URL_S3", "https://s3.example.test/v1")
    with pytest.raises(ValueError, match="LIQUID_URL_INVALIDA"):
        wf.llamar_servidor("S2", "lfm2.5-350m", [{"role": "user", "content": "x"}])


# ---------- Liquid Mirror: finish_reason=length (handoff truncado NO se confirma) ----------
def srv_length(mundo, secuencia):
    """Respuestas del servidor Liquid por llamada: lista de (texto, finish_reason) por servidor."""
    cuentas = {"S2": 0, "S3": 0}
    def f(servidor):
        i = cuentas[servidor]; cuentas[servidor] += 1
        texto, fin = secuencia[servidor][min(i, len(secuencia[servidor]) - 1)]
        return {"texto": texto, "servidor": servidor, "url": "https://%s.example.test/v1" % servidor.lower(), "host": "%s.example.test" % servidor.lower(),
                "modelo_respuesta": "lfm2.5-350m", "finish_reason": fin}
    mundo.respuesta_servidor = f


def test_liquid1_cortado_por_length_pide_continuacion_y_se_une(mundo):
    c = mundo.ctx(); srv_length(mundo, {"S2": [("parte uno, ", "length"), ("parte dos.", "stop")], "S3": [("plan", "stop")]})
    wf.swe_iniciar(lm(), c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert [s[0] for s in mundo.servidores] == ["S2", "S2"]
    cont = mundo.servidores[1][2]  # la continuacion lleva lo ya dicho y pide seguir donde se corto
    assert cont[-2] == {"role": "assistant", "content": "parte uno, "} and "Continua exactamente" in cont[-1]["content"]
    assert r["pasos_terminados"][0]["resultado"] == "parte uno, parte dos." and not r["pasos_terminados"][0].get("parcial")
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["handoff"]["confirmado"] is True and not r["handoff"].get("parcial")


def test_liquid1_sigue_cortado_tras_las_continuaciones_handoff_parcial_y_liquid2_no_corre(mundo):
    c = mundo.ctx(); srv_length(mundo, {"S2": [("corta", "length")], "S3": [("plan", "stop")]})
    wf.swe_iniciar(lm(), c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert 1 < len(mundo.servidores) <= 3 and r["pasos_terminados"][0]["parcial"] is True  # solo 2 continuaciones maximo
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)  # handoff
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "HANDOFF_PARCIAL"
    assert r["handoff"]["confirmado"] is False and r["handoff"]["parcial"] is True
    n = len(mundo.servidores)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c); r = wf.swe_reanudar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "HANDOFF_PARCIAL" and len(mundo.servidores) == n, "ni avanzar ni reanudar ejecutan Liquid 2"
    assert all(s[0] == "S2" for s in mundo.servidores) and mundo.agentes == []
    assert estado_guardado(mundo, "openclaw-001")["handoff"]["confirmado"] is False


def test_handoff_mas_largo_que_el_tope_tambien_es_parcial_no_se_recorta_en_silencio(mundo):
    c = mundo.ctx(); srv_length(mundo, {"S2": [("x" * (wf.MAX_TEXTO + 500), "stop")], "S3": [("plan", "stop")]})
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "HANDOFF_PARCIAL" and r["handoff"]["confirmado"] is False
    assert [s[0] for s in mundo.servidores] == ["S2"]


def test_liquid2_cortado_por_length_no_alimenta_al_agente(mundo):
    c = mundo.ctx(); srv_length(mundo, {"S2": [("analisis", "stop")], "S3": [("plan a medias", "length")]})
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c); wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "LIQUID_RESPUESTA_PARCIAL" and r["paso_actual"] == 2 and mundo.agentes == []


def test_servidor_sin_finish_reason_se_trata_como_completo(mundo):
    c = mundo.ctx(); wf.swe_iniciar(lm(), c)  # el doble por defecto no trae finish_reason
    wf.swe_avanzar({"task_id": "openclaw-001"}, c); r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["handoff"]["confirmado"] is True and len(mundo.servidores) == 1


def test_llamar_servidor_devuelve_finish_reason(servidores):
    assert wf.llamar_servidor("S2", "lfm2.5-350m", [{"role": "user", "content": "hola"}])["finish_reason"] == "stop"


def test_llamar_servidor_no_sigue_redirecciones(monkeypatch):
    destino, visto = HTTPServer(("127.0.0.1", 0), Falso), []
    Falso.visto = visto
    class Redir(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(307); self.send_header("Location", "http://127.0.0.1:%d/robo" % destino.server_port); self.end_headers()
        def log_message(self, *a): pass
    origen = HTTPServer(("127.0.0.1", 0), Redir)
    for s in (destino, origen): threading.Thread(target=s.serve_forever, daemon=True).start()
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:%d/v1" % origen.server_port); monkeypatch.setenv("SWECODE_URL_S3", "https://s3.example.test/v1")
    try:
        with pytest.raises(RuntimeError, match="LIQUID_LLAMADA_FALLIDA"):
            wf.llamar_servidor("S2", "lfm2.5-350m", [{"role": "user", "content": "x"}])
    finally:
        for s in (destino, origen): s.shutdown(); s.server_close()
    assert visto == [], "el destino de la redireccion no recibio la peticion"


def test_el_estado_guardado_tambien_se_redacta_por_valor_de_variable_sensible(mundo, monkeypatch):
    monkeypatch.setenv("RIU_API_KEY", "valor-largo-de-la-clave-del-harness")
    c = mundo.ctx(); wf.swe_iniciar(contrato(workflow="individual", task_id="ind-9", modo_agentico=False, mensaje="usa valor-largo-de-la-clave-del-harness aqui"), c)
    assert "valor-largo-de-la-clave-del-harness" not in json.dumps(mundo.almacen)
