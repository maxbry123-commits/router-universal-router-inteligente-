"""Workflows SWE (individual, swe_code, liquid_mirror) y operaciones del Harness swe_iniciar/avanzar/estado/aprobar/reanudar.

No hay almacenamiento propio: todo pasa por las funciones del Harness (guardar/leer -> Router -> bucket HF) inyectadas en `Contexto`
(guardar, leer, llm, router, con_efectos, diario, anotar). Estados: PENDIENTE, EJECUTANDO, REQUIERE_APROBACION, RECONCILIAR, CONTINUAR,
VERIFICANDO, DONE, GAP.

Reglas: una etapa depende de la anterior y su resultado se guarda ANTES de continuar; si falla el guardado se detiene antes de cualquier
operacion con efectos (RuntimeError PERSISTENCIA_FALLIDA); una operacion con efectos se marca INICIADA y se guarda antes de lanzarla y
CONFIRMADA al terminar: lo que quede INICIADA sin confirmacion pasa a RECONCILIAR y no se reintenta hasta que un operador lo verifique;
la aprobacion solo la da swe_aprobar con operador identificado (nunca el campo `aprobacion` del contrato ni del modelo)."""
import hashlib
import json
import os
import re
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from . import _comun, dispatcher
from .contrato import TareaSWE
from .modelos import validar_modelo

WORKFLOW_SWE_CODE = [
    {"paso": "escribe", "agente": "codex", "modelo": "hf/qwen2.5-coder-1.5b"},
    {"paso": "revisa", "agente": "opencode", "modelo": "hf/qwen3.5-0.8b"},
    {"paso": "ejecuta", "agente": "seleccionado", "modelo": "hf/lfm2.5-350m"},
    {"paso": "verifica", "agente": "openhands", "modelo": "hf/lfm2.5-350m"},
]
WORKFLOW_LIQUID_MIRROR = [
    {"paso": "liquid1", "modelo": "hf/lfm2.5-350m", "servidor": "S2", "funcion": "lee_analiza"},
    {"paso": "handoff", "funcion": "transferir_contexto"},
    {"paso": "liquid2", "modelo": "hf/lfm2.5-350m", "servidor": "S3", "funcion": "ejecutar"},
    {"paso": "verifica", "funcion": "verificar"},
]
ESTADOS = ("PENDIENTE", "EJECUTANDO", "REQUIERE_APROBACION", "RECONCILIAR", "CONTINUAR", "VERIFICANDO", "DONE", "GAP")
# Pasos que cambian el repositorio/entorno: siempre exigen aprobacion de un operador. verifica tambien la exige si el agente no puede
# garantizar solo-lectura (el SDK de OpenHands y el Gateway OpenClaw no lo ofrecen; Codex/OpenCode/Claude Code/SWE-agent si).
PASOS_CON_EFECTOS = ("escribe", "revisa", "ejecuta")
SOLO_LECTURA_GARANTIZADA = {"codex": True, "opencode": True, "claude-code": True, "swe-agent": True, "openhands": False, "openclaw": False}
_TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
_OPERADOR = re.compile(r"[A-Za-z0-9_.@-]{2,64}")
MAX_TEXTO = 8000
MAX_CONTINUACIONES = 2  # Liquid cortado por finish_reason=length: cuantas veces se le pide seguir antes de marcar el resultado como parcial
_LOCKS, _LOCKS_G = {}, threading.Lock()


class _Persistencia(RuntimeError):
    pass


@dataclass
class Contexto:
    guardar: Callable
    leer: Callable
    llm: Callable
    router: Callable
    con_efectos: Callable
    diario: Callable
    anotar: Callable
    llave: Callable
    secreto: Any
    ejecutar_agente: Optional[Callable] = None
    servidor_llm: Optional[Callable] = None
    operadores: Optional[Callable] = None

    def __post_init__(self):
        self.ejecutar_agente = self.ejecutar_agente or dispatcher.ejecutar_agente
        self.servidor_llm = self.servidor_llm or llamar_servidor
        self.operadores = self.operadores or _operadores_env


def _operadores_env():
    return {o.strip() for o in os.environ.get("RIU_SWE_OPERADORES", "").split(",") if _OPERADOR.fullmatch(o.strip())}


def _ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(*partes):
    return hashlib.sha256("\x1f".join(str(p) for p in partes).encode("utf-8", "replace")).hexdigest()


def _limpio(ctx, texto, tope=MAX_TEXTO):
    return _comun.redactar(ctx.secreto.sub("[REDACTADO]", texto if isinstance(texto, str) else str(texto)))[:tope]


def _seg(s):
    s = re.sub(r"[^A-Za-z0-9_-]", "_", str(s or "")) or "general"
    return s if len(s) <= 16 else s[:9] + "-" + _sha(s)[:6]


