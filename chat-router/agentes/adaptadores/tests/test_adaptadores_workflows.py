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
        self.respuesta_llm = None
        self.caps = None  # None = todos los agentes disponibles; dict agente -> {"disponible": bool, "motivo": str}

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
                "recibo": "%s:%s:r%d" % (agente, tarea_id, len(self.agentes)), "exit_code": 0, "modelo_usado": modelo}

    def servidor(self, servidor, modelo, mensajes):
        self.servidores.append((servidor, modelo, mensajes))
        if self.respuesta_servidor:
            r = self.respuesta_servidor(servidor)
            if isinstance(r, Exception):
                raise r
            return r
        return {"texto": "texto de %s" % servidor, "servidor": servidor, "url": "https://%s.example.test/v1" % servidor.lower(), "host": "%s.example.test" % servidor.lower(),
                "modelo_respuesta": modelo, "finish_reason": "stop"}

    def llm(self, cuerpo):
        self.llm_llamadas.append(cuerpo)
        if self.respuesta_llm:
            return self.respuesta_llm(len(self.llm_llamadas), cuerpo)
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
            secreto=SECRETO, ejecutar_agente=self.agente, servidor_llm=self.servidor, operadores=lambda: {"ana", "luis"},
            disponibilidad=lambda: self.caps if self.caps is not None else {a: {"disponible": True, "motivo": ""} for a in ("codex", "opencode", "swe-agent", "openhands", "claude-code", "openclaw")})


@pytest.fixture
def mundo(monkeypatch, tmp_path):
    (tmp_path / "ws" / "yaiwes").mkdir(parents=True)
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", str(tmp_path / "ws"))
    monkeypatch.setenv("SWECODE_URL_S2", "https://s2.example.test/v1")  # dos servidores Liquid distintos por defecto (los dobles no hacen HTTP)
    monkeypatch.setenv("SWECODE_URL_S3", "https://s3.example.test/v1")
    wf._LOCKS.clear()
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
    sin_candado = lambda: [x for x in mundo.guardados if "/locks/" not in x]  # noqa: E731
    n = len(sin_candado())
    r = wf.swe_iniciar(contrato(), c)
    assert r["estado"] == "PENDIENTE" and r["ya_existia"] is True and len(sin_candado()) == n
    with pytest.raises(ValueError, match="TASK_ID_EN_USO"):
        wf.swe_iniciar(contrato(origen="openclaw"), c)
    with pytest.raises(ValueError, match="TASK_ID_EN_USO"):
        wf.swe_iniciar(contrato(sesion="chat-002"), c)


