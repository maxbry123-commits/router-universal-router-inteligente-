"""Layout Engine: geometría sin LLM (grid/flex, gap, snap, bounds, breakpoints)."""
from __future__ import annotations

from engine import Engine, ok, fail

BREAKPOINTS = {"mobile": 480, "tablet": 768, "desktop": 1024}


def breakpoint_for(viewport_width: int) -> str:
    if viewport_width < BREAKPOINTS["tablet"]:
        return "mobile"
    if viewport_width < BREAKPOINTS["desktop"]:
        return "tablet"
    return "desktop"


def snap(value: float, grid: int = 1) -> float:
    if grid <= 1:
        return value
    return round(value / grid) * grid


class LayoutEngine(Engine):
    id = "ui.layout"
    capabilities = ["ui.layout"]

    def compute(self, viewport_width: int, viewport_height: int,
                elements: list[dict], columns: int = 12,
                gap: int = 8, snap_grid: int = 1) -> dict:
        if columns < 1:
            return fail("columns debe ser >= 1")
        bp = breakpoint_for(viewport_width)
        effective_cols = 1 if bp == "mobile" else min(columns, max(1, len(elements)) or 1)
        col_w = (viewport_width - gap * (effective_cols + 1)) / effective_cols
        positions = []
        row, col = 0, 0
        for el in elements:
            span = max(1, min(el.get("span", 1), effective_cols))
            if col + span > effective_cols:
                row += 1
                col = 0
            h = el.get("height", 120)
            x = snap(gap + col * (col_w + gap), snap_grid)
            w = snap(col_w * span + gap * (span - 1), snap_grid)
            positions.append({
                "id": el["id"],
                "x": x, "y": 0, "width": w, "height": h,
                "row": row, "col": col, "span": span,
            })
            col += span
            if col >= effective_cols:
                row += 1
                col = 0
        # y por fila: acumulamos alturas de filas previas (altura = máx de la fila)
        row_heights: dict[int, int] = {}
        for p in positions:
            row_heights[p["row"]] = max(row_heights.get(p["row"], 0), p["height"])
        y_offsets: dict[int, float] = {}
        acc: float = gap
        for r in sorted(row_heights):
            y_offsets[r] = acc
            acc += row_heights[r] + gap
        for p in positions:
            p["y"] = snap(y_offsets[p["row"]], snap_grid)
        total_height = acc
        overflow = [p["id"] for p in positions
                    if p["x"] < 0 or p["y"] < 0
                    or p["x"] + p["width"] > viewport_width
                    or p["y"] + p["height"] > viewport_height]
        return ok(positions, breakpoint=bp, columns=effective_cols,
                  bounds={"width": viewport_width, "height": total_height},
                  overflow=overflow)

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        return self.compute(
            viewport_width=task.get("viewport_width", 1024),
            viewport_height=task.get("viewport_height", 768),
            elements=task.get("elements", []),
            columns=task.get("columns", 12),
            gap=task.get("gap", 8),
            snap_grid=task.get("snap", 1),
        )