def _ruta(origen, proyecto, sesion, task_id):
    return "swe/%s/%s/%s/%s.json" % (origen, _seg(proyecto), _seg(sesion), task_id)


def _ruta_handoff(ruta):
    return ruta[:-len(".json")] + ".handoff.json"


def _indice(task_id):
    return "swe/indice/%s.json" % task_id


def _lock(task_id):
    with _LOCKS_G:
        return _LOCKS.setdefault(task_id, threading.Lock())


# ---------------- persistencia (siempre por las funciones del Harness) ----------------
def _guardar(ctx, nombre, texto):
    try:
        ctx.guardar({"nombre": nombre, "valor": _comun.redactar(ctx.secreto.sub("[REDACTADO]", texto))})
    except Exception as exc:  # noqa: BLE001 - cualquier fallo significa "no quedo guardado"
        raise _Persistencia("PERSISTENCIA_FALLIDA: no se guardo %s (%s)" % (nombre, type(exc).__name__)) from None


def _leer(ctx, nombre, opcional=False):
    try:
        return ctx.leer({"nombre": nombre})["valor"]
    except Exception as exc:  # noqa: BLE001
        m = str(exc)
        if opcional and ("HTTP 404" in m or "no existe" in m):
            return None
        raise _Persistencia("PERSISTENCIA_FALLIDA: no se pudo leer %s (%s)" % (nombre, type(exc).__name__)) from None


def _guardar_estado(ctx, reg):
    reg["fecha"] = _ahora()
    _guardar(ctx, reg["ruta"], json.dumps(reg, ensure_ascii=False, default=str))


def _cargar(ctx, args):
    task_id = args.get("task_id")
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        raise ValueError("TASK_ID_INVALIDO")
    ind = _leer(ctx, _indice(task_id), opcional=True)
    if ind is None:
        raise ValueError("TAREA_NO_ENCONTRADA")
    ruta = json.loads(ind)["ruta"]
    crudo = _leer(ctx, ruta, opcional=True)
    if crudo is None:
        raise ValueError("TAREA_NO_ENCONTRADA")
    reg = json.loads(crudo)
    for campo in ("origen", "proyecto", "sesion"):
        if args.get(campo) not in (None, "") and args[campo] != reg.get(campo):
            raise ValueError("TAREA_NO_COINCIDE")
    return reg


# ---------------- plan ----------------
def plan_de(c):
    """Pasos del workflow para un contrato validado. Cada paso: paso, tipo (llm|liquid|handoff|agente), agente, modelo, servidor, efectos."""
    w = c["workflow"]
    if w == "individual":
        return [{"paso": "responde", "tipo": "llm", "agente": None, "modelo": c["modelo_responde"], "servidor": None, "efectos": False}]
    if w == "swe_code":
        out = []
        for s in WORKFLOW_SWE_CODE:
            agente = c["agente_tool"] if s["agente"] == "seleccionado" else (c["agente_verificador"] if s["paso"] == "verifica" else s["agente"])
            out.append({"paso": s["paso"], "tipo": "agente", "agente": agente, "modelo": s["modelo"], "servidor": None,
                        "efectos": s["paso"] in PASOS_CON_EFECTOS or not SOLO_LECTURA_GARANTIZADA.get(agente, False)})
        return out
    l1, ho, l2 = WORKFLOW_LIQUID_MIRROR[0], WORKFLOW_LIQUID_MIRROR[1], WORKFLOW_LIQUID_MIRROR[2]
    return [{"paso": "liquid1", "tipo": "liquid", "agente": None, "modelo": l1["modelo"], "servidor": l1["servidor"], "efectos": False},
            {"paso": "handoff", "tipo": "handoff", "agente": None, "modelo": None, "servidor": None, "efectos": False},
            {"paso": "liquid2", "tipo": "liquid", "agente": None, "modelo": l2["modelo"], "servidor": l2["servidor"], "efectos": False},
            {"paso": "ejecuta", "tipo": "agente", "agente": c["agente_tool"], "modelo": c["modelo_tool"], "servidor": None, "efectos": True},
            {"paso": "verifica", "tipo": "agente", "agente": c["agente_verificador"], "modelo": c["modelo_revisor"], "servidor": None,
             "efectos": not SOLO_LECTURA_GARANTIZADA.get(c["agente_verificador"], False)}]


def _id_bridge(modelo_id):
    cfg = validar_modelo(modelo_id)
    return cfg["model"] if cfg["provider"] == "hf" else modelo_id


