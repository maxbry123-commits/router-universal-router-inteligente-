"""Adaptador OpenClaw: Gateway existente (por defecto http://127.0.0.1:18789), API OpenAI-compatible POST /v1/chat/completions con
Authorization: Bearer <OPENCLAW_GATEWAY_TOKEN> (docs.openclaw.ai/gateway/openai-http-api; hay que habilitar el endpoint en el Gateway).
Modelo: model "openclaw/default" y cabecera x-openclaw-model "swecode/<id>" (proveedor swecode de SWE CODE free/provider-openclaw.json).
Gateway inaccesible -> AGENTE_NO_INSTALADO (no hay nada que ejecutar). Las politicas de permisos son las del Gateway; una tarea de solo lectura se rechaza (POLITICA_NO_GARANTIZADA) salvo que el operador declare el Gateway en solo lectura. Sin seguir redirecciones."""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from . import _comun
from .modelos import validar_modelo

AGENTE = "openclaw"


def _url():
    u = os.environ.get("RIU_OPENCLAW_URL", "http://127.0.0.1:18789").strip().rstrip("/")
    try:
        x = urlparse(u)
        ok = x.hostname and not x.username and (x.scheme == "https" or (x.scheme == "http" and x.hostname in ("127.0.0.1", "localhost", "::1")))
    except ValueError:
        ok = False
    return u if ok else None


def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    try:
        p = _comun.preparar(AGENTE, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
    except _comun.ErrorPrevio as e:
        return e.resultado
    base = _url()
    if not base:
        return _comun.error(AGENTE, tarea_id, "OPENCLAW_URL_INVALIDA", "RIU_OPENCLAW_URL debe ser https o loopback http")
    token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
    if not token:
        return _comun.error(AGENTE, tarea_id, "AGENTE_NO_CONFIGURADO", "falta OPENCLAW_GATEWAY_TOKEN en el entorno del Harness")
    if not (p["escritura"] or p["ejecucion"]) and os.environ.get("RIU_OPENCLAW_GATEWAY_SOLO_LECTURA", "").strip() != "1":
        # El Gateway aplica SUS politicas y este adaptador no puede imponerle solo-lectura: una tarea de lectura no se ejecuta a ciegas.
        # El operador puede declarar (RIU_OPENCLAW_GATEWAY_SOLO_LECTURA=1) que su Gateway esta configurado sin herramientas de escritura/ejecucion.
        return _comun.error(AGENTE, tarea_id, "POLITICA_NO_GARANTIZADA", "el Gateway OpenClaw no puede garantizar solo-lectura: la tarea no se ejecuta (usa otro agente, o declara el Gateway en solo lectura con RIU_OPENCLAW_GATEWAY_SOLO_LECTURA=1)", False)
    cfg = validar_modelo(modelo)
    id_bridge = cfg["model"] if cfg["provider"] == "hf" else modelo
    cuerpo = json.dumps({"model": "openclaw/default", "user": "conv:" + tarea_id, "messages": [{"role": "user", "content": p["prompt"]}]}).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", data=cuerpo, method="POST", headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + token, "x-openclaw-model": "swecode/" + id_bridge})
    inicio, t0 = _comun.ahora(), time.monotonic()
    try:
        with _comun.abrir(req, _comun.TIMEOUT_S) as r:  # noqa: S310 (URL validada arriba; sin seguir redirecciones)
            bruto = r.read(_comun.MAX_SALIDA + 1)
            estado = r.status
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            return _comun.error(AGENTE, tarea_id, "REDIRECCION_NO_PERMITIDA", "el Gateway respondio una redireccion HTTP %d: no se sigue (el token solo va al host configurado)" % exc.code, False)
        if exc.code in (401, 403, 404):
            return _comun.error(AGENTE, tarea_id, "AGENTE_NO_CONFIGURADO", "el Gateway respondio HTTP %d (token o endpoint chatCompletions no habilitado)" % exc.code)
        return _comun.error(AGENTE, tarea_id, "AGENTE_SALIO_CON_ERROR", "el Gateway respondio HTTP %d" % exc.code, True)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ConnectionRefusedError) or "refused" in str(exc.reason).lower() or "unreachable" in str(exc.reason).lower():
            return _comun.no_instalado(AGENTE, tarea_id, "El Gateway no responde en %s." % base)
        return _comun.error(AGENTE, tarea_id, "AGENTE_TIMEOUT", "sin respuesta del Gateway: %s" % type(exc.reason).__name__, True)
    except TimeoutError:
        return _comun.error(AGENTE, tarea_id, "AGENTE_TIMEOUT", "el Gateway no respondio a tiempo", True)
    try:
        datos = json.loads(bruto.decode("utf-8", "replace"))
        texto = str(datos["choices"][0]["message"]["content"] or "").strip()
    except (ValueError, KeyError, IndexError, TypeError):
        texto = ""
        datos = {}
    if not texto:
        return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "el Gateway no devolvio contenido", True)
    proc = {"exit_code": 0, "stdout": hashlib.sha256(bruto).hexdigest(), "stderr": str(datos.get("id") or ""), "duracion_s": round(time.monotonic() - t0, 3), "truncado": len(bruto) > _comun.MAX_SALIDA}
    return _comun.resultado_ok(AGENTE, tarea_id, proc, texto, [], ["gateway:" + base, "http:%d" % estado, "id:%s" % datos.get("id"), "modelo_gateway:%s" % datos.get("model")], inicio,
                               "swecode/" + id_bridge if datos.get("model") in (None, "openclaw/default") else str(datos["model"]))
