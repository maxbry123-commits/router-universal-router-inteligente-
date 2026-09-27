"""Tests de la traducción Anthropic <-> NVIDIA/OpenAI. CERO red."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from normalizar import (anthropic_a_openai, estimar_tokens, modelo_destino,
                        openai_a_anthropic)


def test_alias_claude_a_modelo_nvidia():
    assert modelo_destino("claude-opus-4-1", "moonshotai/kimi-k2.5") == \
        "moonshotai/kimi-k2.5"
    assert modelo_destino("claude-sonnet-4-5", "z-ai/glm4.7") == "z-ai/glm4.7"
    assert modelo_destino("claude-haiku-4-5-20251001", "m") == "m"


def test_modelo_no_alias_se_respeta():
    assert modelo_destino("nvidia/otro-modelo", "m") == "nvidia/otro-modelo"


def test_system_y_mensajes_texto():
    salida = anthropic_a_openai({
        "model": "claude-sonnet-4-5",
        "system": "Eres conciso.",
        "messages": [{"role": "user", "content": "hola"}],
        "max_tokens": 100,
    }, modelo_env="m")
    assert salida["messages"][0] == {"role": "system", "content": "Eres conciso."}
    assert salida["messages"][1] == {"role": "user", "content": "hola"}
    assert salida["max_tokens"] == 100
    assert salida["model"] == "m"


def test_system_como_lista_de_bloques():
    salida = anthropic_a_openai({
        "system": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}],
        "messages": [],
    }, modelo_env="m")
    assert salida["messages"][0]["content"] == "ab"


def test_tool_use_a_tool_calls():
    salida = anthropic_a_openai({
        "messages": [{"role": "assistant", "content": [
            {"type": "text", "text": "voy a leer"},
            {"type": "tool_use", "id": "toolu_1", "name": "Read",
             "input": {"file_path": "/tmp/x"}},
        ]}],
    }, modelo_env="m")
    msg = salida["messages"][0]
    assert msg["role"] == "assistant"
    assert msg["content"] == "voy a leer"
    assert msg["tool_calls"][0]["id"] == "toolu_1"
    assert msg["tool_calls"][0]["function"]["name"] == "Read"
    assert json.loads(msg["tool_calls"][0]["function"]["arguments"]) == \
        {"file_path": "/tmp/x"}


def test_tool_result_a_role_tool():
    salida = anthropic_a_openai({
        "messages": [{"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_1",
             "content": "contenido del archivo"},
        ]}],
    }, modelo_env="m")
    assert {"role": "tool", "tool_call_id": "toolu_1",
            "content": "contenido del archivo"} in salida["messages"]


def test_reasoning_thinking_output_config_eliminados():
    salida = anthropic_a_openai({
        "messages": [{"role": "user", "content": "hola"}],
        "thinking": {"type": "adaptive"},
        "reasoning": {"effort": "high"},
        "output_config": {"format": "json"},
    }, modelo_env="m")
    for campo in ("thinking", "reasoning", "output_config"):
        assert campo not in salida


def test_tools_anthropic_a_openai():
    salida = anthropic_a_openai({
        "messages": [],
        "tools": [{"name": "Read", "description": "lee",
                   "input_schema": {"type": "object",
                                    "properties": {"file_path": {"type": "string"}}}}],
        "tool_choice": {"type": "any"},
    }, modelo_env="m")
    assert salida["tools"][0]["function"]["name"] == "Read"
    assert salida["tools"][0]["function"]["parameters"]["type"] == "object"
    assert salida["tool_choice"] == "required"


def test_respuesta_texto_a_anthropic():
    salida = openai_a_anthropic({
        "id": "chatcmpl-1",
        "choices": [{"message": {"role": "assistant", "content": "hola"},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }, modelo_original="claude-sonnet-4-5")
    assert salida["type"] == "message"
    assert salida["role"] == "assistant"
    assert salida["content"] == [{"type": "text", "text": "hola"}]
    assert salida["stop_reason"] == "end_turn"
    assert salida["usage"] == {"input_tokens": 10, "output_tokens": 5}
    assert salida["model"] == "claude-sonnet-4-5"


def test_respuesta_tool_calls_a_tool_use():
    salida = openai_a_anthropic({
        "choices": [{"message": {"role": "assistant", "content": None,
                                 "tool_calls": [{
                                     "id": "call_1", "type": "function",
                                     "function": {"name": "Read",
                                                  "arguments": '{"file_path": "/a"}'}}]},
                     "finish_reason": "tool_calls"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 7},
    })
    bloque = salida["content"][0]
    assert bloque["type"] == "tool_use"
    assert bloque["id"] == "call_1"
    assert bloque["name"] == "Read"
    assert bloque["input"] == {"file_path": "/a"}
    assert salida["stop_reason"] == "tool_use"


def test_finish_reason_length_es_max_tokens():
    salida = openai_a_anthropic({
        "choices": [{"message": {"content": "..."}, "finish_reason": "length"}]})
    assert salida["stop_reason"] == "max_tokens"


def test_arguments_invalidos_no_rompen():
    salida = openai_a_anthropic({
        "choices": [{"message": {"tool_calls": [{
            "id": "c", "type": "function",
            "function": {"name": "X", "arguments": "{no-json"}}]},
            "finish_reason": "tool_calls"}]})
    assert salida["content"][0]["input"] == {}


def test_estimar_tokens():
    n = estimar_tokens({
        "system": "abcd" * 10,
        "messages": [{"role": "user", "content": "hola mundo"}],
    })
    assert n >= 10