def _entrada_agente(reg, paso):
    """(objetivo, contexto) del paso: el contexto es el resultado CONFIRMADO de la etapa anterior (y el handoff en Liquid Mirror)."""
    m = reg["mensaje"]
    objetivo = {"escribe": m, "revisa": "Revisa y refactoriza el trabajo del paso anterior. Solicitud original: " + m,
                "ejecuta": ("Ejecuta el plan de Liquid 2. Solicitud original: " if reg["workflow"] == "liquid_mirror" else "Ejecuta lo pendiente usando el trabajo confirmado en los pasos anteriores. Solicitud original: ") + m,
                "verifica": "Verifica con evidencia real (pruebas, estado del repositorio) que se cumplio la solicitud. Solicitud original: " + m}[paso]
    previos = [p for p in reg["pasos_terminados"] if p.get("resultado")]
    partes = []
    if reg.get("handoff") and reg["handoff"].get("confirmado") is True:  # un handoff parcial/no confirmado nunca llega a un agente
        partes.append("Handoff de Liquid 1 (%s): %s" % (reg["handoff"]["servidor_origen"], reg["handoff"].get("resumen", "")))
    if previos:
        partes.append("Resultado confirmado de '%s': %s" % (previos[-1]["paso"], previos[-1]["resultado"]))
    return objetivo, "\n\n".join(partes)[:20000]


def _op_id(reg, idx, p, objetivo, contexto):
    return _sha(reg["task_id"], idx, p["paso"], p["agente"], p["modelo"], objetivo, contexto)[:16]


def _directorio(reg):
    raiz = os.environ.get("RIU_SWE_WORKSPACE_RAIZ", "").strip()
    if not raiz or not os.path.isdir(raiz):
        return None, ("WORKSPACE_NO_CONFIGURADO", "RIU_SWE_WORKSPACE_RAIZ no apunta a un directorio existente")
    proyecto = reg.get("proyecto") or ""
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,63}", proyecto) or ".." in proyecto:
        return None, ("PROYECTO_INVALIDO", "el proyecto no es un nombre simple de carpeta")
    base, ruta = os.path.realpath(raiz), os.path.realpath(os.path.join(raiz, proyecto))
    if not ruta.startswith(base + os.sep) or not os.path.isdir(ruta):
        return None, ("WORKSPACE_NO_CONFIGURADO", "no existe la carpeta del proyecto bajo la raiz")
    return ruta, None


# ---------------- vistas ----------------
def _vista(reg, extra=None):
    v = {"ok": True, "task_id": reg["task_id"], "origen": reg["origen"], "proyecto": reg["proyecto"], "sesion": reg["sesion"], "workflow": reg["workflow"],
         "estado": reg["estado"], "paso_actual": reg["paso_actual"], "plan": [{k: p[k] for k in ("paso", "agente", "modelo", "servidor", "efectos")} for p in reg["plan"]],
         "pasos_terminados": reg["pasos_terminados"], "handoff": reg["handoff"], "resultado_tool": reg["resultado_tool"], "evidencia": reg["evidencia"],
         "aprobacion": reg["aprobacion"], "pendiente_aprobacion": reg.get("pendiente_aprobacion"), "pendiente_reconciliacion": reg.get("pendiente_reconciliacion"),
         "error": reg.get("error"), "fecha": reg["fecha"]}
    if reg["workflow"] == "liquid_mirror":
        v["ejecucion_s2_s3"] = "secuencial"  # las llamadas a S2 y S3 se hacen una tras otra: no se afirma paralelismo
    v.update(extra or {})
    return v


def _tarea_de(reg):
    return TareaSWE.desde_dict(reg["contrato"]).validar()


# ---------------- iniciar ----------------
def swe_iniciar(args, ctx):
    contrato = args.get("tarea") if isinstance(args.get("tarea"), dict) else args
    c = TareaSWE.desde_dict(contrato).validar()
    solicitada = c["aprobacion"]
    c["aprobacion"] = False  # la aprobacion solo la da swe_aprobar
    ruta = _ruta(c["origen"], c["proyecto"], c["sesion"], c["task_id"])
    with _lock(c["task_id"]):
        ind = _leer(ctx, _indice(c["task_id"]), opcional=True)
        if ind is not None:
            if json.loads(ind).get("ruta") != ruta:
                raise ValueError("TASK_ID_EN_USO")
            existente = _leer(ctx, ruta, opcional=True)
            if existente is not None:
                return _vista(json.loads(existente), {"ya_existia": True})
        reg = {"version": 1, "task_id": c["task_id"], "origen": c["origen"], "proyecto": c["proyecto"], "sesion": c["sesion"], "ruta": ruta,
               "workflow": c["workflow"], "mensaje": _limpio(ctx, c["mensaje"], 20000), "contrato": c, "modo_agentico": c["modo_agentico"],
               "modelo_responde": c["modelo_responde"], "modelo_lector": c["modelo_lector"], "modelo_tool": c["modelo_tool"],
               "agente_responde": c["agente_responde"], "agente_tool": c["agente_tool"], "agente_verificador": c["agente_verificador"],
               "plan": plan_de(c), "paso_actual": 0, "pasos_terminados": [], "handoff": None, "resultado_tool": "", "evidencia": [],
               "estado": "PENDIENTE", "aprobacion": False, "aprobacion_solicitada_ignorada": bool(solicitada), "aprobaciones": {}, "operaciones": {},
               "pendiente_aprobacion": None, "pendiente_reconciliacion": None, "error": None, "creada": _ahora(), "fecha": _ahora()}
        _guardar_estado(ctx, reg)
        _guardar(ctx, _indice(c["task_id"]), json.dumps({"ruta": ruta, "origen": c["origen"], "proyecto": c["proyecto"], "sesion": c["sesion"]}))
        return _vista(reg)


