"""Prueba real de endpoint ASGI local, sin proveedores externos ni tokens reales."""
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pasarela


def test_anonimo_no_alcanza_nvidia_ni_el_banco(monkeypatch):
    monkeypatch.setattr(pasarela, "MODO_BRIDGE", True)
    monkeypatch.setenv("RIU_API_KEY", "clave-solo-test-no-real")
    peticion = {"model": "claude-sonnet-4-5", "messages": [{"role": "user", "content": "hola"}]}
    with TestClient(pasarela.app) as cli:
        for headers in ({}, {"authorization": "Bearer equivocada"}, {"x-api-key": "equivocada"}):
            r = cli.post("/v1/messages", json=peticion, headers=headers)
            assert r.status_code == 401
            assert r.json()["error"]["type"] == "authentication_error"
            assert cli.post("/v1/messages/count_tokens", json=peticion, headers=headers).status_code == 401


def test_credencial_valida_envia_al_bridge_existente_sin_exponer_el_token(monkeypatch):
    clave = "clave-ficticia-test"
    modelo = "nvidia/minimaxai/minimax-m3.1-flash"
    upstream = "http://127.0.0.1:7870/v1/chat/completions"
    monkeypatch.setattr(pasarela, "MODO_BRIDGE", True)
    monkeypatch.setattr(pasarela, "UPSTREAM", upstream)
    monkeypatch.setenv("RIU_API_KEY", clave)
    monkeypatch.setenv("MODELO", modelo)
    llamadas = []

    class Respuesta:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"role": "assistant", "content": "respuesta prueba"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 2, "completion_tokens": 3}}

    class Cliente:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, *, headers, json):
            llamadas.append((url, headers, json))
            return Respuesta()

    monkeypatch.setattr(pasarela.httpx, "AsyncClient", Cliente)
    cuerpo = {"model": "claude-sonnet-4-5", "messages": [{"role": "user", "content": "hola"}], "max_tokens": 64}
    with TestClient(pasarela.app) as cli:
        r = cli.post("/v1/messages", json=cuerpo, headers={"authorization": "Bearer " + clave})
        cuenta = cli.post("/v1/messages/count_tokens", json=cuerpo, headers={"x-api-key": clave})
    assert r.status_code == 200, r.text
    assert r.json()["content"][0]["text"] == "respuesta prueba"
    assert cuenta.status_code == 200
    assert len(llamadas) == 1
    url, headers, enviada = llamadas[0]
    assert url == upstream
    assert headers.get("X-API-Key") == clave and "Authorization" not in headers
    assert enviada["model"] == modelo
    assert enviada["messages"][-1]["content"] == "hola"
    assert clave not in r.text


def test_sin_clave_en_servidor_no_autoriza_peticiones(monkeypatch):
    monkeypatch.setattr(pasarela, "MODO_BRIDGE", True)
    monkeypatch.delenv("RIU_API_KEY", raising=False)
    with TestClient(pasarela.app) as cli:
        r = cli.post("/v1/messages", json={}, headers={"authorization": "Bearer cualquiera"})
        assert r.status_code == 401
