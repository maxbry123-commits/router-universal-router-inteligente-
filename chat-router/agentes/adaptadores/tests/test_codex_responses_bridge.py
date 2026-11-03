"""Codex: Responses via bridge existente; prueba sin red y sin tokens reales."""
import os
from agentes.adaptadores import _comun, codex


def test_codex_minimax_usa_bridge_responses_y_no_api_directa(monkeypatch, tmp_path):
    for k in ("RIU_CODEX_BASE_URL", "RIU_AGENTES_LLM_BASE_URL", "RIU_SWE_BRIDGE_URL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("BRIDGE_TOKEN", "credencial-ficticia-puente")
    monkeypatch.setattr(_comun, "preparar", lambda *a: {
        "directorio": str(tmp_path), "escritura": False,
        "ejecucion": False, "prompt": "Audita", "tarea_id": "t-1"})
    monkeypatch.setattr(_comun, "binario", lambda *a: "/usr/bin/codex")
    monkeypatch.setattr(_comun, "endpoint_modelo", lambda *a: {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "CLAVE-PROVEEDOR-NO-ENVIAR",
        "modelo": "minimaxai/minimax-m3.1-flash"})
    capturado = {}

    def simular(argv, cwd, env, entrada=None):
        capturado["args"], capturado["env"] = argv, env
        with open(argv[argv.index("-o") + 1], "w", encoding="utf-8") as f:
            f.write("Evidencia confirmada")
        return {"timeout": False, "exit_code": 0, "stdout": "", "stderr": "",
                "truncado": False, "duracion_s": 0.01}

    monkeypatch.setattr(_comun, "ejecutar_proceso", simular)
    r = codex.run("t-1", "nvidia/minimaxai/minimax-m3.1-flash", "Audita", "", {}, {})
    assert r["ok"] is True and r["recibo"].startswith("codex:t-1:")
    assert capturado["args"][capturado["args"].index("-m") + 1] == "nvidia/minimaxai/minimax-m3.1-flash"
    assert "127.0.0.1:7870/v1" in str(capturado["args"])
    assert capturado["env"]["RIU_AGENTE_LLM_KEY"] == "credencial-ficticia-puente"
    assert "CLAVE-PROVEEDOR-NO-ENVIAR" not in str(capturado["args"])
    assert "CLAVE-PROVEEDOR-NO-ENVIAR" not in str(capturado["env"])


def test_codex_rechaza_url_no_http(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BASE_URL", "file:///etc")
    monkeypatch.setattr(_comun, "preparar", lambda *a: {
        "directorio": str(tmp_path), "escritura": False, "prompt": "Analiza", "tarea_id": "t-2"})
    monkeypatch.setattr(_comun, "binario", lambda *a: "/usr/bin/codex")
    monkeypatch.setattr(_comun, "endpoint_modelo", lambda *a: {
        "base_url": "https://api.groq.com/openai/v1", "api_key": "x", "modelo": "modelo"})
    r = codex.run("t-2", "nvidia/minimaxai/minimax-m3.1-flash", "Analiza", "", {}, {})
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_CONFIGURADO"