def swe_estado(args, ctx):
    return _vista(_cargar(ctx, args))


# ---------------- aprobar / reconciliar (operador identificado) ----------------
def _operador(args, ctx):
    op = args.get("operador")
    if not isinstance(op, str) or not _OPERADOR.fullmatch(op):
        raise ValueError("OPERADOR_REQUERIDO")
    permitidos = ctx.operadores()
    if not permitidos:
        raise ValueError("APROBADORES_NO_CONFIGURADOS")
    if op not in permitidos:
        raise ValueError("OPERADOR_NO_AUTORIZADO")
    return op


def swe_aprobar(args, ctx):
    with _lock(str(args.get("task_id"))):
        reg = _cargar(ctx, args)
        if reg["estado"] != "REQUIERE_APROBACION" or not reg.get("pendiente_aprobacion"):
            raise ValueError("ESTADO_NO_APROBABLE")
        operador = _operador(args, ctx)  # el campo `aprobacion` de cualquier mensaje o modelo no cuenta: solo operador + op_id
        pend = reg["pendiente_aprobacion"]
        if args.get("op_id") != pend["op_id"]:
            raise ValueError("OP_NO_PENDIENTE")
        reg["aprobaciones"][pend["op_id"]] = {"por": operador, "fecha": _ahora(), "paso": pend["paso"], "agente": pend["agente"], "modelo": pend["modelo"]}
        reg["aprobacion"], reg["pendiente_aprobacion"], reg["error"] = True, None, None
        reg["estado"] = "VERIFICANDO" if pend["paso"] == "verifica" else "CONTINUAR"
        _guardar_estado(ctx, reg)
        return _vista(reg)


def _reconciliar(reg, args, ctx):
    r = args.get("reconciliacion")
    operador = _operador(args, ctx)
    pend = reg.get("pendiente_reconciliacion") or {}
    if (not isinstance(r, dict) or r.get("op_id") != pend.get("op_id") or r.get("resultado") not in ("confirmada", "no_ejecutada")
            or not isinstance(r.get("evidencia"), str) or not r["evidencia"].strip()):
        raise ValueError("RECONCILIACION_INVALIDA")
    op_id, evid = pend["op_id"], _limpio(ctx, r["evidencia"], 2000)
    op = reg["operaciones"][op_id]
    if r["resultado"] == "confirmada":
        op.update({"estado": "CONFIRMADA", "reconciliada_por": operador, "evidencia": evid})
        _cerrar_paso(ctx, reg, op["idx"], evid, None, [], ["reconciliacion:" + operador], reconciliado_por=operador)
    else:
        reg["operaciones"].pop(op_id, None)
        reg["aprobaciones"].pop(op_id, None)  # lo aprobado pudo ejecutarse: hay que volver a aprobar antes de repetir
        reg["estado"], reg["aprobacion"] = "CONTINUAR", False
    reg["pendiente_reconciliacion"], reg["error"] = None, None
    _guardar_estado(ctx, reg)


def swe_reanudar(args, ctx):
    """Retoma desde el ultimo checkpoint guardado (nunca desde memoria del proceso)."""
    with _lock(str(args.get("task_id"))):
        reg = _cargar(ctx, args)
        if reg["estado"] == "RECONCILIAR":
            if args.get("reconciliacion") is None:
                return _vista(reg)  # nada se reintenta hasta que un operador verifique el estado real
            _reconciliar(reg, args, ctx)
        elif reg["estado"] == "GAP":
            if reg.get("error"):
                for k, o in list(reg["operaciones"].items()):
                    if o["estado"] == "FALLIDA":
                        reg["operaciones"].pop(k)  # fallo sin efectos: se puede reintentar (la aprobacion sigue valida)
            reg["estado"], reg["error"] = "CONTINUAR", None
            _guardar_estado(ctx, reg)
        return _avanzar(reg, args, ctx)


