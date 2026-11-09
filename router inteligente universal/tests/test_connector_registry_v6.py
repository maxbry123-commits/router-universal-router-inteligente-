import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from red.connector_registry import CONNECTOR_REGISTRY, get_connector_class
from red.conector_gitlab import ConectorGitLab
from red.conector_mcp_app import ConectorMCPApp
from red.conectores import (
    ConectorDB,
    ConectorGitHub,
    ConectorHuggingFace,
    ConectorHTTP,
    ConectorInterno,
    ConectorMCP,
    ConectorMemoria,
    ConectorVPS,
    ConectorWebhook,
)

EXPECTED = {
    "http": ConectorHTTP,
    "mcp": ConectorMCP,
    "mcp_app": ConectorMCPApp,
    "github": ConectorGitHub,
    "huggingface": ConectorHuggingFace,
    "db": ConectorDB,
    "gitlab": ConectorGitLab,
    "vps": ConectorVPS,
    "memoria": ConectorMemoria,
    "interno": ConectorInterno,
    "webhook": ConectorWebhook,
}


def test_registry_es_explicito_y_sin_duplicados():
    assert CONNECTOR_REGISTRY == EXPECTED
    assert len(CONNECTOR_REGISTRY) == len(set(CONNECTOR_REGISTRY))


@pytest.mark.parametrize("kind, expected", EXPECTED.items())
def test_registry_resuelve_cada_adapter(kind, expected):
    assert get_connector_class(kind) is expected


def test_registry_falla_cerrado_para_kind_desconocido():
    with pytest.raises(ValueError, match=r"^conector_no_registrado:no-existe$"):
        get_connector_class("no-existe")
