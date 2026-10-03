"""Conexion universal (Director 2026-10-03): candado del Director, tokens por agente, secciones (fichas), ventana. Sin red."""
from __future__ import annotations

import asyncio
import json

import pytest

from integration.chat_mvp import candado, director, rutas, secciones, tokens


def _asgi(app, method, path, headers=None):
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        sent.append(msg)

    scope = {"type": "http", "method": method, "path": path,
             "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]}
    asyncio.run(app(scope, receive, send))
    return sent, scope


async def _ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def _status(sent):
    return sent[0]["status"]


@pytest.fixture()
def clave(monkeypatch):
    monkeypatch.setenv("RIU_DIRECTOR_KEY_HASH", director.make_hash("clave-de-prueba", iterations=1000))
    director._fails.clear()  # noqa: SLF001
    yield "clave-de-prueba"
    director._fails.clear()  # noqa: SLF001


@pytest.fixture()
def registro(monkeypatch):
    monkeypatch.setattr(tokens.REGISTRO, "data", {})
    monkeypatch.setattr(tokens.REGISTRO, "loaded_at", 1.0)
    monkeypatch.setattr(tokens.REGISTRO, "cargar", lambda: None)
    monkeypatch.setattr(tokens.REGISTRO, "guardar", lambda: None)
    tokens.REGISTRO._ventanas.clear()  # noqa: SLF001
    return tokens.REGISTRO


def _token(reg, nombre, permisos, rpm=600, activo=True):
    tok = tokens.PREFIX + nombre.replace("/", "-")
    reg.data[tokens.huella(tok)] = {"nombre": nombre, "instancia": nombre.split("/")[0], "permisos": permisos,
                                    "limite_rpm": rpm, "activo": activo}
    return tok


def test_director_hash_verifica_y_bloquea(clave):
    assert director.verify(clave)
    assert not director.verify("otra")
    for _ in range(director.MAX_FAILS):
        director.verify("mala")
    assert director.locked() and not director.verify(clave)  # bloqueado aunque la clave sea buena


def test_director_sin_hash_falla_cerrado(monkeypatch):
    monkeypatch.delenv("RIU_DIRECTOR_KEY_HASH", raising=False)
    assert not director.verify("cualquiera")


@pytest.mark.parametrize("method,path", [("POST", "/vault/credentials"), ("POST", "/tokens"), ("GET", "/tokens"),
                                         ("POST", "/hf/hardware"), ("POST", "/control/pause-router"), ("DELETE", "/chat/agents/x"),
                                         ("POST", "/secciones"), ("DELETE", "/secciones/x"), ("POST", "/chat/github/commit")])
def test_candado_exige_clave_del_director(method, path, clave, registro):
    app = candado.Candado(_ok_app)
    assert _status(_asgi(app, method, path)[0]) == 403
    assert _status(_asgi(app, method, path, {"X-Director-Key": clave})[0]) == 200


@pytest.mark.parametrize("method,path", [("GET", "/vault/status"), ("POST", "/memoria/save"), ("POST", "/control/hf/invoke"),
                                         ("DELETE", "/espacio/mio.txt"), ("GET", "/secciones"), ("POST", "/v1/router/chat/completions")])
def test_candado_deja_pasar_el_uso(method, path, clave, registro):
    tok = _token(registro, "inst/a", list(tokens.PERMISOS_BASE))
    assert _status(_asgi(candado.Candado(_ok_app), method, path, {"Authorization": "Bearer " + tok})[0]) == 200


def test_token_sin_permiso_y_limite_por_minuto(clave, registro):
    tok = _token(registro, "inst/b", ["chat"], rpm=2)
    app = candado.Candado(_ok_app)
    h = {"X-API-Key": tok}
    assert _status(_asgi(app, "POST", "/hf/compute/run", h)[0]) == 403  # sin permiso computo
    registro._ventanas.clear()  # noqa: SLF001
    assert _status(_asgi(app, "POST", "/v1/router/chat/completions", h)[0]) == 200
    assert _status(_asgi(app, "POST", "/v1/router/chat/completions", h)[0]) == 200
    assert _status(_asgi(app, "POST", "/v1/router/chat/completions", h)[0]) == 429  # su limite, no el de los demas
    otro = _token(registro, "inst/c", ["chat"], rpm=2)
    assert _status(_asgi(app, "POST", "/v1/router/chat/completions", {"X-API-Key": otro})[0]) == 200


def test_token_apagado_no_entra_y_dueno_en_scope(registro):
    tok = _token(registro, "inst/d", ["chat"], activo=False)
    assert registro.buscar(tok) is None
    tok2 = _token(registro, "inst/e", ["chat", "memoria"])
    sent, scope = _asgi(candado.Candado(_ok_app), "POST", "/memoria/save", {"X-API-Key": tok2})
    assert _status(sent) == 200 and scope["state"]["riu_owner"] == "tok:inst/e"


def test_auth_acepta_tokens_del_banco(registro):
    from integration.huggingface.api_key_auth import authenticate_api_key

    tok = _token(registro, "inst/f", ["chat"])
    assert authenticate_api_key(tok) == "tok:inst/f"
    with pytest.raises(RuntimeError):
        authenticate_api_key(tokens.PREFIX + "no-existe")


def test_plantilla_y_conversion_de_ficha():
    raw = json.loads(json.dumps(secciones.PLANTILLA))
    f = secciones.convertir(raw)
    assert f.mode == "queue" and len(f.members) == 1 and f.members[0].template == "{input}"
    raw["pasos"] = [{"nombre": n, "modelo": "auto", "system_prompt": f"eres {n}", "instruccion": "{input}"}
                    for n in ("entrada", "arquitectura", "codigo", "verifica", "decide", "salida")]
    assert len(secciones.convertir(raw).members) == 6
    with pytest.raises(ValueError):
        secciones.convertir({**raw, "pasos": []})
    with pytest.raises(ValueError):
        secciones.convertir({**raw, "modo": "magia"})


def test_rutas_una_sola_raiz():
    for sub in (rutas.MEMORIA, rutas.BANCO, rutas.LABORATORIO, rutas.CONTROL, rutas.CODIGO, rutas.FICHAS, rutas.ESPACIOS, rutas.VENTANA):
        assert sub.startswith("router-inteligente-universal/")
    assert rutas.VENTANA.endswith("Ventana status router inteligente universal")
    assert tokens._ruta_espacio("tok:a/b", "x/y.md").endswith("router-inteligente-universal/espacios/tok_a_b/x/y.md")  # noqa: SLF001
    with pytest.raises(Exception):
        tokens._ruta_espacio("tok:a/b", "../otro/secreto")  # noqa: SLF001
