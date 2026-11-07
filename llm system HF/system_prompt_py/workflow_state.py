import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

class Sentinel:
    def __init__(self):
        self.events: List[dict] = []
        self.node_executions: Dict[str, int] = {}
        self.start_time = time.time()

    def log(self, event: dict):
        event["timestamp"] = time.time()
        self.events.append(event)
        nid = event.get("node_id")
        if nid:
            self.node_executions[nid] = self.node_executions.get(nid, 0) + 1
            if self.node_executions[nid] > 10:
                raise Exception(f"Loop infinito en nodo {nid}")

    def get_metrics(self) -> dict:
        return {"total_events": len(self.events), "node_executions": dict(self.node_executions), "uptime_s": round(time.time() - self.start_time, 3)}

@dataclass
class WorkflowState:
    input_data: dict
    current_node: Optional[str] = None
    completed_nodes: List[str] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    node_results: Dict[str, dict] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    sentinel: Sentinel = field(default_factory=Sentinel)
    STATE_PATH = "workflow_state.json"
