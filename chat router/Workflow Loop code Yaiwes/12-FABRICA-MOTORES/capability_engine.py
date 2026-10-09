"""Capability Engine (docs 14-16): registro obligatorio, compatibilidad, recetas.

Regla "ningún componente invisible": si existen carpetas de componentes en
disco sin registrar, el motor falla.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from engine import Engine, ok, fail


@dataclass
class Component:
    id: str
    provides: list[str]
    requires: list[str] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    runtime: str = "web"


class CapabilityEngine(Engine):
    id = "ui.capability"
    capabilities = ["ui.capability"]

    def __init__(self, components: list[dict] | None = None,
                 components_dir: str | None = None):
        self.registry: dict[str, Component] = {}
        for c in components or []:
            self.register(c)
        self.components_dir = components_dir

    def register(self, data: dict) -> Component:
        comp = Component(
            id=data["id"],
            provides=list(data.get("provides", [])),
            requires=list(data.get("requires", [])),
            compatible_with=list(data.get("compatible_with", [])),
            conflicts_with=list(data.get("conflicts_with", [])),
            runtime=data.get("runtime", "web"),
        )
        self.registry[comp.id] = comp
        return comp

    def check_invisible(self) -> list[str]:
        """Carpetas de componentes en disco sin registrar."""
        if not self.components_dir or not os.path.isdir(self.components_dir):
            return []
        invisibles = []
        for entry in sorted(os.listdir(self.components_dir)):
            full = os.path.join(self.components_dir, entry)
            if os.path.isdir(full) and not entry.startswith("."):
                if entry not in self.registry:
                    invisibles.append(entry)
        return invisibles

    def candidates_for(self, capability: str) -> list[Component]:
        return [c for c in self.registry.values() if capability in c.provides]

    def _pair_conflict(self, a: Component, b: Component) -> str | None:
        if b.id in a.conflicts_with or a.id in b.conflicts_with:
            return f"{a.id} en conflicto con {b.id}"
        if a.compatible_with and b.id not in a.compatible_with:
            return f"{a.id} no declara compatibilidad con {b.id}"
        if b.compatible_with and a.id not in b.compatible_with:
            return f"{b.id} no declara compatibilidad con {a.id}"
        return None

    def compose(self, objective_capabilities: list[str]) -> dict:
        """Devuelve composición compatible + auditoría de descarte."""
        chosen: list[Component] = []
        audit: list[dict] = []
        for cap in objective_capabilities:
            cands = self.candidates_for(cap)
            if not cands:
                audit.append({"capability": cap, "chosen": None,
                              "reason": "sin candidatos registrados"})
                return fail(f"capacidad sin candidatos: {cap}", audit=audit)
            picked = None
            for cand in cands:
                conflict = None
                for prev in chosen:
                    conflict = self._pair_conflict(prev, cand)
                    if conflict:
                        break
                missing = [r for r in cand.requires
                           if not any(r in p.provides for p in chosen)
                           and not any(r in c.provides for c in cands)]
                if conflict:
                    audit.append({"capability": cap, "chosen": None,
                                  "discarded": cand.id, "reason": conflict})
                    continue
                if missing:
                    audit.append({"capability": cap, "chosen": None,
                                  "discarded": cand.id,
                                  "reason": f"requires no satisfechos: {missing}"})
                    continue
                picked = cand
                break
            if picked is None:
                return fail(f"ningún candidato compatible para: {cap}",
                            audit=audit)
            chosen.append(picked)
            audit.append({
                "capability": cap,
                "chosen": picked.id,
                "discarded": [c.id for c in cands if c.id != picked.id],
                "reason": "compatible y requires satisfechos",
            })
        return ok(
            [c.id for c in chosen],
            audit=audit,
            runtimes=sorted({c.runtime for c in chosen}),
        )

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        invisibles = self.check_invisible()
        if invisibles:
            return fail(f"componentes invisibles sin registrar: {invisibles}")
        return self.compose(task.get("objective", []))
