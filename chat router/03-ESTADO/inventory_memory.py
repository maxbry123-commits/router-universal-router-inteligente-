"""Read-back de fuentes de memoria; no infiere conectividad por archivos."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "chat router/03-ESTADO/MEMORIA-INVENTARIO.json"
ADAPTERS = {
    "sqlite": "chat router/memoria/memoria_yaiwes/__init__.py",
    "state-hub": "chat router/03-ESTADO/checkpoint_guard.py",
    "graphiti": "chat router/memoria/memoria_yaiwes/__init__.py",
    "graphify": "chat router/memoria/memoria_yaiwes/__init__.py",
}


def inspect_sources(root: Path = ROOT, inventory: Path = INVENTORY) -> dict:
    components = json.loads(inventory.read_text(encoding="utf-8"))["components"]
    results = []
    for item in components:
        path = item["path"]
        source = (root / path).resolve() if path else None
        adapter_path = ADAPTERS.get(item["name"])
        adapter = (root / adapter_path).resolve() if adapter_path else None
        results.append({
            "name": item["name"],
            "source": "PRESENT" if source and source.is_relative_to(root.resolve()) and source.exists() else "MISSING",
            "adapter": "PRESENT" if adapter and adapter.is_file() else "NOT_INVENTORIED",
            "runtime": "NOT_VERIFIED_THIS_RUN",
            "operation": "NOT_VERIFIED_THIS_RUN",
            "readback": "NOT_VERIFIED_THIS_RUN",
            "restart": "NOT_VERIFIED_THIS_RUN",
        })
    return {"schema": "yaiwes.memory.source-readback/v1", "components": results}


if __name__ == "__main__":
    print(json.dumps(inspect_sources(), ensure_ascii=False, indent=2))
