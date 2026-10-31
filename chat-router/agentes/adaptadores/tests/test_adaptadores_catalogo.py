"""Catalogo unico de modelos, validadores y contrato TareaSWE (BLOQUE 1 s3-s4)."""
import dataclasses
import pytest

from agentes.adaptadores import modelos
from agentes.adaptadores.contrato import TareaSWE


def tarea(**kw):
    base = dict(task_id="yaiwes-001", origen="yaiwes", mensaje="Revisar proyecto", workflow="swe_code",
                modelo_responde="hf/lfm2.5-350m", modelo_lector="hf/lfm2.5-350m", modelo_tool="hf/qwen2.5-coder-1.5b",
                modelo_revisor="hf/qwen3.5-0.8b", agente_responde="openclaw", agente_tool="swe-agent",
                agente_verificador="openhands")
    base.update(kw)
    return TareaSWE(**base)


def test_catalogo_exacto_cuatro_locales_y_cinco_api():
    assert set(modelos.MODELOS) == {
        "hf/lfm2.5-350m", "hf/qwen2.5-coder-1.5b", "hf/qwen3.5-0.8b", "hf/qwen3-0.6b",
        "groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b",
        "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"}
    assert sum(1 for m in modelos.MODELOS.values() if m["provider"] == "hf") == 4
    assert modelos.MODELOS["nvidia/nvidia/nemotron-3-ultra-550b-a55b"] == {"provider": "nvidia", "model": "nvidia/nemotron-3-ultra-550b-a55b"}
    assert modelos.MODELOS["groq/qwen/qwen3.8-27b"] == {"provider": "groq", "model": "qwen/qwen3.8-27b"}
    assert not any("llama" in k for k in modelos.MODELOS)


def test_constantes_agentes_y_workflows():
    assert modelos.AGENTES == ("openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code")
    assert modelos.WORKFLOWS == ("individual", "swe_code", "liquid_mirror")


def test_validadores():
    assert modelos.validar_modelo("hf/qwen3-0.6b") == {"provider": "hf", "model": "qwen3-0.6b"}
    with pytest.raises(ValueError, match="MODELO_NO_REGISTRADO"):
        modelos.validar_modelo("groq/llama-3.3-70b-versatile")
    with pytest.raises(ValueError, match="AGENTE_NO_REGISTRADO"):
        modelos.validar_agente("bash")
    with pytest.raises(ValueError, match="WORKFLOW_NO_REGISTRADO"):
        modelos.validar_workflow("otro")
    modelos.validar_agente("claude-code")
    modelos.validar_workflow("liquid_mirror")


def test_validar_devuelve_dict_completo_con_defaults():
    d = tarea().validar()
    assert d["modo_agentico"] is False and d["aprobacion"] is False and d["sesion"] == "" and d["proyecto"] == ""
    assert d["agente_tool"] == "swe-agent" and d["modelo_tool"] == "hf/qwen2.5-coder-1.5b"
    assert [f.name for f in dataclasses.fields(TareaSWE)][:11] == [
        "task_id", "origen", "mensaje", "workflow", "modelo_responde", "modelo_lector", "modelo_tool", "modelo_revisor",
        "agente_responde", "agente_tool", "agente_verificador"]


@pytest.mark.parametrize("campo,valor,codigo", [
    ("task_id", "con espacio", "TASK_ID_INVALIDO"), ("task_id", "", "TASK_ID_INVALIDO"), ("task_id", "a" * 65, "TASK_ID_INVALIDO"),
    ("task_id", "../x", "TASK_ID_INVALIDO"), ("origen", "web", "ORIGEN_INVALIDO"), ("mensaje", "   ", "MENSAJE_VACIO"),
    ("workflow", "x", "WORKFLOW_NO_REGISTRADO"), ("modelo_tool", "hf/otro", "MODELO_NO_REGISTRADO"),
    ("modelo_revisor", "nvidia/meta/llama-3.3-70b-instruct", "MODELO_NO_REGISTRADO"), ("agente_tool", "bash", "AGENTE_NO_REGISTRADO"),
    ("agente_responde", "gpt", "AGENTE_NO_REGISTRADO"), ("agente_verificador", "", "AGENTE_NO_REGISTRADO")])
def test_validar_rechaza(campo, valor, codigo):
    with pytest.raises(ValueError, match=codigo):
        tarea(**{campo: valor}).validar()


def test_task_id_con_salto_de_linea_no_pasa_por_fullmatch():
    with pytest.raises(ValueError, match="TASK_ID_INVALIDO"):
        tarea(task_id="ok\n").validar()


def test_desde_dict_estricto():
    d = tarea().validar()
    assert TareaSWE.desde_dict(d).validar() == d
    with pytest.raises(ValueError, match="CAMPOS_DESCONOCIDOS"):
        TareaSWE.desde_dict({**d, "estado": "DONE"})
    d2 = dict(d); d2.pop("mensaje")
    with pytest.raises(ValueError, match="CAMPOS_FALTANTES"):
        TareaSWE.desde_dict(d2)
    with pytest.raises(ValueError, match="CONTRATO_INVALIDO"):
        TareaSWE.desde_dict("no es dict")


def test_contrato_identico_para_ambos_origenes():
    a = tarea(origen="yaiwes").validar(); b = tarea(origen="openclaw").validar()
    assert a.keys() == b.keys()


@pytest.mark.parametrize("campo,valor", [("modo_agentico", "false"), ("modo_agentico", 1), ("aprobacion", "true"), ("sesion", 5), ("proyecto", None)])
def test_tipos_del_contrato(campo, valor):
    with pytest.raises(ValueError, match="CAMPO_TIPO_INVALIDO"):
        tarea(**{campo: valor}).validar()
