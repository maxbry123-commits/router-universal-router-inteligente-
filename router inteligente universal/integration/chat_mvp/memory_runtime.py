"""Shared memory facade for chat turns and the memory HTTP endpoints."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

from .store import Store

PACKAGE_DIR = Path(__file__).resolve().parents[3] / "chat router" / "04-MEMORIA" / "memoria_yaiwes"


class Memory(Protocol):
    def health(self) -> dict: ...

    def save(self, scope: str, key: str, data: object) -> dict: ...

    def load(self, scope: str, key: str) -> list[dict]: ...

    def search(self, scope: str, query: str, k: int = 10) -> dict: ...


_facade: Memory | None = None
_store: Store | None = None


def scope_for(owner: str, scope: str) -> str:
    return f"owner:{owner}:{scope}"


def memory(store: Store) -> Memory:
    global _facade, _store
    if _facade is None or _store is not store:
        spec = importlib.util.spec_from_file_location(
            "memoria_yaiwes", PACKAGE_DIR / "__init__.py",
            submodule_search_locations=[str(PACKAGE_DIR)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("MEMORIA_PACKAGE_LOAD_FAILED")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _facade = cast(Memory, module.build_memory(store))
        _store = store
    return _facade
