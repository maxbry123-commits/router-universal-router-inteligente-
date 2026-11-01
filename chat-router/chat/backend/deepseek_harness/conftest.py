"""Aislamiento (mismo criterio que agentes/adaptadores/tests/conftest.py): ninguna prueba depende de lo que haya instalado en agentes/runtime/ de la maquina que las corre.
Con un runtime real instalado, `codex` aparece como binario presente y pasa de NO INSTALADO a NO CONFIGURADO (falta RIU_CODEX_BASE_URL): la semantica es correcta, la prueba debe aislarse."""
import pytest


@pytest.fixture(autouse=True)
def _runtime_vacio(monkeypatch, tmp_path_factory):
    monkeypatch.setenv("RIU_AGENTES_RUNTIME", str(tmp_path_factory.mktemp("runtime-vacio")))