# ---------------- avanzar ----------------
def swe_avanzar(args, ctx):
    with _lock(str(args.get("task_id"))):
        return _avanzar(_cargar(ctx, args), args, ctx)


def _avanzar(reg, args, ctx):
    try:
        n = max(1, min(int(args.get("max_pasos") or 1), 8))
    except (TypeError, ValueError):
        n = 1
    for _ in range(n):
        if not _una(reg, ctx):
            break
    return _vista(reg)


def _fallar(ctx, reg, idx, codigo, mensaje, seguro, op_id=None):
    reg["error"] = {"codigo": codigo, "mensaje": _limpio(ctx, mensaje, 500), "paso": reg["plan"][idx]["paso"] if idx < len(reg["plan"]) else None, "fecha": _ahora()}
    if seguro:  # certeza de que no hubo efectos: GAP, se puede reintentar tras corregir
        if op_id and op_id in reg["operaciones"]:
            reg["operaciones"][op_id]["estado"] = "FALLIDA"
        reg["estado"] = "GAP"
    else:
        reg["estado"] = "RECONCILIAR"
        reg["pendiente_reconciliacion"] = {"op_id": op_id, "paso": reg["plan"][idx]["paso"], "motivo": codigo}
    _guardar_estado(ctx, reg)
    return False


def _cerrar_paso(ctx, reg, idx, texto, recibo, herramientas, evidencias, **extra):
    p = reg["plan"][idx]
    reg["pasos_terminados"].append({"paso": p["paso"], "agente": p["agente"], "modelo": p["modelo"], "servidor": p["servidor"], "recibo": recibo,
                                    "resultado": _limpio(ctx, texto), "herramientas": herramientas, "evidencias": evidencias, "fecha": _ahora(), **extra})
    reg["evidencia"] = (reg["evidencia"] + [_limpio(ctx, e, 300) for e in evidencias])[-50:]
    if p["tipo"] == "agente" and p["paso"] != "verifica":  # resultado_tool = lo que produjo la herramienta, no la verificacion
        reg["resultado_tool"] = _limpio(ctx, texto)
    reg["paso_actual"] = idx + 1
    reg["aprobacion"], reg["pendiente_aprobacion"] = False, None
    if reg["paso_actual"] >= len(reg["plan"]):
        reg["estado"] = "DONE"  # solo cuando se completo la ultima etapa (verifica) con recibo; finish_reason=stop no cuenta
    else:
        reg["estado"] = "VERIFICANDO" if reg["plan"][reg["paso_actual"]]["paso"] == "verifica" else "CONTINUAR"


def _una(reg, ctx):
    """Ejecuta como mucho UN paso. Devuelve True si se puede seguir con el siguiente en la misma llamada."""
    est = reg["estado"]
    if est in ("DONE", "RECONCILIAR", "GAP"):
        return False
    idx = reg["paso_actual"]
    if idx >= len(reg["plan"]):
        reg["estado"] = "DONE"
        _guardar_estado(ctx, reg)
        return False
    p = reg["plan"][idx]
    if est == "EJECUTANDO":  # quedo a medias en un proceso que ya no corre (aqui tenemos el candado de la tarea)
        pend = next((k for k, o in reg["operaciones"].items() if o["estado"] == "INICIADA"), None)
        if pend:
            return _revisar_iniciada(reg, ctx, idx, pend)
    if p["tipo"] == "agente":
        return _paso_agente(reg, ctx, idx, p)
    if p["tipo"] == "llm":
        return _paso_llm(reg, ctx, idx, p)
    if p["tipo"] == "liquid":
        return _paso_liquid(reg, ctx, idx, p)
    return _paso_handoff(reg, ctx, idx, p)


def _revisar_iniciada(reg, ctx, idx, op_id):
    """INICIADA sin CONFIRMADA: si el diario del Harness conserva la confirmacion real se adopta; si no, hay que reconciliar (no se reejecuta)."""
    op = reg["operaciones"][op_id]
    entrada = ctx.diario(reg["task_id"]).get(op["llave"])
    if isinstance(entrada, dict) and entrada.get("estado") == "CONFIRMADA" and entrada.get("recibo"):
        op["estado"] = "CONFIRMADA"
        _cerrar_paso(ctx, reg, op["idx"], entrada.get("resultado", ""), entrada["recibo"], entrada.get("herramientas", []), entrada.get("evidencias", []), adoptado_del_diario=True)
        _guardar_estado(ctx, reg)
        return True
    return _fallar(ctx, reg, idx, "OPERACION_SIN_CONFIRMAR", "la operacion %s quedo iniciada sin confirmacion: verificar su estado real antes de reintentar" % op_id, False, op_id)


