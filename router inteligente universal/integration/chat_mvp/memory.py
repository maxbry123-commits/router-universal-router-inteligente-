"""Memory adapters for the chat runtime.

The local Store is the writable source of truth. The YAIWES dataset plugin is
mounted as a read-only recall source; it never receives conversation writes.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping


_ROOT = Path(__file__).resolve().parents[3]
_PLUGIN = _ROOT / "dataset Yaiwes" / "plugin" / "yaiwes_dataset_plugin.py"


class DatasetMemory:
    """Read-only bridge to the checked-in YAIWES dataset plugin."""

    def __init__(self, plugin_path: str | Path = _PLUGIN) -> None:
        self.plugin_path = Path(plugin_path)
        self._plugin: Any = None

    def _load(self) -> Any:
        if self._plugin is None:
            if not self.plugin_path.is_file():
                raise FileNotFoundError("YAIWES_DATASET_PLUGIN_NOT_FOUND")
            spec = importlib.util.spec_from_file_location("riu_yaiwes_dataset_plugin", self.plugin_path)
            if spec is None or spec.loader is None:
                raise ImportError("YAIWES_DATASET_PLUGIN_LOAD_FAILED")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self._plugin = module.DatasetYaiwesPlugin()
        return self._plugin

    def health(self) -> dict[str, Any]:
        try:
            health = self._load().health()
            return {"configured": True, **health}
        except (FileNotFoundError, ImportError, OSError, ValueError, KeyError) as exc:
            return {"configured": False, "ok": False, "mode": "unavailable", "error": str(exc)}

    def recall(self, query: str, limits: Mapping[str, int] | None = None) -> dict[str, Any]:
        query = " ".join(str(query or "").split())
        if not query:
            return {"query": "", "routes": {}, "records": [], "source": "yaiwes-dataset", "read_only": True}
        try:
            routes = self._load().route_and_retrieve(query, parallel_width=1, limits=limits)
            records = [record for rows in routes.values() for record in rows]
            return {"query": query, "routes": routes, "records": records,
                    "source": "yaiwes-dataset", "read_only": True}
        except (FileNotFoundError, ImportError, OSError, ValueError, KeyError) as exc:
            return {"query": query, "routes": {}, "records": [], "source": "yaiwes-dataset",
                    "read_only": True, "available": False, "error": str(exc)}


DATASET_MEMORY = DatasetMemory()
