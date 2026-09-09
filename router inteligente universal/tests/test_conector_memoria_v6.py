from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from red.connector_registry import get_connector_class
from red.conectores import ConectorMemoria


class FakeEstado:
    def __init__(self):
        self.data = {"router/status": {"ok": True}}
        self.commits = []

    def leer(self, path):
        return self.data[path]

    def commit(self, proposals, actor="red"):
        self.commits.append((proposals, actor))
        return "commit-test-001"

    def snapshot(self):
        return {"items": len(self.data)}

    def verificar_hash_chain(self):
        return True


def test_registry_resolves_existing_memoria_connector():
    assert get_connector_class("memoria") is ConectorMemoria


def test_memoria_read_commit_snapshot_contract():
    async def run():
        estado = FakeEstado()
        conector = ConectorMemoria("memoria-test", estado)

        read = await conector.enviar({"_op": "leer", "path": "router/status"})
        assert read == {"status": "DONE", "output": {"ok": True}}

        commit = await conector.enviar({
            "_op": "commit",
            "proposals": [{"path": "x", "value": 1}],
            "actor": "test",
        })
        assert commit == {"status": "DONE", "output": {"commit": "commit-test-001"}}
        assert estado.commits == [([{"path": "x", "value": 1}], "test")]

        snapshot = await conector.enviar({"_op": "snapshot"})
        assert snapshot == {"status": "DONE", "output": {"items": 1}}
        assert await conector.sondear() is True

    asyncio.run(run())


def test_memoria_unknown_operation_fails_closed():
    async def run():
        conector = ConectorMemoria("memoria-test", FakeEstado())
        result = await conector.enviar({"_op": "desconocida"})
        assert result == {"status": "FAIL", "error": "op_desconocida:desconocida"}

    asyncio.run(run())
