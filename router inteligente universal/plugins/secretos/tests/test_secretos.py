"""Tests del plugin secretos: cifrado formato banco, nunca valor en claro por HTTP, persistencia SQLite + espejo bucket, restauracion."""
import base64
import hashlib
import json
import time

import pytest

from plugins.secretos import plugin as S


class FakeSQLite:
    def __init__(self):
        self.rows = []

    def save(self, scope, key, data):
        self.rows.append({"id": len(self.rows) + 1, "scope": scope, "key": key, "data": json.loads(json.dumps(data))})
        return {"id": len(self.rows)}

    def search(self, scope, q, k=10):
        out = [r for r in reversed(self.rows) if r["scope"] == scope and (q in r["key"] or q in json.dumps(r["data"]))]
        return out[:k]


class FakeBucket:
    def __init__(self):
        self.files = {}

    def __call__(self, accion, p):
        if accion == "write":
            self.files[p["path"]] = p["content"]
            return {"status": "ok"}
        if accion == "read":
            if p["path"] not in self.files:
                return {"status": "error", "error": "no existe"}
            return {"status": "ok", "content": self.files[p["path"]]}
        return {"status": "error"}


VALOR = "gsk_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("FICHA_CLAVE_BANCO", "clave-de-prueba-banco")
    monkeypatch.delenv("RIU_SECRETOS_PIN", raising=False)
    monkeypatch.delenv("RIU_MCP_TOKEN", raising=False)
    mem, bucket = FakeSQLite(), FakeBucket()
    S.set_backend(mem, bucket)
    yield mem, bucket
    S.set_backend(None, None)


def _espera_espejo(bucket, texto=None, t=3.0):
    fin = time.time() + t
    while time.time() < fin:
        c = bucket.files.get(S.MIRROR)
        if c and (texto is None or texto in c):
            return c
        time.sleep(0.02)
    return bucket.files.get(S.MIRROR)


def test_guardar_listar_nunca_en_claro(env):
    mem, bucket = env
    r = S.handle("guardar", {"nombre": "groq-1", "valor": VALOR, "proveedor": "groq"})
    assert r["ok"] and r["secreto"]["mascara"] == "gsk…6789"
    todo = json.dumps([S.handle("listar"), S.handle("status"), r])
    assert VALOR not in todo
    assert VALOR not in json.dumps(mem.rows)  # SQLite solo guarda el sello cifrado
    espejo = _espera_espejo(bucket, "groq-1")
    assert espejo and VALOR not in espejo
    assert S.obtener("groq-1") == VALOR
    assert S.por_proveedor("groq") == [VALOR]


