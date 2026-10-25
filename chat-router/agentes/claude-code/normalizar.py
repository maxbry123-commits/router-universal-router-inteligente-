"""Funciones puras de traducción Anthropic Messages <-> NVIDIA/OpenAI chat.

Sin red, sin estado global mutable. Todo el módulo es testeable offline.
"""
import json
import os
import re
import uuid

MODELO_POR_DEFECTO = "moonshotai/kimi-k2.5"

_ALIAS_CLAUDE = re.compile(r"^claude-(opus|sonnet|haiku)[\w.-]*$", re.IGNORECASE)

# Campos que NVIDIA/OpenAI no soporta y hay que eliminar del request
_CAMPOS_PROHIBIDOS = ("reasoning", "output_config", "thinking", "metadata")


def modelo_destino(modelo, modelo_env=None):
    """Resuelve alias claude-opus/sonnet/haiku-* al modelo NVIDIA configurado."""
    destino = modelo_env or os.environ.get("MODELO") or MODELO_POR_DEFECTO
    if not modelo:
        return destino
    if _ALIAS_CLAUDE.match(str(modelo)):
        return destino
    return modelo


def _texto_de_contenido(contenido):
    """Extrae texto plano de un content Anthropic (str o lista de bloques)."""
    if isinstance(contenido, str):
        return contenido
    partes = []
    if isinstance(contenido, list):
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(bloque.get("text", ""))
    return "".join(partes)


def _mensaje_usuario_a_openai(mensaje):
    """Convierte un mensaje user Anthropic (puede llevar tool_result)."""
    contenido = mensaje.get("content")
    salida = []
    if isinstance(contenido, list):
        textos = []
        for bloque in contenido:
            if not isinstance(bloque, dict):
                continue
            tipo = bloque.get("type")
            if tipo == "tool_result":
                cuerpo = bloque.get("content")
                salida.append({
                    "role": "tool",
                    "tool_call_id": bloque.get("tool_use_id", ""),
                    "content": _texto_de_contenido(cuerpo) if cuerpo is not None else "",
                })
            elif tipo == "text":
                textos.append(bloque.get("text", ""))
        if textos:
            salida.insert(0, {"role": "user", "content": "".join(textos)})
        if salida:
            return salida
    return [{"role": "user", "content": _texto_de_contenido(contenido)}]


def _mensaje_assistant_a_openai(mensaje):
    """Convierte un mensaje assistant Anthropic (tool_use -> tool_calls)."""
    contenido = mensaje.get("content")
    if isinstance(contenido, str):
        return [{"role": "assistant", "content": contenido}]
    texto = []
    tool_calls = []
    for bloque in contenido or []:
        if not isinstance(bloque, dict):
            continue
        tipo = bloque.get("type")
        if tipo == "text":
            texto.append(bloque.get("text", ""))
        elif tipo == "tool_use":
            tool_calls.append({
                "id": bloque.get("id", "call_" + uuid.uuid4().hex[:8]),
                "type": "function",
                "function": {
                    "name": bloque.get("name", ""),
                    "arguments": json.dumps(bloque.get("input") or {}),
                },
            })
    msg = {"role": "assistant", "content": "".join(texto) or None}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return [msg]


def anthropic_a_openai(peticion, modelo_env=None):
    """Traduce un request Anthropic /v1/messages a OpenAI /chat/completions."""
    peticion = dict(peticion or {})
    mensajes = []
    sistema = peticion.get("system")
    if sistema:
        mensajes.append({"role": "system", "content": _texto_de_contenido(sistema)})
    for mensaje in peticion.get("messages") or []:
        rol = mensaje.get("role")
        if rol == "user":
            mensajes.extend(_mensaje_usuario_a_openai(mensaje))
        elif rol == "assistant":
            mensajes.extend(_mensaje_assistant_a_openai(mensaje))

    salida = {
        "model": modelo_destino(peticion.get("model"), modelo_env),
        "messages": mensajes,
        "stream": bool(peticion.get("stream")),
    }
    if peticion.get("max_tokens"):
        salida["max_tokens"] = peticion["max_tokens"]
    if peticion.get("temperature") is not None:
        salida["temperature"] = peticion["temperature"]
    if peticion.get("top_p") is not None:
        salida["top_p"] = peticion["top_p"]
    if peticion.get("stop_sequences"):
        salida["stop"] = peticion["stop_sequences"]

    herramientas = peticion.get("tools")
    if herramientas:
        salida["tools"] = [{
            "type": "function",
            "function": {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
            },
        } for t in herramientas]
        eleccion = peticion.get("tool_choice")
        if isinstance(eleccion, dict):
            tipo = eleccion.get("type")
            if tipo == "any":
                salida["tool_choice"] = "required"
            elif tipo == "tool" and eleccion.get("name"):
                salida["tool_choice"] = {
                    "type": "function",
                    "function": {"name": eleccion["name"]},
                }
            else:
                salida["tool_choice"] = "auto"

    # thinking adaptive / reasoning / output_config: no soportados -> eliminar
    for campo in _CAMPOS_PROHIBIDOS:
        salida.pop(campo, None)
    return salida


def _stop_reason(finish_reason, hay_tool_calls):
    if finish_reason == "tool_calls" or hay_tool_calls:
        return "tool_use"
    if finish_reason == "length":
        return "max_tokens"
    if finish_reason == "stop" or finish_reason is None:
        return "end_turn"
    return "end_turn"


def openai_a_anthropic(respuesta, modelo_original=None):
    """Traduce una respuesta OpenAI chat.completion a Anthropic Message."""
    respuesta = respuesta or {}
    eleccion = (respuesta.get("choices") or [{}])[0]
    mensaje = eleccion.get("message") or {}
    bloques = []
    if mensaje.get("content"):
        bloques.append({"type": "text", "text": mensaje["content"]})
    for llamada in mensaje.get("tool_calls") or []:
        funcion = llamada.get("function") or {}
        try:
            argumentos = json.loads(funcion.get("arguments") or "{}")
        except (TypeError, ValueError):
            argumentos = {}
        bloques.append({
            "type": "tool_use",
            "id": llamada.get("id", "toolu_" + uuid.uuid4().hex[:8]),
            "name": funcion.get("name", ""),
            "input": argumentos,
        })
    uso = respuesta.get("usage") or {}
    return {
        "id": respuesta.get("id", "msg_" + uuid.uuid4().hex[:12]),
        "type": "message",
        "role": "assistant",
        "model": modelo_original or respuesta.get("model", ""),
        "content": bloques,
        "stop_reason": _stop_reason(eleccion.get("finish_reason"),
                                    bool(mensaje.get("tool_calls"))),
        "stop_sequence": None,
        "usage": {
            "input_tokens": uso.get("prompt_tokens", 0),
            "output_tokens": uso.get("completion_tokens", 0),
        },
    }


def estimar_tokens(peticion):
    """Estimación grosera de tokens de entrada para /v1/messages/count_tokens."""
    total = 0
    peticion = peticion or {}
    textos = [_texto_de_contenido(peticion.get("system") or "")]
    for mensaje in peticion.get("messages") or []:
        textos.append(_texto_de_contenido(mensaje.get("content")))
        if isinstance(mensaje.get("content"), list):
            for bloque in mensaje["content"]:
                if isinstance(bloque, dict) and bloque.get("type") == "tool_use":
                    textos.append(json.dumps(bloque.get("input") or {}))
    for herramienta in peticion.get("tools") or []:
        textos.append(herramienta.get("name", ""))
        textos.append(herramienta.get("description", ""))
    for texto in textos:
        total += max(1, len(texto) // 4)
    return total
