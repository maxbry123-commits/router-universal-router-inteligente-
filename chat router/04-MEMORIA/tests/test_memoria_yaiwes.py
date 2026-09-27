from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ROUTER_ROOT = ROOT / "router inteligente universal"
MEMORY_ROOT = ROOT / "04-MEMORIA"
if str(ROUTER_ROOT) not in sys.path:
    sys.path.insert(0, str(ROUTER_ROOT))
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

from integration.chat_mvp.store import Store  # noqa: E402
from memoria_yaiwes import build_memory  # noqa: E402


def test_m0_inventory_has_thirteen_verified_components():
    inventory = json.loads((ROOT / "03-ESTADO" / "MEMORIA-INVENTARIO.json").read_text(encoding="utf-8"))
    assert len(inventory["components"]) == 13
    assert {item["name"] for item in inventory["components"]} >= {"sqlite", "state-hub", "graphiti", "memanto", "graphify", "agentdb", "postgresql", "redis", "hf-storage-bucket"}
    assert next(item for item in inventory["components"] if item["name"] == "agentdb")["source_status"] == "GAP_ABSENT"


def test_m2_memory_survives_restart_and_m4_graph_search(tmp_path):
    store = Store(tmp_path)
    memory = build_memory(store)
    saved = memory.save("agente", "preferencia", {"idioma": "es"})
    assert saved["status"] == "SAVED"
    assert memory.load("agente", "preferencia")[0]["data"] == {"idioma": "es"}
    assert memory.search("agente", "preferencia")["graph"]
    store.close()

    reopened = Store(tmp_path)
    restored = build_memory(reopened)
    assert restored.load("agente", "preferencia")[0]["data"] == {"idioma": "es"}
    assert restored.health()["adapters"]["sqlite"]["records"] == 1
    reopened.close()


def test_m1_health_reports_gaps_without_claiming_live_services(tmp_path):
    memory = build_memory(Store(tmp_path))
    health = memory.health()
    assert health["fallback"] == "sqlite"
    assert health["adapters"]["sqlite"]["status"] == "CONNECTED"
    assert health["adapters"]["falkordb"]["runtime_status"] == "GAP"
    assert health["adapters"]["memanto"]["source_status"] == "PRESENT"


def test_m7_loader_mounts_health_and_save_routes(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from integration.chat_mvp import app as chat_app
    from integration.chat_mvp import router

    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"m-key": "agent-m"}')
    router.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    headers = {"X-API-Key": "m-key"}
    health = client.get("/memoria/health", headers=headers)
    assert health.status_code == 200 and health.json()["fallback"] == "sqlite"
    saved = client.post("/memoria/save", headers=headers, json={"scope": "chat", "key": "turno-1", "data": {"ok": True}})
    assert saved.status_code == 200
    loaded = client.get("/memoria/load", headers=headers, params={"scope": "chat", "key": "turno-1"})
    assert loaded.status_code == 200 and loaded.json()["records"][0]["data"] == {"ok": True}
    router.set_store(None)
