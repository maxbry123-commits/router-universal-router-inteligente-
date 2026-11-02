"""Subproceso seguro compartido por los adaptadores: lista de argumentos, sin shell, timeout, limite de salida, entorno minimo."""
import os
import stat
import sys
import pytest

from agentes.adaptadores import _comun


def script(tmp_path, nombre, cuerpo):
    p = tmp_path / nombre
    p.write_text("#!%s\n%s\n" % (sys.executable, cuerpo))
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def test_ejecuta_sin_shell_y_con_argumentos_literales(tmp_path):
    s = script(tmp_path, "eco", "import sys,json; print(json.dumps(sys.argv[1:]))")
    r = _comun.ejecutar_proceso([s, "a b", "$(whoami)", ";rm -rf /", "`id`"], cwd=str(tmp_path), env=_comun.entorno_base(), timeout=10)
    assert r["exit_code"] == 0 and not r["timeout"]
    import json
    assert json.loads(r["stdout"]) == ["a b", "$(whoami)", ";rm -rf /", "`id`"]


def test_timeout_mata_el_proceso(tmp_path):
    s = script(tmp_path, "lento", "import time; time.sleep(30)")
    r = _comun.ejecutar_proceso([s], cwd=str(tmp_path), env=_comun.entorno_base(), timeout=0.5)
    assert r["timeout"] is True and r["exit_code"] != 0


def test_limite_de_salida(tmp_path):
    s = script(tmp_path, "mucho", "import sys\nfor _ in range(200000): sys.stdout.write('x'*100)\n")
    r = _comun.ejecutar_proceso([s], cwd=str(tmp_path), env=_comun.entorno_base(), timeout=20, max_salida=10_000)
    assert r["truncado"] is True and len(r["stdout"]) <= 10_000


def test_entorno_minimo_no_filtra_claves(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "valor-secreto-de-prueba")
    monkeypatch.setenv("RIU_API_KEY", "otro-secreto-de-prueba")
    e = _comun.entorno_base()
    assert "GROQ_API_KEY" not in e and "RIU_API_KEY" not in e and "PATH" in e


def test_binario_prefiere_variable_y_valida_ejecutable(monkeypatch, tmp_path):
    s = script(tmp_path, "x", "pass")
    monkeypatch.setenv("RIU_PRUEBA_BIN", s)
    assert _comun.binario("noexiste-xyz", "RIU_PRUEBA_BIN") == s
    monkeypatch.setenv("RIU_PRUEBA_BIN", str(tmp_path / "no-existe"))
    assert _comun.binario("noexiste-xyz", "RIU_PRUEBA_BIN") is None
    monkeypatch.delenv("RIU_PRUEBA_BIN")
    assert _comun.binario("noexiste-xyz", "RIU_PRUEBA_BIN") is None


def test_preparar_valida_entradas(tmp_path):
    ok = dict(tarea_id="t-1", modelo="hf/lfm2.5-350m", objetivo="hacer algo", contexto="ctx", permisos={"directorio": str(tmp_path)}, checkpoint={})
    p = _comun.preparar("codex", **ok)
    assert p["prompt"].startswith("Tarea t-1") and "hacer algo" in p["prompt"] and p["directorio"] == str(tmp_path)
    for cambio, codigo in [({"tarea_id": "../x"}, "TASK_ID_INVALIDO"), ({"modelo": "x/y"}, "MODELO_NO_REGISTRADO"),
                           ({"objetivo": "  "}, "OBJETIVO_VACIO"), ({"permisos": "no"}, "PERMISOS_INVALIDOS"),
                           ({"permisos": {"directorio": str(tmp_path / "nada")}}, "DIRECTORIO_INVALIDO"),
                           ({"permisos": {}}, "DIRECTORIO_INVALIDO")]:
        with pytest.raises(_comun.ErrorPrevio) as e:
            _comun.preparar("codex", **{**ok, **cambio})
        assert e.value.resultado["codigo"] == codigo and e.value.resultado["ok"] is False and e.value.resultado["efectos_posibles"] is False


def test_prompt_nunca_empieza_por_guion(tmp_path):
    p = _comun.preparar("codex", "t-1", "hf/lfm2.5-350m", "--help; rm", "", {"directorio": str(tmp_path)}, {})
    assert not p["prompt"].startswith("-")


def test_endpoint_hf_usa_bridge_y_modelo_desnudo(monkeypatch):
    monkeypatch.delenv("RIU_AGENTES_LLM_BASE_URL", raising=False)
    monkeypatch.setenv("RIU_SWE_BRIDGE_URL", "http://127.0.0.1:7870")
    e = _comun.endpoint_modelo("hf/qwen3-0.6b")
    assert e["base_url"] == "http://127.0.0.1:7870/v1" and e["modelo"] == "qwen3-0.6b" and e["proveedor"] == "hf"


