"""Canvas Engine: modelo de página determinista, sin navegador."""
from __future__ import annotations

import copy

from engine import Engine, ok, fail


class CanvasEngine(Engine):
    id = "ui.canvas"
    capabilities = ["ui.canvas"]

    def __init__(self):
        self.page: dict | None = None

    def create_page(self, page_id: str, title: str = "") -> dict:
        self.page = {"id": page_id, "title": title, "sections": []}
        return self.page

    def _require_page(self) -> dict | None:
        return self.page

    def _find_section(self, section_id: str) -> dict | None:
        for s in self.page["sections"]:
            if s["id"] == section_id:
                return s
        return None

    def _find_component(self, component_id: str):
        for s in self.page["sections"]:
            for c in s["components"]:
                if c["id"] == component_id:
                    return s, c
        return None, None

    def add_section(self, section_id: str) -> dict:
        if self._require_page() is None:
            raise ValueError("página no creada")
        if self._find_section(section_id):
            raise ValueError(f"sección duplicada: {section_id}")
        section = {"id": section_id, "components": []}
        self.page["sections"].append(section)
        return section

    def add_component(self, section_id: str, component: dict) -> dict:
        section = self._find_section(section_id)
        if section is None:
            raise ValueError(f"sección no existe: {section_id}")
        if "id" not in component or "type" not in component:
            raise ValueError("componente requiere id y type")
        prev, _ = self._find_component(component["id"])
        if prev is not None:
            raise ValueError(f"componente duplicado: {component['id']}")
        comp = {
            "id": component["id"],
            "type": component["type"],
            "properties": dict(component.get("properties", {})),
            "action_id": component.get("action_id"),
        }
        section["components"].append(comp)
        return comp

    def move_component(self, component_id: str, target_section_id: str,
                       index: int | None = None) -> dict:
        src, comp = self._find_component(component_id)
        if comp is None:
            raise ValueError(f"componente no existe: {component_id}")
        dst = self._find_section(target_section_id)
        if dst is None:
            raise ValueError(f"sección destino no existe: {target_section_id}")
        src["components"].remove(comp)
        if index is None:
            dst["components"].append(comp)
        else:
            dst["components"].insert(index, comp)
        return comp

    def set_property(self, component_id: str, key: str, value) -> dict:
        _, comp = self._find_component(component_id)
        if comp is None:
            raise ValueError(f"componente no existe: {component_id}")
        comp["properties"][key] = value
        return comp

    def export_json(self) -> dict:
        if self.page is None:
            raise ValueError("página no creada")
        return copy.deepcopy(self.page)

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        ops = task.get("ops", [])
        try:
            for op in ops:
                name = op["op"]
                args = op.get("args", [])
                kwargs = op.get("kwargs", {})
                getattr(self, {
                    "createPage": "create_page",
                    "addSection": "add_section",
                    "addComponent": "add_component",
                    "moveComponent": "move_component",
                    "setProperty": "set_property",
                }[name])(*args, **kwargs)
            return ok(self.export_json())
        except (ValueError, KeyError) as exc:
            return fail(str(exc))
