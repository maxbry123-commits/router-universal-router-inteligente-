"""Action/Flow Engine: botón → action_id → handler; flujo visual → DAG ejecutable.

Regla: ningún botón muerto (todo action_id debe tener handler registrado).
"""
from __future__ import annotations

from engine import Engine, ok, fail

BUILTIN_HANDLERS = {"validate", "serialize", "persist", "notify"}


class ActionFlowEngine(Engine):
    id = "ui.actions"
    capabilities = ["ui.actions"]

    def __init__(self):
        self.handlers: dict[str, callable] = {}
        for name in BUILTIN_HANDLERS:
            self.handlers[name] = self._builtin(name)

    @staticmethod
    def _builtin(name: str):
        def handler(payload: dict) -> dict:
            return {"handler": name, "status": "PASS", "payload": payload}
        return handler

    def register_handler(self, action_id: str, handler) -> None:
        self.handlers[action_id] = handler

    def bind_button(self, button_id: str, action_id: str) -> dict:
        if action_id not in self.handlers:
            return fail(f"botón muerto: {button_id} → {action_id} sin handler")
        return ok({"button": button_id, "action_id": action_id})

    def check_dead_buttons(self, page: dict) -> list[str]:
        """Botones del canvas cuyo action_id no tiene handler."""
        dead = []
        for section in page.get("sections", []):
            for comp in section.get("components", []):
                if comp.get("type") == "button":
                    aid = comp.get("action_id")
                    if not aid or aid not in self.handlers:
                        dead.append(comp["id"])
        return dead

    def compile_flow(self, flow: dict) -> dict:
        """Compila {nodes, edges} a un DAG ejecutable (orden topológico)."""
        nodes = {n["id"]: n for n in flow.get("nodes", [])}
        edges = flow.get("edges", [])
        for n in nodes.values():
            step = n.get("step")
            if step not in self.handlers:
                return fail(f"paso sin handler: {n['id']} ({step})")
        indegree = {nid: 0 for nid in nodes}
        adj = {nid: [] for nid in nodes}
        for e in edges:
            if e["from"] not in nodes or e["to"] not in nodes:
                return fail(f"arista inválida: {e}")
            adj[e["from"]].append(e["to"])
            indegree[e["to"]] += 1
        queue = sorted([n for n, d in indegree.items() if d == 0])
        order = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for nxt in sorted(adj[nid]):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if len(order) != len(nodes):
            return fail("ciclo detectado en el flujo")
        return ok({"order": order,
                   "steps": [nodes[n]["step"] for n in order]})

    def run_flow(self, compiled: dict, payload: dict | None = None) -> dict:
        data = payload or {}
        trace = []
        for step in compiled["steps"]:
            out = self.handlers[step](data)
            trace.append(out)
            if out.get("status") != "PASS":
                return fail(f"paso falló: {step}", trace=trace)
        return ok(trace)

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        if "flow" in task:
            compiled = self.compile_flow(task["flow"])
            if compiled["status"] != "PASS":
                return compiled
            return self.run_flow(compiled["result"], task.get("payload"))
        if "page" in task:
            dead = self.check_dead_buttons(task["page"])
            if dead:
                return fail(f"botones muertos: {dead}", dead=dead)
            return ok({"dead": []})
        return fail("tarea sin 'flow' ni 'page'")