def test_endpoint_groq_nvidia_requieren_clave_del_entorno(monkeypatch):
    for v in ("RIU_API_KEY", "BRIDGE_TOKEN", "RIU_AGENTES_LLM_API_KEY",
              "GROQ_API_KEY", "GROQ_API_KEY_1", "NVIDIA_API_KEY", "NVIDIA_API_KEY_1"):
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(_comun.ErrorPrevio) as e:
        _comun.endpoint_modelo("groq/qwen/qwen3.8-27b")
    assert e.value.resultado["codigo"] == "AGENTE_NO_CONFIGURADO"
    monkeypatch.setenv("GROQ_API_KEY_1", "clave-de-prueba-ficticia")
    g = _comun.endpoint_modelo("groq/qwen/qwen3.8-27b")
    assert g["base_url"] == "https://api.groq.com/openai/v1" and g["modelo"] == "qwen/qwen3.8-27b" and g["api_key"] == "clave-de-prueba-ficticia"
    monkeypatch.setenv("NVIDIA_API_KEY", "otra-clave-ficticia")
    n = _comun.endpoint_modelo("nvidia/z-ai/glm-5.3")
    assert n["base_url"] == "https://integrate.api.nvidia.com/v1" and n["modelo"] == "z-ai/glm-5.3"



def test_agentes_usan_la_clave_del_chat_para_el_bridge_existente(monkeypatch):
    for k in ("RIU_AGENTES_LLM_API_KEY", "BRIDGE_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RIU_API_KEY", "clave-ficticia-del-chat")
    assert _comun._credencial_bridge() == "clave-ficticia-del-chat"
    hf = _comun.endpoint_modelo("hf/lfm2.5-350m")
    assert hf["modelo"] == "lfm2.5-350m" and hf["api_key"] == "clave-ficticia-del-chat"


def test_proveedores_sin_variable_reutilizan_banco_del_bridge(monkeypatch):
    for k in ["RIU_AGENTES_LLM_API_KEY", "BRIDGE_TOKEN", "RIU_AGENTES_LLM_BASE_URL",
              "GROQ_API_KEY", "NVIDIA_API_KEY"] + [f"GROQ_API_KEY_{n}" for n in range(1, 21)] + [f"NVIDIA_API_KEY_{n}" for n in range(1, 21)]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RIU_API_KEY", "clave-ficticia-del-chat")
    monkeypatch.setenv("RIU_SWE_BRIDGE_URL", "http://127.0.0.1:7870")
    for model in ("groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash"):
        ep = _comun.endpoint_modelo(model)
        assert ep["modelo"] == model
        assert ep["base_url"] == "http://127.0.0.1:7870/v1"
        assert ep["api_key"] == "clave-ficticia-del-chat"


def test_recibo_es_hash_de_la_ejecucion_real():
    a = _comun.recibo("codex", "t-1", 0, "salida real", "2026-10-31T00:00:00Z")
    assert a.startswith("codex:t-1:") and a == _comun.recibo("codex", "t-1", 0, "salida real", "2026-10-31T00:00:00Z")
    assert a != _comun.recibo("codex", "t-1", 0, "otra salida", "2026-10-31T00:00:00Z")


def test_redactar_oculta_claves():
    assert "[REDACTADO]" in _comun.redactar("token sk-abcdefghijklmnop1234 fin")
    assert "ghp_abcdefghijklm" not in _comun.redactar("x ghp_abcdefghijklmnop y")


def test_redactar_cubre_por_valor_las_variables_sensibles_del_entorno(monkeypatch):
    monkeypatch.setenv("RIU_API_KEY", "valor-secreto-sin-forma-conocida-1")
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "otro-valor-secreto-2")
    monkeypatch.setenv("GROQ_API_KEY_3", "tercera-clave-groq-ficticia")
    monkeypatch.setenv("CORTA_KEY", "abc")  # demasiado corta: no se redacta (no destrozar texto normal)
    monkeypatch.setenv("NO_ES_CREDENCIAL", "valor-normal-largo-123")
    t = _comun.redactar("salida: valor-secreto-sin-forma-conocida-1 y otro-valor-secreto-2; tercera-clave-groq-ficticia abc valor-normal-largo-123")
    assert "valor-secreto-sin-forma-conocida-1" not in t and "otro-valor-secreto-2" not in t and "tercera-clave-groq-ficticia" not in t
    assert t.count("[REDACTADO]") == 3 and "abc" in t and "valor-normal-largo-123" in t
    assert "[REDACTADO]" in _comun.redactar("gsk_abcdefghijklmnop")  # la forma sigue funcionando


def test_error_y_resultado_ok_redactan_por_valor(monkeypatch):
    monkeypatch.setenv("RIU_API_KEY", "valor-secreto-sin-forma-conocida-1")
    e = _comun.error("codex", "t-1", "X", "fallo con valor-secreto-sin-forma-conocida-1 dentro")
    assert "valor-secreto" not in e["error"]
    proc = {"exit_code": 0, "stdout": "", "stderr": "", "duracion_s": 0, "truncado": False}
    r = _comun.resultado_ok("codex", "t-1", proc, "texto valor-secreto-sin-forma-conocida-1", [], [], "2026-01-01T00:00:00Z")
    assert "valor-secreto" not in r["resultado"]
