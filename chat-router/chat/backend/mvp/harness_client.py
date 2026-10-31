"""Cliente sin dependencias para el Harness remoto (edificio 2)."""
import json
import os
import re
import time
from urllib import error, request

REINTENTABLES = {429, 502, 503, 504}


def _endpoint():
    base = os.environ.get("RIU_DEEPSEEK_HARNESS_URL", "").rstrip("/")
    if not base:
        raise RuntimeError("Harness no configurado")
    if not (base.startswith("https://") or base.startswith("http://127.0.0.1:")):
        raise ValueError("URL Harness requiere HTTPS")
    return base + "/invoke"


def _enviar(accion, datos, clave):
    if accion not in ("status", "invoke", "llm"):
        raise ValueError("accion Harness no permitida")
    if not isinstance(clave, str) or not clave:
        raise RuntimeError("credencial Harness ausente en banco")
    url = _endpoint()
    headers = {"Content-Type": "application/json", "X-API-Key": clave}
    cuerpo = json.dumps({"action": accion, **datos}).encode("utf-8")
    solicitud = request.Request(url, data=cuerpo, headers=headers, method="POST")
    for intento in range(3):
        try:
            with request.urlopen(solicitud, timeout=None) as respuesta:
                return json.load(respuesta)
        except error.HTTPError as exc:
            if exc.code == 403:
                try:
                    motivo = str(json.loads(exc.read() or b"{}").get("detail") or "")[:160]
                except ValueError:
                    motivo = ""
                return {"status": "error", "status_code": 403, "error": "Herramienta bloqueada por Router (HTTP 403)" + (": " + motivo if motivo else "")}
            if exc.code not in REINTENTABLES or intento == 2:
                raise RuntimeError("Harness HTTP " + str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError):
            raise RuntimeError("Harness no disponible") from None
        time.sleep(min(2 ** intento, 2))


def status(clave):
    return _enviar("status", {}, clave)


def guardar(clave, nombre, valor):
    return _enviar("invoke", {"tool": "guardar", "args": {"nombre": nombre, "valor": valor}}, clave)


def leer(clave, nombre):
    return _enviar("invoke", {"tool": "leer", "args": {"nombre": nombre}}, clave)


def computar(clave, tarea):
    return _enviar("invoke", {"tool": "computar", "args": {"tarea": tarea}}, clave)


def llm(clave, mensajes, modelo, opciones=None, controles=None):
    return _enviar("llm", {"mensajes": mensajes, "modelo": modelo,
                          "opciones": opciones or {}, **(controles or {})}, clave)


# --- SWE: tareas con agentes reales. YAIWES -> (aqui) -> Harness -> agentes/adaptadores. El contrato y el catalogo son los de agentes/adaptadores (no se copian). ---
SWE_OPERACIONES = frozenset(("swe_iniciar", "swe_avanzar", "swe_estado", "swe_aprobar", "swe_reanudar"))
_TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
_SEGMENTO = re.compile(r"[A-Za-z0-9_-]{0,64}")
_OP_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
_OPERADOR = re.compile(r"[A-Za-z0-9_.@-]{2,64}")
_CODIGO = re.compile(r"[A-Z][A-Z0-9_]{2,63}")
SWE_MAX_MENSAJE = 200_000


def swe_invoke(clave, operacion, datos):
    permitidas = SWE_OPERACIONES
    if not isinstance(operacion, str) or operacion not in permitidas:
        raise ValueError("OPERACION_SWE_NO_AUTORIZADA")
    if not isinstance(datos, dict):
        raise ValueError("DATOS_SWE_INVALIDOS")
    return _enviar("invoke", {"tool": operacion, "args": datos}, clave)


