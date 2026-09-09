"""Deterministic contract tests for ConectorHuggingFace v6."""
from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "red" / "conectores.py"
spec = importlib.util.spec_from_file_location("riu_conectores", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
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


async def test_conector_huggingface_model_info_routes_without_secret() -> None:
    connector, fake = _connector_with_fake()
    result = await connector.enviar(
        {"_accion": "model_info", "repo_id": "owner/model"}
    )
    assert result["status"] == "DONE"
    assert fake.payloads == [{
        "_ruta": "/models/owner/model",
        "_metodo": "GET",
        "repo_id": "owner/model",
    }]
    assert "HF_TOKEN" not in repr(fake.payloads)


async def test_conector_huggingface_dataset_and_spaces_routes() -> None:
    connector, fake = _connector_with_fake()
    await connector.enviar(
        {"_accion": "dataset_info", "repo_id": "owner/data"}
    )
    await connector.enviar({"_accion": "list_spaces"})
    assert fake.payloads[0]["_ruta"] == "/datasets/owner/data"
    assert fake.payloads[0]["_metodo"] == "GET"
    assert fake.payloads[1]["_ruta"] == "/spaces"
    assert fake.payloads[1]["_metodo"] == "GET"


async def test_conector_huggingface_sondear_delegates() -> None:
    connector, _ = _connector_with_fake()
    assert await connector.sondear() is True
