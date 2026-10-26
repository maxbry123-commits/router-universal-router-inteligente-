import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from red.connector_registry import get_connector_class
from red.conectores import ConectorVPS


def test_registry_resuelve_vps():
    assert get_connector_class("vps") is ConectorVPS


@pytest.mark.asyncio
async def test_vps_falla_cerrado_en_comando_no_permitido():
    conector = ConectorVPS("vps-test", "https://127.0.0.1:9")
    result = await conector.enviar({"_cmd": "rm_everything"})
    assert result["status"] == "FAIL"
    assert result["error"] == "cmd_no_permitido:rm_everything"


def test_vps_lista_permitida_es_contractual():
    conector = ConectorVPS("vps-test", "https://127.0.0.1:9")
    assert conector.comandos_permitidos == (
        "status", "deploy", "restart", "logs", "run_script"
    )