def _paso_agente(reg, ctx, idx, p):
    objetivo, contexto = _entrada_agente(reg, p["paso"])
    op_id = _op_id(reg, idx, p, objetivo, contexto)
    op = reg["operaciones"].get(op_id)
    if op and op["estado"] == "CONFIRMADA":
        return True  # ya hecho: no se repite (el paso se cerro junto con la confirmacion)
    if op and op["estado"] == "INICIADA":
        return _revisar_iniciada(reg, ctx, idx, op_id)
    if not reg["modo_agentico"]:
        return _fallar(ctx, reg, idx, "MODO_AGENTICO_APAGADO", "el modo agentico esta apagado: no se activan agentes externos para ejecutar operaciones", True)
    directorio, falta = _directorio(reg)
    if falta:
        return _fallar(ctx, reg, idx, falta[0], falta[1], True)
    if p["efectos"] and op_id not in reg["aprobaciones"]:
        reg["estado"], reg["aprobacion"] = "REQUIERE_APROBACION", False
        reg["pendiente_aprobacion"] = {"op_id": op_id, "paso": p["paso"], "agente": p["agente"], "modelo": p["modelo"],
                                       "permisos": {"escritura": p["paso"] in PASOS_CON_EFECTOS, "ejecucion": p["paso"] in ("ejecuta", "verifica")},
                                       "objetivo": _limpio(ctx, objetivo, 500)}
        _guardar_estado(ctx, reg)
        return False
    aprobada = reg["aprobaciones"].get(op_id) or {}
    permisos = {"directorio": directorio, "escritura": p["paso"] in PASOS_CON_EFECTOS, "ejecucion": p["paso"] in ("ejecuta", "verifica") and p["efectos"],
                "aprobado_por": aprobada.get("por")}
    llave = ctx.llave("swe_agente", {"task_id": reg["task_id"], "op_id": op_id})
    # 1) INICIADA se guarda ANTES de lanzar nada con efectos: si no queda guardada, no se ejecuta
    reg["operaciones"][op_id] = {"estado": "INICIADA", "idx": idx, "paso": p["paso"], "agente": p["agente"], "modelo": p["modelo"], "llave": llave,
                                 "intentos": (op or {}).get("intentos", 0) + 1, "inicio": _ahora()}
    reg["estado"], reg["error"], reg["pendiente_aprobacion"] = ("VERIFICANDO" if p["paso"] == "verifica" else "EJECUTANDO"), None, None
    _guardar_estado(ctx, reg)
    diario = None
    if ctx.con_efectos("swe_agente", {"task_id": reg["task_id"], "op_id": op_id}):
        diario = ctx.diario(reg["task_id"])
        diario[llave] = {"estado": "INICIADA", "op_id": op_id, "paso": p["paso"], "agente": p["agente"]}
        ctx.anotar(reg["task_id"], diario)
    checkpoint = {"task_id": reg["task_id"], "paso_actual": idx, "estado": reg["estado"], "pasos_terminados": [{"paso": x["paso"], "recibo": x["recibo"]} for x in reg["pasos_terminados"]]}
    try:
        res = ctx.ejecutar_agente(p["agente"], reg["task_id"], p["modelo"], objetivo, contexto, permisos, checkpoint)
    except dispatcher.AgenteError as e:
        r = e.resultado if isinstance(e.resultado, dict) else {}
        seguro = e.codigo == "EJECUCION_AGENTE_FALLIDA" and r.get("efectos_posibles") is False
        return _fallar(ctx, reg, idx, str(r.get("codigo") or e.codigo), str(r.get("error") or e.codigo), seguro, op_id)
    except ValueError as e:  # AGENTE_NO_AUTORIZADO: ni siquiera se importo un adaptador
        return _fallar(ctx, reg, idx, str(e) or "AGENTE_NO_AUTORIZADO", "agente no autorizado", True, op_id)
    except Exception as e:  # noqa: BLE001 - desconocido: pudo haber efectos
        return _fallar(ctx, reg, idx, "AGENTE_EXCEPCION", type(e).__name__, False, op_id)
    texto, recibo = _limpio(ctx, res.get("resultado", "")), res["recibo"]
    if diario is not None:  # el diario conserva la confirmacion aunque el guardado del estado falle justo despues
        diario[llave] = {"estado": "CONFIRMADA", "op_id": op_id, "paso": p["paso"], "agente": p["agente"], "recibo": recibo, "resultado": texto[:2000],
                         "herramientas": res.get("herramientas", []), "evidencias": [_limpio(ctx, e, 300) for e in res.get("evidencias", []) if isinstance(e, str)]}
        ctx.anotar(reg["task_id"], diario)
    reg["operaciones"][op_id].update({"estado": "CONFIRMADA", "fin": _ahora(), "recibo": recibo})
    _cerrar_paso(ctx, reg, idx, texto, recibo, [str(h) for h in res.get("herramientas", [])], [e for e in res.get("evidencias", []) if isinstance(e, str)])
    _guardar_estado(ctx, reg)  # si esto falla: PERSISTENCIA_FALLIDA, la operacion queda INICIADA y se reconcilia/adopta del diario
    return True