def swe_argumentos(operacion, cuerpo, operador=None):
    """Argumentos para el Harness desde el cuerpo del frontend. iniciar = el contrato TareaSWE exacto (origen siempre yaiwes, aprobacion siempre False);
    el resto solo task_id/origen/sesion/proyecto (+ op_id y el operador que pone el SERVIDOR en aprobar). Nada mas del cliente cruza."""
    if operacion not in SWE_OPERACIONES:
        raise ValueError("OPERACION_SWE_NO_AUTORIZADA")
    if not isinstance(cuerpo, dict):
        raise ValueError("CONTRATO_INVALIDO")
    if operacion == "swe_iniciar":
        from agentes.adaptadores.contrato import TareaSWE  # contrato unico YAIWES/OpenClaw: validar() es el de los adaptadores
        if cuerpo.get("origen") != "yaiwes":
            raise ValueError("ORIGEN_INVALIDO")
        if any(type(cuerpo.get(k, False)) is not bool for k in ("modo_agentico", "aprobacion")):
            raise ValueError("CONTRATO_INVALIDO")
        if any(not isinstance(cuerpo.get(k, ""), str) or not _SEGMENTO.fullmatch(cuerpo.get(k, "")) for k in ("sesion", "proyecto")):
            raise ValueError("CONTRATO_INVALIDO")
        if isinstance(cuerpo.get("mensaje"), str) and len(cuerpo["mensaje"]) > SWE_MAX_MENSAJE:
            raise ValueError("MENSAJE_DEMASIADO_LARGO")
        tarea = TareaSWE.desde_dict(cuerpo).validar()
        tarea["aprobacion"] = False  # la aprobacion solo la da swe_aprobar con operador identificado
        return tarea
    task_id = cuerpo.get("task_id")
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        raise ValueError("TASK_ID_INVALIDO")
    if cuerpo.get("origen", "yaiwes") != "yaiwes":
        raise ValueError("ORIGEN_INVALIDO")
    args = {"task_id": task_id, "origen": "yaiwes"}
    for k in ("sesion", "proyecto"):
        v = cuerpo.get(k)
        if v not in (None, ""):
            if not isinstance(v, str) or not _SEGMENTO.fullmatch(v):
                raise ValueError("CONTRATO_INVALIDO")
            args[k] = v
    if operacion == "swe_aprobar":
        op_id = cuerpo.get("op_id")
        if not isinstance(op_id, str) or not _OP_ID.fullmatch(op_id):
            raise ValueError("OP_ID_INVALIDO")
        if not isinstance(operador, str) or not _OPERADOR.fullmatch(operador):
            raise ValueError("OPERADOR_NO_CONFIGURADO")
        args.update(op_id=op_id, operador=operador)  # quien aprueba lo fija el servidor autenticado: ni `aprobacion` ni `operador` del cliente o del modelo cuentan
    return args


def swe_error(salida):
    """Codigo estable de un error del Harness ({"status":"error","error":CODIGO}); cualquier otro texto se descarta (puede traer rutas o credenciales)."""
    e = salida.get("error") if isinstance(salida, dict) else None
    return e if isinstance(e, str) and _CODIGO.fullmatch(e) else None


def swe_capacidades(status):
    """Lo que el Harness reporta conectado en su `status` (result.swe.{agentes,workflows,modelos}), saneado contra el catalogo unico. Lo que no reporta no se inventa."""
    from agentes.adaptadores import modelos as cat
    swe = (status.get("result") if isinstance(status, dict) else None) or {}
    swe = swe.get("swe") if isinstance(swe, dict) else None
    swe = swe if isinstance(swe, dict) else {}
    salida = {}
    for grupo, validos in (("agentes", cat.AGENTES), ("workflows", cat.WORKFLOWS), ("modelos", cat.MODELOS)):
        entradas = swe.get(grupo) if isinstance(swe.get(grupo), dict) else {}
        salida[grupo] = {}
        for k, v in entradas.items():
            if k not in validos or not isinstance(v, dict) or type(v.get("disponible")) is not bool:
                continue
            e = {"disponible": v["disponible"]}
            if isinstance(v.get("motivo"), str) and v["motivo"]:
                e["motivo"] = v["motivo"][:200]
            if grupo == "agentes" and isinstance(v.get("modelos"), list):
                e["modelos"] = [m for m in v["modelos"] if isinstance(m, str) and m in cat.MODELOS]
            salida[grupo][k] = e
    return salida
