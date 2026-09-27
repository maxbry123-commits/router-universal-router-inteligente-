"""QA Engine: comprobaciones deterministas del JSON de página.

- componentes interactivos con acción (ningún botón muerto)
- solapes de layout
- tamaños táctiles mínimos (44 px)
- breakpoints (mobile/tablet/desktop sin overflow)
"""
from __future__ import annotations

from engine import Engine, ok, fail
from layout_engine import LayoutEngine

MIN_TOUCH = 44
INTERACTIVE = {"button", "link", "input", "select"}


class QAEngine(Engine):
    id = "qa.visual"
    capabilities = ["qa.visual"]

    def __init__(self):
        self.layout = LayoutEngine()

    def check_actions(self, page: dict, known_actions: set[str] | None) -> list[str]:
        issues = []
        for s in page.get("sections", []):
            for c in s.get("components", []):
                if c.get("type") in INTERACTIVE:
                    aid = c.get("action_id")
                    if not aid:
                        issues.append(f"{c['id']}: interactivo sin action_id")
                    elif known_actions is not None and aid not in known_actions:
                        issues.append(f"{c['id']}: action_id sin handler: {aid}")
        return issues

    def check_overlaps(self, positions: list[dict]) -> list[str]:
        issues = []
        for i, a in enumerate(positions):
            for b in positions[i + 1:]:
                if (a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"]
                        and a["y"] < b["y"] + b["height"]
                        and b["y"] < a["y"] + a["height"]):
                    issues.append(f"solape: {a['id']} ∩ {b['id']}")
        return issues

    def check_touch(self, page: dict, positions: list[dict]) -> list[str]:
        size = {p["id"]: p for p in positions}
        issues = []
        for s in page.get("sections", []):
            for c in s.get("components", []):
                if c.get("type") in INTERACTIVE and c["id"] in size:
                    p = size[c["id"]]
                    if p["width"] < MIN_TOUCH or p["height"] < MIN_TOUCH:
                        issues.append(
                            f"{c['id']}: táctil < {MIN_TOUCH}px "
                            f"({p['width']}x{p['height']})")
        return issues

    def check_breakpoints(self, page: dict, columns: int, gap: int) -> list[str]:
        elements = []
        for s in page.get("sections", []):
            for c in s.get("components", []):
                props = c.get("properties", {})
                elements.append({
                    "id": c["id"],
                    "span": props.get("span", 1),
                    "height": max(props.get("height", MIN_TOUCH), MIN_TOUCH),
                })
        issues = []
        for bp, width in (("mobile", 360), ("tablet", 768), ("desktop", 1280)):
            res = self.layout.compute(width, 100000, elements,
                                      columns=columns, gap=gap)
            if res["status"] != "PASS":
                issues.append(f"{bp}: layout FAIL")
                continue
            issues.extend(f"{bp}: {o}" for o in
                          self.check_overlaps(res["result"]))
            if res.get("overflow"):
                issues.append(f"{bp}: overflow {res['overflow']}")
        return issues

    def run(self, page: dict, known_actions: set[str] | None = None,
            columns: int = 12, gap: int = 8) -> dict:
        issues = []
        issues += self.check_actions(page, known_actions)
        issues += self.check_breakpoints(page, columns, gap)
        mobile = self.layout.compute(360, 100000, [
            {"id": c["id"],
             "span": c.get("properties", {}).get("span", 1),
             "height": max(c.get("properties", {}).get("height", MIN_TOUCH),
                           MIN_TOUCH)}
            for s in page.get("sections", []) for c in s.get("components", [])
        ], columns=columns, gap=gap)
        if mobile["status"] == "PASS":
            issues += self.check_touch(page, mobile["result"])
        if issues:
            return fail("QA con issues", issues=issues)
        return ok({"issues": []})

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        page = task.get("page")
        if not page:
            return fail("sin página")
        return self.run(page, known_actions=task.get("known_actions"),
                        columns=task.get("columns", 12),
                        gap=task.get("gap", 8))