def _paso_llm(reg, ctx, idx, p):
    try:
        salida = ctx.llm({"messages": [{"role": "user", "content": reg["mensaje"]}], "modelo": _id_bridge(p["modelo"]), "tarea_id": reg["task_id"]})
    except Exception as e:  # noqa: BLE001
        return _fallar(ctx, reg, idx, "LLM_FALLIDO", "%s: %s" % (type(e).__name__, e), True)
    texto = salida.get("texto") if isinstance(salida, dict) else None
    if not isinstance(texto, str) or not texto.strip():
        return _fallar(ctx, reg, idx, "LLM_SIN_RESPUESTA", "el modelo no devolvio texto", True)
    _cerrar_paso(ctx, reg, idx, texto, "llm:%s:%s" % (salida.get("modelo_respuesta") or p["modelo"], _sha(texto)[:16]), list(salida.get("herramientas_usadas") or []), [])
    _guardar_estado(ctx, reg)
    return True


def _paso_liquid(reg, ctx, idx, p):
    if p["paso"] == "liquid1":
        mensajes = [{"role": "system", "content": "Eres Liquid 1 (lector). Lee y analiza la solicitud; no ejecutes nada. Devuelve un analisis y un plan concreto."},
                    {"role": "user", "content": reg["mensaje"]}]
    else:
        h = reg.get("handoff")
        if not h or h.get("confirmado") is not True:
            return _fallar(ctx, reg, idx, "HANDOFF_NO_CONFIRMADO", "Liquid 2 no ejecuta sin el handoff confirmado de Liquid 1", True)
        guardado = _leer(ctx, _ruta_handoff(reg["ruta"]), opcional=True)
        try:
            d = json.loads(guardado) if guardado else {}
            valido = _sha(d.get("resumen"), d.get("recibo_origen")) == h["sha256"] and d.get("sha256") == h["sha256"]
        except ValueError:
            valido = False
        if not valido:
            return _fallar(ctx, reg, idx, "HANDOFF_NO_CONFIRMADO", "el handoff guardado no coincide con el confirmado", True)
        mensajes = [{"role": "system", "content": "Eres Liquid 2 (ejecutor). Tu contexto es independiente: solo conoces el handoff confirmado de Liquid 1. Devuelve las acciones concretas a ejecutar."},
                    {"role": "user", "content": "Handoff confirmado de Liquid 1 (%s):\n%s\n\nSolicitud: %s" % (h["servidor_origen"], d["resumen"], reg["mensaje"])}]
    try:
        r = ctx.servidor_llm(p["servidor"], _id_bridge(p["modelo"]), mensajes)
    except ValueError as e:
        return _fallar(ctx, reg, idx, str(e) or "LIQUID_LLAMADA_FALLIDA", "servidor %s: %s" % (p["servidor"], e), True)
    except Exception as e:  # noqa: BLE001 - sin efectos: es solo un LLM
        return _fallar(ctx, reg, idx, "LIQUID_LLAMADA_FALLIDA", "servidor %s: %s" % (p["servidor"], type(e).__name__), True)
    texto = r.get("texto") if isinstance(r, dict) else None
    if not isinstance(texto, str) or not texto.strip() or r.get("servidor") != p["servidor"]:
        return _fallar(ctx, reg, idx, "LIQUID_SIN_RESPUESTA", "el servidor %s no devolvio texto valido" % p["servidor"], True)
    fin, cont = r.get("finish_reason"), 0
    while fin == "length" and cont < MAX_CONTINUACIONES:  # cortado por el limite de salida: se pide seguir donde se corto (mismo servidor, nunca otro)
        cont += 1
        try:
            r2 = ctx.servidor_llm(p["servidor"], _id_bridge(p["modelo"]), mensajes + [
                {"role": "assistant", "content": texto},
                {"role": "user", "content": "Continua exactamente donde se corto la respuesta anterior, sin repetir texto."}])
        except Exception:  # noqa: BLE001 - sin efectos: se queda con lo que hay y se marca parcial
            break
        t2 = r2.get("texto") if isinstance(r2, dict) else None
        if not isinstance(t2, str) or not t2.strip() or r2.get("servidor") != p["servidor"]:
            break
        texto, fin = texto + t2, r2.get("finish_reason")
    parcial = fin == "length" or len(texto) > MAX_TEXTO  # truncado por el proveedor o por el tope de almacenamiento: NO es un resultado completo
    if parcial and p["paso"] == "liquid2":
        return _fallar(ctx, reg, idx, "LIQUID_RESPUESTA_PARCIAL", "la respuesta de Liquid 2 quedo truncada (finish_reason=length o mas de %d caracteres): no se pasa a ningun agente" % MAX_TEXTO, True)
    recibo = "liquid:%s:%s:%s" % (p["servidor"], r.get("host"), _sha(texto)[:16])
    _cerrar_paso(ctx, reg, idx, texto, recibo, [], ["servidor:%s" % p["servidor"], "host:%s" % r.get("host"), "modelo_respuesta:%s" % r.get("modelo_respuesta")],
                 **({"parcial": True} if parcial else {}))
    _guardar_estado(ctx, reg)
    return True