def test_iniciar_rechaza_mismo_id_con_otro_objetivo_o_modelo(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    ruta = "swe/yaiwes/yaiwes/chat-001/yaiwes-001.json"
    anterior = mundo.almacen[ruta]
    for cambio in ({"mensaje": "otra tarea"}, {"modelo_tool": "hf/qwen3-0.6b"}, {"workflow": "individual"}):
        with pytest.raises(ValueError, match="TASK_ID_EN_USO"):
            wf.swe_iniciar(contrato(**cambio), c)
        assert mundo.almacen[ruta] == anterior


def test_iniciar_restaura_indice_faltante_sin_reejecutar(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    indice = "swe/indice/yaiwes-001.json"
    ruta = "swe/yaiwes/yaiwes/chat-001/yaiwes-001.json"
    estado = mundo.almacen[ruta]
    del mundo.almacen[indice]
    r = wf.swe_iniciar(contrato(), c)
    assert r["ya_existia"] is True and mundo.almacen[ruta] == estado
    assert json.loads(mundo.almacen[indice])["ruta"] == ruta
    assert mundo.agentes == []


def test_iniciar_no_recrea_estado_perdido_si_hay_indice(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    ruta = "swe/yaiwes/yaiwes/chat-001/yaiwes-001.json"
    del mundo.almacen[ruta]
    with pytest.raises(ValueError, match="TAREA_ESTADO_FALTANTE"):
        wf.swe_iniciar(contrato(), c)
    assert ruta not in mundo.almacen


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
    assert [a["modelo"] for a in mundo.agentes] == ["hf/qwen2.5-coder-1.5b", "hf/qwen3.5-0.8b", "hf/qwen2.5-coder-1.5b", "hf/qwen3.5-0.8b"]  # ejecuta=modelo_tool, verifica=modelo_revisor del contrato
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
        if nombre.endswith("yaiwes-001.json") and "indice" not in nombre and "locks" not in nombre:
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


def test_servidor_sin_finish_reason_no_se_asume_completo(mundo):
    c = mundo.ctx(); srv_length(mundo, {"S2": [("texto sin motivo de fin", None)], "S3": [("plan", "stop")]}); wf.swe_iniciar(lm(), c)  # el servidor no informa finish_reason
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["pasos_terminados"][0]["parcial"] is True and r["pasos_terminados"][0]["finish_reason"] is None
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "HANDOFF_PARCIAL" and r["handoff"]["confirmado"] is False and len(mundo.servidores) == 1


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



# =====================================================================================================
# AUDITORIA 3 / A2 (checklist 80-107, 131-146): Individual, NO_DISPONIBLE, DONE verificado, estados finos, candado entre procesos, finish_reason
# =====================================================================================================
import time


def ind(**kw):
    return contrato(workflow="individual", task_id="ind-1", **kw)


def test_individual_apagado_solo_el_modelo_que_responde_sin_agentes_ni_herramientas(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(ind(modo_agentico=False, modelo_responde="groq/qwen/qwen3.8-27b", agente_tool="codex", modelo_tool="hf/qwen3-0.6b"), c)
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert r["estado"] == "DONE" and mundo.agentes == [] and len(mundo.llm_llamadas) == 1
    b = mundo.llm_llamadas[0]
    assert b["modelo"] == "groq/qwen/qwen3.8-27b" and b["agente_tool"] is False and b["llm_tool"] is False and b["tools"] is False
    assert [p["paso"] for p in r["plan"]] == ["responde"] and r["plan"][0]["agente"] is None
    assert "hf/qwen3-0.6b" not in json.dumps(b)  # modelo_tool no se usa con el modo apagado


def test_individual_encendido_usa_el_agente_seleccionado_y_luego_responde_el_modelo(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(ind(modo_agentico=True, agente_tool="opencode", modelo_tool="hf/qwen3-0.6b", modelo_responde="groq/qwen/qwen3.8-27b"), c)
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert [(p["paso"], p["agente"], p["modelo"]) for p in r["plan"]] == [("ejecuta", "opencode", "hf/qwen3-0.6b"), ("responde", None, "groq/qwen/qwen3.8-27b")]
    assert r["estado"] == "REQUIERE_APROBACION" and mundo.agentes == [] and mundo.llm_llamadas == []  # ni agente ni LLM sin operador
    r = aprobar_y_avanzar(mundo, c, "ind-1")
    assert mundo.agentes[0]["agente"] == "opencode" and mundo.agentes[0]["modelo"] == "hf/qwen3-0.6b"
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert r["estado"] == "DONE" and len(mundo.llm_llamadas) == 1
    cuerpo = json.dumps(mundo.llm_llamadas[0])
    assert mundo.llm_llamadas[0]["modelo"] == "groq/qwen/qwen3.8-27b" and "hecho por opencode" in cuerpo and "opencode:ind-1:r1" in cuerpo  # responde con el resultado y recibo reales
    e = estado_guardado(mundo, "ind-1")
    assert e["pasos_terminados"][0]["agente_ejecutado"] == "opencode" and e["pasos_terminados"][0]["modelo_usado"] == "hf/qwen3-0.6b"


def test_uso_del_contrato_es_honesto_por_workflow(mundo):
    c = mundo.ctx()
    r = wf.swe_iniciar(ind(modo_agentico=False), c)
    u = r["uso_contrato"]
    assert u["modelo_responde"]["usado"] is True and u["agente_responde"]["usado"] is False and "no ejecuta" in u["agente_responde"]["nota"]
    assert u["agente_tool"]["usado"] is False and u["modelo_tool"]["usado"] is False
    r = wf.swe_iniciar(contrato(task_id="sc-1"), c)
    u = r["uso_contrato"]
    assert u["agente_tool"]["usado"] and u["modelo_tool"]["usado"] and u["agente_verificador"]["usado"] and u["modelo_revisor"]["usado"]
    assert u["modelo_responde"]["usado"] is False and u["agente_responde"]["usado"] is False and u["modelo_lector"]["usado"] is False
    r = wf.swe_iniciar(lm(), c)
    assert r["uso_contrato"]["modelo_lector"]["usado"] is False and "hf/lfm2.5-350m" in r["uso_contrato"]["modelo_lector"]["nota"]


def test_swe_code_ejecuta_y_verifica_usan_modelo_tool_y_modelo_revisor_sin_confundir_con_modelo_responde(mundo):
    c = mundo.ctx()
    r = wf.swe_iniciar(contrato(modelo_tool="hf/qwen3-0.6b", modelo_revisor="hf/lfm2.5-350m", modelo_responde="hf/qwen3.5-0.8b"), c)
    assert [(p["paso"], p["agente"], p["modelo"]) for p in r["plan"]] == [("escribe", "codex", "hf/qwen2.5-coder-1.5b"), ("revisa", "opencode", "hf/qwen3.5-0.8b"),
                                                                       ("ejecuta", "swe-agent", "hf/qwen3-0.6b"), ("verifica", "openhands", "hf/lfm2.5-350m")]


# ---------- NO DISPONIBLE ----------
def test_swe_code_con_un_agente_necesario_ausente_es_no_disponible_sin_pedir_aprobacion_ni_ejecutar(mundo):
    mundo.caps = {a: {"disponible": True, "motivo": ""} for a in ("codex", "swe-agent", "openhands")}
    mundo.caps["opencode"] = {"disponible": False, "motivo": "opencode no esta instalado"}
    c = mundo.ctx()
    r = wf.swe_iniciar(contrato(), c)
    assert r["estado"] == "NO_DISPONIBLE" and r["error"]["codigo"] == "WORKFLOW_NO_DISPONIBLE" and "opencode" in r["error"]["mensaje"]
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "NO_DISPONIBLE" and r["pendiente_aprobacion"] is None and mundo.agentes == []
    mundo.caps["opencode"] = {"disponible": True, "motivo": ""}
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)  # ya instalado: la tarea sigue sola
    assert r["estado"] == "REQUIERE_APROBACION"


def test_agente_seleccionado_ausente_no_se_sustituye_por_otro(mundo):
    mundo.caps = {a: {"disponible": a != "swe-agent", "motivo": "swe-agent no esta instalado"} for a in ("codex", "opencode", "swe-agent", "openhands")}
    c = mundo.ctx()
    r = wf.swe_iniciar(contrato(agente_tool="swe-agent"), c)
    assert r["estado"] == "NO_DISPONIBLE" and "swe-agent" in r["error"]["mensaje"] and mundo.agentes == []


def test_comprobacion_de_disponibilidad_rota_no_se_presenta_como_no_instalado(mundo):
    c = mundo.ctx()
    def rota():
        raise OSError("sin red")
    c.disponibilidad = rota
    r = wf.swe_iniciar(contrato(), c)
    assert r["estado"] == "PENDIENTE" and r["error"] is None


def test_liquid_mirror_sin_s2_s3_independientes_es_no_disponible(mundo, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9001/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://localhost:9001/v1")  # mismo host:puerto con otro nombre
    c = mundo.ctx()
    r = wf.swe_iniciar(lm(), c)
    assert r["estado"] == "NO_DISPONIBLE" and "independientes" in r["error"]["mensaje"]
    with pytest.raises(ValueError, match="LIQUID_SERVIDORES_NO_INDEPENDIENTES"):
        wf.llamar_servidor("S2", "lfm2.5-350m", [{"role": "user", "content": "x"}])
    monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9002/v1")
    assert wf.swe_avanzar({"task_id": "openclaw-001"}, c)["estado"] == "CONTINUAR"


def test_liquid_mirror_tiene_exactamente_dos_participantes(mundo, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9001/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9002/v1")
    r = wf.swe_iniciar(lm(), mundo.ctx())
    part = [(p["participante"], p["servidor"]) for p in r["plan"] if p.get("participante")]
    assert part == [("LIQUID 1 - LECTOR", "S2"), ("LIQUID 2 - EJECUTOR", "S3")]


# ---------- DONE solo con operaciones verificadas ----------
def test_done_exige_todas_las_etapas_con_recibo_y_operaciones_confirmadas(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    for _ in range(4):
        aprobar_y_avanzar(mundo, c)
    e = estado_guardado(mundo)
    assert e["estado"] == "DONE" and all(p["recibo"] for p in e["pasos_terminados"])
    # un DONE manipulado/incompleto no se acepta: falta una operacion confirmada
    ruta = json.loads(mundo.almacen["swe/indice/yaiwes-001.json"])["ruta"]
    wf.swe_iniciar(contrato(task_id="yaiwes-002"), c)
    assert wf.verificado(estado_guardado(mundo, "yaiwes-002")) is False
    assert wf.verificado(e) is True
    e["operaciones"][next(iter(e["operaciones"]))]["estado"] = "INICIADA"
    assert wf.verificado(e) is False


def test_cursor_al_final_no_fabrica_done(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    reg = estado_guardado(mundo)
    reg["paso_actual"] = len(reg["plan"])
    reg["estado"] = "CONTINUAR"
    mundo.almacen[reg["ruta"]] = json.dumps(reg)
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "DONE_NO_VERIFICADO"
    assert mundo.agentes == []


def test_ultimo_paso_sin_recibo_no_marca_done(mundo):
    mundo.respuesta_agente = lambda a, n: {"ok": True, "agente": a, "task_id": "yaiwes-001", "resultado": "x", "recibo": "", "exit_code": 0} if n == 4 else None
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    for _ in range(3):
        aprobar_y_avanzar(mundo, c)
    r = aprobar_y_avanzar(mundo, c)
    assert r["estado"] != "DONE"  # el dispatcher real tambien rechaza AGENTE_SIN_RECIBO; aqui el doble lo deja pasar y el workflow lo detecta


# ---------- agente y modelo realmente usados, errores verificables ----------
def test_se_registra_agente_y_modelo_realmente_usados_y_el_error_con_su_contexto(mundo):
    mundo.respuesta_agente = lambda a, n: {"ok": True, "agente": a, "task_id": "yaiwes-001", "resultado": "ok", "recibo": "r1", "exit_code": 0, "modelo_usado": "qwen2.5-coder-1.5b"} if n == 1 else None
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    r = aprobar_y_avanzar(mundo, c)
    p = r["pasos_terminados"][0]
    assert p["agente_ejecutado"] == "codex" and p["modelo_usado"] == "qwen2.5-coder-1.5b" and p["modelo"] == "hf/qwen2.5-coder-1.5b"
    mal = {"ok": False, "agente": "opencode", "codigo": "AGENTE_SALIO_CON_ERROR", "error": "codigo de salida 2", "efectos_posibles": True, "exit_code": 2}
    mundo.respuesta_agente = lambda a, n: AgenteError("EJECUCION_AGENTE_FALLIDA", mal)
    r = aprobar_y_avanzar(mundo, c)
    er = r["error"]
    assert er["agente"] == "opencode" and er["modelo"] == "hf/qwen3.5-0.8b" and er["exit_code"] == 2 and er["efectos_posibles"] is True and er["codigo"] == "AGENTE_SALIO_CON_ERROR"


def test_agente_distinto_del_planeado_no_se_acepta(mundo):
    mundo.respuesta_agente = lambda a, n: {"ok": True, "agente": "claude-code", "task_id": "yaiwes-001", "resultado": "x", "recibo": "r", "exit_code": 0}
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    r = aprobar_y_avanzar(mundo, c)
    assert r["estado"] == "RECONCILIAR" and r["error"]["codigo"] == "AGENTE_DISTINTO"


def test_el_agente_recibe_el_op_id_como_clave_de_idempotencia(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    r = aprobar_y_avanzar(mundo, c)
    assert mundo.agentes[0]["checkpoint"]["op_id"] in estado_guardado(mundo)["operaciones"]


# ---------- estados finos ----------
def test_estado_detallado_distingue_los_seis_estados(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    ruta = json.loads(mundo.almacen["swe/indice/yaiwes-001.json"])["ruta"]
    base = estado_guardado(mundo)
    assert wf.estado_detallado(base) is None
    e = json.loads(json.dumps(base)); e["estado"] = "EJECUTANDO"; e["operaciones"] = {"x": {"estado": "INICIADA"}}
    assert wf.estado_detallado(e) == "OPERACION_INICIADA"
    e = json.loads(json.dumps(base)); e["pasos_terminados"] = [{"paso": "escribe", "recibo": "r", "agente": "codex"}]; e["operaciones"] = {"x": {"estado": "CONFIRMADA"}}
    assert wf.estado_detallado(e) == "OPERACION_CONFIRMADA"
    e = json.loads(json.dumps(base)); e["parcial"] = {"paso": "responde", "texto": "a medias"}
    assert wf.estado_detallado(e) == "RESPUESTA_PARCIAL"
    e = json.loads(json.dumps(base)); e["llm_pendiente"] = {"tool_calls": ["a"]}
    assert wf.estado_detallado(e) == "ESPERANDO_TOOLS"
    e = json.loads(json.dumps(base)); e["estado"] = "RECONCILIAR"
    assert wf.estado_detallado(e) == "RECONCILIAR"
    e = json.loads(json.dumps(base)); e["estado"] = "DONE"
    assert wf.estado_detallado(e) == "DONE"


def test_individual_respuesta_cortada_se_guarda_parcial_no_done_y_se_completa_al_reanudar(mundo):
    c = mundo.ctx()
    secuencia = [{"texto": "primera mitad ", "tool_calls": [], "finish_reason": "length", "herramientas_usadas": [], "modelo_respuesta": "lfm2.5-350m"},
                 {"texto": "primera mitad segunda mitad", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": [], "modelo_respuesta": "lfm2.5-350m"}]
    mundo.respuesta_llm = lambda n, cuerpo: secuencia[n - 1]
    wf.swe_iniciar(ind(modo_agentico=False), c)
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert r["estado"] == "GAP" and r["estado_detallado"] == "RESPUESTA_PARCIAL" and r["error"]["codigo"] == "LLM_RESPUESTA_PARCIAL" and r["pasos_terminados"] == []
    assert estado_guardado(mundo, "ind-1")["parcial"]["texto"] == "primera mitad "  # el parcial queda guardado, no se pierde
    r = wf.swe_reanudar({"task_id": "ind-1"}, c)
    cuerpo = mundo.llm_llamadas[1]
    assert cuerpo["acumulado"] == "primera mitad " and cuerpo["messages"][-2] == {"role": "assistant", "content": "primera mitad "}
    assert r["estado"] == "DONE" and r["pasos_terminados"][0]["resultado"] == "primera mitad segunda mitad" and r["parcial"] is None


def test_individual_sin_finish_reason_no_se_asume_terminado(mundo):
    c = mundo.ctx()
    mundo.respuesta_llm = lambda n, cuerpo: {"texto": "algo", "tool_calls": [], "herramientas_usadas": [], "modelo_respuesta": "lfm2.5-350m"}
    wf.swe_iniciar(ind(modo_agentico=False), c)
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert r["estado"] == "GAP" and r["estado_detallado"] == "RESPUESTA_PARCIAL" and r["error"]["codigo"] == "LLM_RESPUESTA_PARCIAL"


def test_individual_pausa_de_herramientas_es_esperando_tools_y_se_reanuda_sin_repetir(mundo):
    c = mundo.ctx()
    pausa = {"texto": "", "tool_calls": [], "finish_reason": "pausa_herramientas", "continuar": True, "mensajes": [{"role": "user", "content": "Revisar proyecto"}, {"role": "tool", "content": "ya leido"}],
             "acumulado": "", "herramientas_usadas": ["github_leer"], "modelo_solicitado": "x"}
    fin = {"texto": "listo", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": [], "modelo_respuesta": "lfm2.5-350m"}
    mundo.respuesta_llm = lambda n, cuerpo: pausa if n == 1 else fin
    wf.swe_iniciar(ind(modo_agentico=False), c)
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert r["estado"] == "CONTINUAR" and r["estado_detallado"] == "ESPERANDO_TOOLS" and r["pasos_terminados"] == []
    r = wf.swe_avanzar({"task_id": "ind-1"}, c)
    assert mundo.llm_llamadas[1]["messages"][-1]["content"] == "ya leido"  # retoma la conversacion guardada, no empieza de cero
    assert r["estado"] == "DONE" and r["estado_detallado"] == "DONE" and "github_leer" in r["pasos_terminados"][0]["herramientas"]


def test_individual_cambio_de_modelo_no_se_oculta(mundo):
    c = mundo.ctx()
    mundo.respuesta_llm = lambda n, cuerpo: {"texto": "hola", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": [], "modelo_respuesta": "lfm2.5-350m", "aviso_modelo": "Se pidio otro"}
    wf.swe_iniciar(ind(modo_agentico=False, modelo_responde="groq/qwen/qwen3.8-27b"), c)
    p = wf.swe_avanzar({"task_id": "ind-1"}, c)["pasos_terminados"][0]
    assert p["cambio_modelo"] is True and p["modelo_usado"] == "lfm2.5-350m" and p["modelo"] == "groq/qwen/qwen3.8-27b"


# ---------- persistencia confirmada, checkpoints por etapa, reconciliar ----------
def test_checkpoint_por_etapa_y_participante_se_guarda_antes_de_avanzar(mundo, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9001/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9002/v1")
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    n1 = "swe/openclaw/yaiwes/openclaw-001/openclaw-001.etapa-liquid1.json"
    d = json.loads(mundo.almacen[n1])
    assert d["participante"] == "LIQUID 1 - LECTOR" and d["servidor"] == "S2" and d["recibo"].startswith("liquid:S2:") and len(d["sha256"]) == 64
    assert mundo.guardados.index(n1) < len(mundo.guardados) - 1 and mundo.guardados[-1].endswith("openclaw-001.json")  # etapa antes del estado que avanza
    wf.swe_avanzar({"task_id": "openclaw-001"}, c); wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    d2 = json.loads(mundo.almacen["swe/openclaw/yaiwes/openclaw-001/openclaw-001.etapa-liquid2.json"])
    assert d2["participante"] == "LIQUID 2 - EJECUTOR" and d2["servidor"] == "S3"
    assert n1 != "swe/openclaw/yaiwes/openclaw-001/openclaw-001.etapa-liquid2.json"


def test_si_falla_el_checkpoint_de_etapa_no_arranca_el_siguiente_paso(mundo, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9001/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9002/v1")
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    mundo.falla_guardar = lambda n: ".etapa-" in n
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert estado_guardado(mundo, "openclaw-001")["paso_actual"] == 0


def test_guardado_no_remoto_o_distinto_no_cuenta_como_confirmado(mundo):
    c = mundo.ctx()
    c.guardar = lambda a: {"nombre": a["nombre"], "destino": "local"}  # solo local: no es persistencia garantizada
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_iniciar(contrato(), c)
    c2 = mundo.ctx()
    orig = mundo.guardar
    c2.guardar = lambda a: (orig(a), mundo.almacen.__setitem__(a["nombre"], "otra cosa"))[0]  # el relectura no coincide
    wf.swe_iniciar(contrato(task_id="yaiwes-009"), c2) if False else None
    c3 = mundo.ctx(); c3.guardar = c2.guardar
    c3.guardar({"nombre": "x", "valor": "v"})
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf._guardar_confirmado(c3, "y", "contenido")


def test_el_diario_local_no_sustituye_a_la_persistencia_remota(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    mundo.diarios["yaiwes-001"] = json.dumps({"cualquiera": {"estado": "CONFIRMADA", "recibo": "falso"}})  # el respaldo local existe...
    mundo.falla_guardar = lambda n: True  # ...pero el remoto cae
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert mundo.agentes == []


def test_fallo_al_guardar_tras_ejecutar_deja_reconciliar_o_adoptable(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    mundo.diarios.clear()
    c.con_efectos = lambda n, a: False  # sin diario: la confirmacion solo existia en memoria
    cuenta = {"n": 0}
    def f(n):
        if n.endswith("yaiwes-001.json") and "indice" not in n and "locks" not in n:
            cuenta["n"] += 1
            return cuenta["n"] >= 2
        return False
    mundo.falla_guardar = f
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    mundo.falla_guardar = lambda n: False
    r = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert r["estado"] == "RECONCILIAR" and len(mundo.agentes) == 1 and r["estado_detallado"] == "RECONCILIAR"


# ---------- candado entre procesos / servidores (en el almacen, con TTL y propietario) ----------
@pytest.mark.parametrize("valor", ["{invalido", "null", "[]", '""'])
def test_candado_corrupto_falla_cerrado_sin_ejecutar_agentes(mundo, valor):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    mundo.almacen["swe/locks/yaiwes-001.json"] = valor
    with pytest.raises(ValueError, match="CANDADO_CORRUPTO"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert mundo.agentes == []
    assert mundo.almacen["swe/locks/yaiwes-001.json"] == valor


def test_candado_en_el_almacen_bloquea_a_otro_propietario_vigente(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    mundo.almacen["swe/locks/yaiwes-001.json"] = json.dumps({"propietario": "otro-servidor:123:abc", "token": "t", "expira": time.time() + 60})  # otro servidor lo tiene
    with pytest.raises(ValueError, match="TAREA_BLOQUEADA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    with pytest.raises(ValueError, match="TAREA_BLOQUEADA"):
        wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": "x", "operador": "ana"}, c)
    assert mundo.agentes == []


def test_candado_vencido_se_toma_y_se_libera_al_terminar(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    mundo.almacen["swe/locks/yaiwes-001.json"] = json.dumps({"propietario": "muerto:1:z", "token": "t", "expira": time.time() - 5})  # TTL vencido: el dueno murio
    assert wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["estado"] == "REQUIERE_APROBACION"
    assert json.loads(mundo.almacen["swe/locks/yaiwes-001.json"])["expira"] == 0  # liberado


def test_candado_se_libera_aunque_falle_la_operacion(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    mundo.falla_guardar = lambda n: n.endswith("yaiwes-001.json") and "indice" not in n and "locks" not in n
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert json.loads(mundo.almacen["swe/locks/yaiwes-001.json"])["expira"] == 0


def test_la_operacion_con_efectos_no_arranca_si_se_perdio_el_candado(mundo):
    c = mundo.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    orig = mundo.guardar
    def roba(args):  # otro servidor toma el candado justo mientras guardamos INICIADA
        r = orig(args)
        if args["nombre"].endswith("yaiwes-001.json") and "indice" not in args["nombre"] and "INICIADA" in args["valor"]:
            mundo.almacen["swe/locks/yaiwes-001.json"] = json.dumps({"propietario": "intruso:9:q", "token": "q", "expira": time.time() + 60})
        return r
    c.guardar = roba
    with pytest.raises(ValueError, match="TAREA_BLOQUEADA"):
        wf.swe_avanzar({"task_id": "yaiwes-001"}, c)
    assert mundo.agentes == []


def test_candado_con_task_id_invalido_no_toca_el_almacen(mundo):
    c = mundo.ctx()
    with pytest.raises(ValueError, match="TASK_ID_INVALIDO"):
        wf.swe_avanzar({"task_id": "../x"}, c)
    assert mundo.almacen == {}


# ---------- Liquid: S2/S3 reales, handoff, recuperacion ----------
def test_liquid_mirror_con_dos_servidores_http_reales_independientes(mundo, servidores):
    c = mundo.ctx(); c.servidor_llm = wf.llamar_servidor  # HTTP real contra dos puertos distintos
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c); wf.swe_avanzar({"task_id": "openclaw-001"}, c); r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    puertos = [v[0] for v in Falso.visto]
    assert len(puertos) == 2 and puertos[0] != puertos[1] and puertos == [servidores[0].server_port, servidores[1].server_port]
    assert r["pasos_terminados"][0]["resultado"] == "puerto %d" % servidores[0].server_port and r["pasos_terminados"][2]["resultado"] == "puerto %d" % servidores[1].server_port
    assert "puerto %d" % servidores[0].server_port in json.dumps(Falso.visto[1][2]["messages"])  # S3 solo recibe el handoff de S2
    assert r["pasos_terminados"][0]["finish_reason"] == "stop" and r["pasos_terminados"][2]["finish_reason"] == "stop"


def test_recuperacion_tras_reinicio_desde_el_ultimo_handoff_sin_repetir_liquid1(mundo, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9001/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9002/v1")
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c); wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    llamadas_antes = list(mundo.servidores)
    c2 = mundo.ctx()  # "reinicio": otro Contexto, nada en memoria; solo el almacen
    wf._LOCKS.clear()
    r = wf.swe_reanudar({"task_id": "openclaw-001"}, c2)
    assert [s[0] for s in mundo.servidores] == [s[0] for s in llamadas_antes] + ["S3"] and r["handoff"]["confirmado"] is True and r["paso_actual"] == 3


def test_handoff_ya_guardado_y_valido_se_adopta_tras_caida_entre_guardar_handoff_y_estado(mundo, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9001/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9002/v1")
    c = mundo.ctx()
    wf.swe_iniciar(lm(), c)
    wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    mundo.falla_guardar = lambda n: n.endswith("openclaw-001.json") and "indice" not in n and "locks" not in n and mundo.almacen.get("swe/openclaw/yaiwes/openclaw-001/openclaw-001.handoff.json") is not None and "etapa" not in n
    with pytest.raises(RuntimeError, match="PERSISTENCIA_FALLIDA"):
        wf.swe_avanzar({"task_id": "openclaw-001"}, c)  # handoff escrito, estado no
    assert estado_guardado(mundo, "openclaw-001")["handoff"] is None
    mundo.falla_guardar = lambda n: False
    antes = mundo.guardados.count("swe/openclaw/yaiwes/openclaw-001/openclaw-001.handoff.json")
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["handoff"]["confirmado"] is True and mundo.guardados.count("swe/openclaw/yaiwes/openclaw-001/openclaw-001.handoff.json") == antes  # se adopto, no se reescribio


def test_liquid2_cortado_guarda_el_parcial_y_no_activa_al_agente(mundo):
    c = mundo.ctx(); srv_length(mundo, {"S2": [("analisis", "stop")], "S3": [("plan a medias", "length")]})
    wf.swe_iniciar(lm(), c)
    for _ in range(2): wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    r = wf.swe_avanzar({"task_id": "openclaw-001"}, c)
    assert r["estado"] == "GAP" and r["estado_detallado"] == "RESPUESTA_PARCIAL" and r["parcial"]["texto"].startswith("plan a medias") and r["parcial"]["finish_reason"] == "length" and mundo.agentes == []
    srv_length(mundo, {"S2": [("analisis", "stop")], "S3": [("plan completo", "stop")]})
    r = wf.swe_reanudar({"task_id": "openclaw-001"}, c)  # reintenta SOLO Liquid 2 con el handoff ya guardado
    assert r["paso_actual"] == 3 and r["parcial"] is None and [s[0] for s in mundo.servidores][-1] == "S3"


# ---------- preflight segun `estado` de disponibilidad (A5): bloquea lo que de verdad falta, deja intentar lo SIN VERIFICAR ----------
@pytest.mark.parametrize("estado", ["NO INSTALADO", "NO CONFIGURADO", "NO COMPATIBLE", "NO DISPONIBLE EN PROVEEDOR"])
def test_preflight_bloquea_los_estados_que_de_verdad_faltan(mundo, estado):
    mundo.caps = {a: {"disponible": True, "estado": "DISPONIBLE", "motivo": ""} for a in ("codex", "opencode", "swe-agent", "openhands")}
    mundo.caps["opencode"] = {"disponible": False, "estado": estado, "motivo": "causa concreta"}
    r = wf.swe_iniciar(contrato(), mundo.ctx())
    assert r["estado"] == "NO_DISPONIBLE" and "opencode" in r["error"]["mensaje"] and mundo.agentes == []


def test_preflight_deja_intentar_un_agente_sin_verificar_y_el_resultado_es_el_real(mundo):
    mundo.caps = {a: {"disponible": True, "estado": "DISPONIBLE", "motivo": ""} for a in ("codex", "opencode", "swe-agent", "openhands")}
    mundo.caps["codex"] = {"disponible": False, "estado": "SIN VERIFICAR", "motivo": "no se pudo comprobar", "intentable": False}
    c = mundo.ctx()
    r = wf.swe_iniciar(contrato(), c)
    assert r["estado"] == "PENDIENTE" and r["error"] is None  # no se presenta como NO INSTALADO
    no = {"ok": False, "agente": "codex", "codigo": "AGENTE_NO_INSTALADO", "error": "falta codex", "efectos_posibles": False}
    mundo.respuesta_agente = lambda a, n: AgenteError("EJECUCION_AGENTE_FALLIDA", no)
    r = aprobar_y_avanzar(mundo, c)  # se intento de verdad y el adaptador dijo la verdad
    assert r["estado"] == "GAP" and r["error"]["codigo"] == "AGENTE_NO_INSTALADO" and len(mundo.agentes) == 1


# ---------- candado ENTRE PROCESOS reales (almacen compartido en disco; no solo threads) ----------
_PROCESO = r'''
import json, os, re, sys, time
from agentes.adaptadores import workflows as wf
almacen, rol, task = sys.argv[1], sys.argv[2], sys.argv[3]
def ruta(n): return os.path.join(almacen, n.replace("/", "__"))
def guardar(a):
    open(ruta(a["nombre"]), "w").write(a["valor"]); return {"nombre": a["nombre"], "destino": "hf"}
def leer(a):
    if not os.path.exists(ruta(a["nombre"])): raise RuntimeError("Router HTTP 404: no existe")
    return {"valor": open(ruta(a["nombre"])).read()}
def agente(ag, t, modelo, objetivo, contexto, permisos, cp):
    open(os.path.join(almacen, "EJECUTADO-%s-%d" % (rol, os.getpid())), "w").write(ag)
    time.sleep(float(os.environ.get("DUERME", "0")))
    return {"ok": True, "agente": ag, "task_id": t, "resultado": "hecho", "herramientas": [], "evidencias": [], "recibo": "%s:%s:r-%s" % (ag, t, rol), "exit_code": 0, "modelo_usado": modelo}
c = wf.Contexto(guardar=guardar, leer=leer, llm=None, router=None, con_efectos=lambda *a: False, diario=lambda t: {}, anotar=lambda *a: None, llave=lambda n, a: n,
                secreto=re.compile(r"(?!x)x"), ejecutar_agente=agente, operadores=lambda: {"ana"}, disponibilidad=lambda: {})
try:
    r = wf.swe_avanzar({"task_id": task}, c)
    print(json.dumps({"ok": True, "estado": r["estado"], "paso_actual": r["paso_actual"]}))
except ValueError as e:
    print(json.dumps({"ok": False, "error": str(e)}))
'''


def test_dos_procesos_reales_no_ejecutan_la_misma_tarea_a_la_vez(tmp_path, monkeypatch):
    import subprocess
    import sys
    almacen = tmp_path / "almacen"; almacen.mkdir()
    (tmp_path / "ws" / "yaiwes").mkdir(parents=True)
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", str(tmp_path / "ws"))
    m = Mundo(); c = m.ctx()
    wf.swe_iniciar(contrato(), c)
    op = wf.swe_avanzar({"task_id": "yaiwes-001"}, c)["pendiente_aprobacion"]["op_id"]
    wf.swe_aprobar({"task_id": "yaiwes-001", "op_id": op, "operador": "ana"}, c)
    for nombre, valor in m.almacen.items():  # el mismo estado, ahora en el almacen compartido en disco
        (almacen / nombre.replace("/", "__")).write_text(valor)
    import os
    env = {**os.environ, "RIU_SWE_WORKSPACE_RAIZ": str(tmp_path / "ws"), "PYTHONPATH": os.pathsep.join(sys.path)}
    a = subprocess.Popen([sys.executable, "-c", _PROCESO, str(almacen), "A", "yaiwes-001"], env={**env, "DUERME": "6"}, stdout=subprocess.PIPE, text=True)
    t0 = time.time()
    while not list(almacen.glob("EJECUTADO-A-*")) and time.time() - t0 < 30:
        time.sleep(0.1)
    assert list(almacen.glob("EJECUTADO-A-*")), "el proceso A debia estar ejecutando el agente"
    b = subprocess.run([sys.executable, "-c", _PROCESO, str(almacen), "B", "yaiwes-001"], env=env, capture_output=True, text=True, timeout=60)
    sal_b = json.loads(b.stdout.strip().splitlines()[-1])
    sal_a = json.loads(a.communicate(timeout=60)[0].strip().splitlines()[-1])
    assert sal_b == {"ok": False, "error": "TAREA_BLOQUEADA"} and not list(almacen.glob("EJECUTADO-B-*"))  # B no ejecuto nada
    assert sal_a["ok"] is True and len(list(almacen.glob("EJECUTADO-*"))) == 1
    assert json.loads((almacen / "swe__locks__yaiwes-001.json").read_text())["expira"] == 0  # A libero el candado