def test_formato_banco_unico(env):
    """El sello se abre con la misma formula de vault_hook/_qwen_conf (FICHA-SELLO-1, scrypt de FICHA_CLAVE_BANCO, AES-GCM aad=cabecera)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    S.handle("guardar", {"nombre": "x", "valor": "hola-mundo-123"})
    b = base64.b64decode(S._vigentes()["x"]["sello"])
    cab = b"FICHA-SELLO-1"; k = len(cab)
    ll = hashlib.scrypt(b"clave-de-prueba-banco", salt=b[k:k + 16], n=2 ** 15, r=8, p=1, dklen=32, maxmem=2 ** 26)
    assert AESGCM(ll).decrypt(b[k + 16:k + 28], b[k + 28:], cab).decode() == "hola-mundo-123"


def test_rotar_y_borrar(env):
    S.handle("guardar", {"nombre": "gh", "valor": "uno-uno-uno-uno"})
    r = S.handle("guardar", {"nombre": "gh", "valor": "dos-dos-dos-dos"})
    assert r["rotado"] and S.obtener("gh") == "dos-dos-dos-dos"
    assert S.handle("borrar", {"nombre": "gh"})["ok"]
    assert S.obtener("gh") is None and S.handle("listar")["secretos"] == []
    assert S.handle("borrar", {"nombre": "gh"})["error"] == "NO_EXISTE"


def test_validaciones_y_sin_clave(env, monkeypatch):
    assert S.handle("guardar", {"nombre": "../x", "valor": "v"})["error"] == "NOMBRE_INVALIDO"
    assert S.handle("guardar", {"nombre": "ok", "valor": ""})["error"] == "VALOR_INVALIDO"
    assert S.handle("guardar", {"nombre": "ok", "valor": "v", "proveedor": "A B"})["error"] == "PROVEEDOR_INVALIDO"
    monkeypatch.delenv("FICHA_CLAVE_BANCO")
    monkeypatch.delenv("RIU_VAULT_PASSPHRASE", raising=False)
    assert S.handle("guardar", {"nombre": "ok", "valor": "v"})["error"] == "SIN_CLAVE_DEL_BANCO_EN_EL_ROUTER"
    assert S.handle("obtener", {"nombre": "ok"})["error"] == "ACCION_DESCONOCIDA"  # no hay accion HTTP que devuelva el valor


def test_reinicio_sin_sqlite_restaura_del_bucket(env):
    mem, bucket = env
    S.handle("guardar", {"nombre": "nv-1", "valor": "nvapi-xxxxxxxxxxxxxxxx", "proveedor": "nvidia"})
    S.handle("guardar", {"nombre": "borrado", "valor": "zzzzzzzzzzzz"})
    S.handle("borrar", {"nombre": "borrado"})
    _espera_espejo(bucket, '"borrado": true')
    S.espejo_bucket(sincrono=True)
    nuevo = FakeSQLite()  # el Space reinicio y el SQLite llego vacio
    S.set_backend(nuevo, bucket)
    r = S.handle("restaurar")
    assert r["ok"] and r["importados"] >= 1
    assert S.obtener("nv-1") == "nvapi-xxxxxxxxxxxxxxxx" and S.obtener("borrado") is None


def test_espejo_no_borra_secretos_de_otra_copia(env):
    mem, bucket = env
    S.handle("guardar", {"nombre": "a", "valor": "aaaaaaaaaaaa"})
    S.espejo_bucket(sincrono=True)
    S.set_backend(FakeSQLite(), bucket)  # otra copia del Router, SQLite vacio y antes de restaurar
    S._restaurado["hecho"] = True  # simula que la restauracion de fondo aun no corrio
    S.handle("guardar", {"nombre": "b", "valor": "bbbbbbbbbbbb"})
    S.espejo_bucket(sincrono=True)
    doc = json.loads(bucket.files[S.MIRROR])
    assert set(doc["secretos"]) == {"a", "b"}
    assert S.obtener("a") == "aaaaaaaaaaaa"


def test_pin_opcional(env, monkeypatch):
    monkeypatch.setenv("RIU_SECRETOS_PIN", "4321")
    assert S.handle("guardar", {"nombre": "p", "valor": "vvvvvvvv"})["error"] == "PIN_REQUERIDO"
    assert S.handle("guardar", {"nombre": "p", "valor": "vvvvvvvv", "pin": "4321"})["ok"]
    assert S.handle("listar")["ok"]  # leer mascaras no pide PIN


def test_token_mcp(env, monkeypatch):
    r = S.handle("mcp_token_nuevo")
    assert r["ok"] and r["token"].startswith("riu-mcp-") and r["una_vez"]
    assert S.verificar_token_mcp(r["token"]) and not S.verificar_token_mcp("otro") and not S.verificar_token_mcp(None)
    assert r["token"] not in json.dumps(S.handle("listar"))
    monkeypatch.setenv("RIU_MCP_TOKEN", "env-token")
    assert S.verificar_token_mcp("env-token")


def test_vault_hook_suma_secretos_al_pool(env):
    from integration.chat_mvp import vault_hook
    S.handle("guardar", {"nombre": "groq-9", "valor": VALOR, "proveedor": "groq"})
    assert VALOR in vault_hook.provider_keys("groq")
    assert VALOR not in vault_hook.provider_keys("nvidia")