def _paso_handoff(reg, ctx, idx, p):
    l1 = next((x for x in reg["pasos_terminados"] if x["paso"] == "liquid1" and x.get("recibo")), None)
    if not l1:
        return _fallar(ctx, reg, idx, "HANDOFF_SIN_ORIGEN", "no hay resultado confirmado de Liquid 1", True)
    resumen = _limpio(ctx, l1["resultado"])
    sha = _sha(resumen, l1["recibo"])
    h = {"de": "liquid1", "servidor_origen": "S2", "servidor_destino": "S3", "recibo_origen": l1["recibo"], "resumen": resumen, "sha256": sha, "fecha": _ahora(), "confirmado": False}
    ruta = _ruta_handoff(reg["ruta"])
    if l1.get("parcial"):  # Liquid 1 quedo cortado: el handoff se guarda como PARCIAL, nunca se confirma y Liquid 2 no corre con el
        h["parcial"] = True
        _guardar(ctx, ruta, json.dumps(h, ensure_ascii=False))
        reg["handoff"] = h
        return _fallar(ctx, reg, idx, "HANDOFF_PARCIAL", "el resultado de Liquid 1 quedo truncado (finish_reason=length o mas de %d caracteres): el handoff es parcial y no se confirma; acorta la solicitud y crea una tarea nueva" % MAX_TEXTO, True)
    _guardar(ctx, ruta, json.dumps(h, ensure_ascii=False))
    releido = json.loads(_leer(ctx, ruta))  # confirmado = guardado Y releido con el mismo contenido
    if _sha(releido.get("resumen"), releido.get("recibo_origen")) != sha:
        return _fallar(ctx, reg, idx, "HANDOFF_NO_CONFIRMADO", "el handoff releido no coincide con el guardado", True)
    reg["handoff"] = {**h, "confirmado": True}
    _cerrar_paso(ctx, reg, idx, "handoff confirmado sha256=" + sha, "handoff:%s" % sha[:20], [], ["handoff:" + ruta])
    _guardar_estado(ctx, reg)
    return True


# ---------------- servidores Liquid reales (S2 / S3) ----------------
def llamar_servidor(servidor, modelo, mensajes, timeout=None):
    """POST {SWECODE_URL_<servidor>}/chat/completions (OpenAI-compatible). Sin URL del servidor pedido NO se usa otro slot; S2 y S3 deben ser distintos."""
    if servidor not in ("S2", "S3"):
        raise ValueError("LIQUID_SERVIDOR_INVALIDO")
    urls = {s: os.environ.get("SWECODE_URL_" + s, "").strip().rstrip("/") for s in ("S2", "S3")}
    url = urls[servidor]
    if not url:
        raise ValueError("LIQUID_SERVIDOR_NO_CONFIGURADO")
    for u in (x for x in urls.values() if x):
        x = urlparse(u)
        if not (x.hostname and not x.username and (x.scheme == "https" or (x.scheme == "http" and x.hostname in ("127.0.0.1", "localhost")))):
            raise ValueError("LIQUID_URL_INVALIDA")
    otro = urls["S3" if servidor == "S2" else "S2"]
    if otro and otro == url:
        raise ValueError("LIQUID_SERVIDORES_NO_INDEPENDIENTES")
    req = urllib.request.Request(url + "/chat/completions", method="POST", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"model": modelo, "messages": mensajes, "temperature": 0.2}).encode())
    try:
        with _comun.abrir(req, timeout or float(os.environ.get("RIU_SWE_TIMEOUT_S", "130"))) as r:  # noqa: S310 (URL validada arriba; sin seguir redirecciones)
            bruto = json.loads(r.read(5_000_000).decode("utf-8", "replace"))
        texto = bruto["choices"][0]["message"]["content"] or ""
        fin = bruto["choices"][0].get("finish_reason")
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LIQUID_LLAMADA_FALLIDA %s: %s" % (servidor, type(exc).__name__)) from None
    return {"texto": texto, "servidor": servidor, "url": url, "host": urlparse(url).netloc, "modelo_respuesta": bruto.get("model") or modelo, "finish_reason": fin}
