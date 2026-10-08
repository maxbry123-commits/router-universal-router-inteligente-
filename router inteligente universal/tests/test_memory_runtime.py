from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp.memory_runtime import memory, scope_for
from integration.chat_mvp.router import set_store
from integration.chat_mvp.store import Store


def test_scope_for_is_namespaced_and_bounded() -> None:
    assert scope_for("chat-ui", "chat:abc") == "chat-ui:chat:abc"
    assert scope_for("chat-ui", "chat-ui:chat:abc") == "chat-ui:chat:abc"
    assert len(scope_for("owner", "x" * 200)) == 80


def test_memory_runtime_save_search_load(tmp_path: Path) -> None:
    store = Store(tmp_path / "riu-data")
    set_store(store)
    try:
        mem = memory(store)
        scope = scope_for("chat-ui", "chat:test-session")
        payload = {"modelo": "deepseek-test", "pregunta": "hola", "respuesta": "mundo"}

        saved = mem.save(scope, "turno-1", payload)
        assert saved["status"] == "SAVED"

        found = mem.search(scope, "hola", 6)
        sqlite_rows = found.get("sqlite", [])
        assert sqlite_rows
        assert sqlite_rows[0]["data"]["respuesta"] == "mundo"

        loaded = mem.load(scope, "turno-1")
        assert loaded
        assert loaded[0]["data"] == payload
    finally:
        set_store(None)
        store.close()
