"""Aislamiento: ninguna prueba debe depender de lo que haya instalado en agentes/runtime/ de la maquina que las corre.
Por defecto RIU_AGENTES_RUNTIME apunta a un directorio vacio; las pruebas de runtime (test_adaptadores_runtime.py) lo reemplazan a proposito."""
import pytest


@pytest.fixture(autouse=True)
def _runtime_vacio(monkeypatch, tmp_path_factory):
    monkeypatch.setenv("RIU_AGENTES_RUNTIME", str(tmp_path_factory.mktemp("runtime-vacio")))
