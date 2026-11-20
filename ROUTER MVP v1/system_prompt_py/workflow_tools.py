import hashlib
from code_splitter import split_code, NodeTooLargeError
from loc_limits import MAX_BLOCK_LOC

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "dividir_tarea", "description": "Registra el plan de partes de una tarea grande.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"},
            "partes": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "desc": {"type": "string"}}, "required": ["id", "desc"]}}},
            "required": ["task_id", "partes"]}}},
    {"type": "function", "function": {"name": "entregar_parte", "description": "Entrega el código de una parte. Máximo 200 LOC.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "part_id": {"type": "string"}, "code": {"type": "string"}},
            "required": ["task_id", "part_id", "code"]}}},
    {"type": "function", "function": {"name": "checkpoint_guardar", "description": "Guarda el texto parcial de una parte para reanudar.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "part_id": {"type": "string"}, "text": {"type": "string"}},
            "required": ["task_id", "part_id", "text"]}}},
    {"type": "function", "function": {"name": "recuperar_checkpoint", "description": "Devuelve partes hechas, pendientes y parcial de una tarea.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "continuar_cola", "description": "Devuelve la siguiente parte pendiente o DONE.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
]

def _bid(task_id: str, part_id: str) -> str:
    return f"{task_id}:{part_id}"

class WorkflowTools:
    def __init__(self, checkpoint):
        self.cp = checkpoint

    def _plan(self, task_id: str) -> list:
        return self.cp.state.setdefault("plan", {}).get(task_id, [])

    def dividir_tarea(self, task_id: str, partes: list) -> dict:
        ids = [p["id"] for p in partes]
        if len(ids) != len(set(ids)) or not ids:
            return {"status": "error", "error": "ids de parte vacios o repetidos"}
        self.cp.state.setdefault("plan", {})[task_id] = [{"id": p["id"], "desc": p["desc"]} for p in partes]
        self.cp._save()
        return {"status": "ok", "partes": len(ids)}

    def entregar_parte(self, task_id: str, part_id: str, code: str) -> dict:
        if part_id not in [p["id"] for p in self._plan(task_id)]:
            return {"status": "error", "error": "parte no existe en el plan"}
        try:
            split = split_code(code, MAX_BLOCK_LOC, _bid(task_id, part_id))
        except NodeTooLargeError as e:
            return {"status": "error", "error": str(e)}
        loc = len(code.splitlines())
        self.cp.save_block(_bid(task_id, part_id), code)
        self.cp.clear_partial(_bid(task_id, part_id))
        return {"status": "ok", "loc": loc, "partes_internas": len(split["parts"])}

    def checkpoint_guardar(self, task_id: str, part_id: str, text: str) -> dict:
        self.cp.save_partial(_bid(task_id, part_id), text)
        return {"status": "ok", "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}

    def recuperar_checkpoint(self, task_id: str) -> dict:
        done = {b["id"] for b in self.cp.state["completed_blocks"]}
        plan = self._plan(task_id)
        hechas = [p["id"] for p in plan if _bid(task_id, p["id"]) in done]
        pendientes = [p["id"] for p in plan if _bid(task_id, p["id"]) not in done]
        parcial = {p["id"]: self.cp.get_partial(_bid(task_id, p["id"])) for p in plan
                   if self.cp.get_partial(_bid(task_id, p["id"]))}
        return {"status": "ok", "hechas": hechas, "pendientes": pendientes, "parciales": parcial}

    def continuar_cola(self, task_id: str) -> dict:
        r = self.recuperar_checkpoint(task_id)
        if not r["pendientes"]:
            return {"status": "ok", "siguiente": "DONE"}
        return {"status": "ok", "siguiente": r["pendientes"][0]}

    def dispatch(self, name: str, args: dict) -> dict:
        fn = {"dividir_tarea": self.dividir_tarea, "entregar_parte": self.entregar_parte,
              "checkpoint_guardar": self.checkpoint_guardar, "recuperar_checkpoint": self.recuperar_checkpoint,
              "continuar_cola": self.continuar_cola}.get(name)
        if fn is None:
            return {"status": "error", "error": f"herramienta desconocida: {name}"}
        try:
            return fn(**args)
        except TypeError as e:
            return {"status": "error", "error": f"argumentos invalidos: {e}"}
