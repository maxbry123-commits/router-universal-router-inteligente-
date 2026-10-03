"""Pruebas: los clientes de prueba actuan como el Director (mandan su clave de prueba), asi las rutas protegidas por el
candado se siguen probando de punta a punta. El candado mismo se prueba en test_conexion_universal.py (sin esta ayuda)."""
from __future__ import annotations

import pytest

CLAVE_PRUEBAS = "clave-director-de-pruebas"


@pytest.fixture(autouse=True)
def _director_en_pruebas(monkeypatch, request):
    if request.node.fspath.basename == "test_conexion_universal.py":
        return
    from integration.chat_mvp import director

    monkeypatch.setenv("RIU_DIRECTOR_KEY_HASH", director.make_hash(CLAVE_PRUEBAS, iterations=1000))
    from starlette.testclient import TestClient

    original = TestClient.__init__

    def init(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("X-Director-Key", CLAVE_PRUEBAS)
        original(self, *args, headers=headers, **kwargs)

    monkeypatch.setattr(TestClient, "__init__", init)
