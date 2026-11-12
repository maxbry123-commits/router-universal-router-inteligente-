import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from core_recovery import atomic_write_json
import json

class Sentinel:
    def __init__(self):
        self.events = []
        self.node_executions = {}
    def log(self, event: dict):
        event["timestamp"] = time.time()
        self.events.append(event)
    def get_metrics(self) -> dict:
        return {"total_events": len(self.events), "node_executions": self.node_executions}

@dataclass
class WorkflowState:
    input_data: dict
    current_node: Optional[str] = None
    completed_nodes: List[str] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    sentinel: Sentinel = field(default_factory=Sentinel)
    STATE_PATH = "workflow_state.json"

    def persist(self, path: str = None) -> None:
        path = path or self.STATE_PATH
        try:
            atomic_write_json(path, {
                "input_data": self.input_data,
                "current_node": self.current_node,
                "completed_nodes": self.completed_nodes,
                "retry_counts": self.retry_counts,
                "errors": self.errors
            })
        except Exception:
            pass

    @classmethod
    def load(cls, path: str = None, input_data: dict = None) -> "WorkflowState":
        path = path or cls.STATE_PATH
        state = cls(input_data=input_data or {})
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                state.current_node = data.get("current_node")
                state.completed_nodes = data.get("completed_nodes", [])
                state.retry_counts = data.get("retry_counts", {})
                state.errors = data.get("errors", [])
        except FileNotFoundError:
            pass
        return state
