"""Deterministic contract tests for ConectorHuggingFace v6."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "red" / "conectores.py"
spec = importlib.util.spec_from_file_location("riu_conectores", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules["riu_conectores"] = module
spec.loader.exec_module(module)
ConectorHuggingFace = module.ConectorHuggingFace


class FakeHTTP:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    async def enviar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"status": "DONE", "output": payload}

    async def sondear(self) -> bool:
        return True


def _connector_with_fake() -> tuple[ConectorHuggingFace, FakeHTTP]:
    connector = ConectorHuggingFace("hf-test")
    fake = FakeHTTP()
    connector._api = lambda: fake
    return connector, fake


def test_conector_huggingface_model_info_routes_without_secret() -> None:
    connector, fake = _connector_with_fake()
    result = asyncio.run(connector.enviar(
        {"_accion": "model_info", "repo_id": "owner/model"}
    ))
    assert result["status"] == "DONE"
    assert fake.payloads == [{
        "_ruta": "/models/owner/model",
        "_metodo": "GET",
        "repo_id": "owner/model",
    }]
    assert "HF_TOKEN" not in repr(fake.payloads)


def test_conector_huggingface_dataset_and_spaces_routes() -> None:
    connector, fake = _connector_with_fake()
    asyncio.run(connector.enviar(
        {"_accion": "dataset_info", "repo_id": "owner/data"}
    ))
    asyncio.run(connector.enviar({"_accion": "list_spaces"}))
    assert fake.payloads[0]["_ruta"] == "/datasets/owner/data"
    assert fake.payloads[0]["_metodo"] == "GET"
    assert fake.payloads[1]["_ruta"] == "/spaces"
    assert fake.payloads[1]["_metodo"] == "GET"


def test_conector_huggingface_sondear_delegates() -> None:
    connector, _ = _connector_with_fake()
    assert asyncio.run(connector.sondear()) is True
