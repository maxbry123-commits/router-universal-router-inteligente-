"""Tests contractuales del ConectorGitLab v6."""
from __future__ import annotations

import pytest

from red.conector_gitlab import ConectorGitLab
from red.connector_registry import get_connector_class


def test_gitlab_project_path_encoded() -> None:
    connector = ConectorGitLab("gitlab", "grupo/proyecto")
    assert connector._project_path() == "grupo%2Fproyecto"


def test_gitlab_fails_closed_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)
    connector = ConectorGitLab("gitlab", "grupo/proyecto")
    with pytest.raises(RuntimeError, match="env_faltante:GITLAB_TOKEN"):
        connector._headers()


@pytest.mark.asyncio
async def test_gitlab_rejects_unknown_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITLAB_TOKEN", "dummy")
    connector = ConectorGitLab("gitlab", "grupo/proyecto")
    result = await connector.enviar({"_accion": "inventada"})
    assert result == {"status": "FAIL", "error": "accion_no_soportada:inventada"}


def test_gitlab_is_wired_in_registry() -> None:
    assert get_connector_class("gitlab") is ConectorGitLab


def test_registry_fails_closed_for_unknown_kind() -> None:
    with pytest.raises(ValueError, match="conector_no_registrado:desconocido"):
        get_connector_class("desconocido")
