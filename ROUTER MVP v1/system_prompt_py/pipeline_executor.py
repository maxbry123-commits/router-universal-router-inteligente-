import time
from workflow_state import WorkflowState
from health_monitor import is_shutting_down, HealthChecker
from dag_engine import DAGEngine

class PipelineExecutor:
    def __init__(self, dag: DAGEngine):
        self.dag = dag
        self.STATE_PATH = "workflow_state.json"

    def execute(self, input_data: dict, _depth: int = 0) -> WorkflowState:
        if is_shutting_down():
            state = WorkflowState.load(path=self.STATE_PATH, input_data=input_data)
            state.persist(self.STATE_PATH)
            HealthChecker.refresh(status="shutdown")
            return state

        state = WorkflowState.load(path=self.STATE_PATH, input_data=input_data)
        state.sentinel.log({"event": "pipeline_start", "depth": _depth})

        try:
            order = self.dag.topological_sort(input_data.get("ops", []))
        except Exception as e:
            state.errors.append(f"DAG invalido: {e}")
            state.persist(self.STATE_PATH)
            return state

        start_idx = 0
        if state.completed_nodes:
            last = state.completed_nodes[-1]
            if last in [n["id"] for n in order]:
                start_idx = [n["id"] for n in order].index(last) + 1

        for i in range(start_idx, len(order)):
            if is_shutting_down():
                state.persist(self.STATE_PATH)
                HealthChecker.refresh(status="shutdown_mid")
                return state

            node = order[i]
            node_id = node["id"]
            state.current_node = node_id
            HealthChecker.refresh(in_flight_node=node_id)

            try:
                state.completed_nodes.append(node_id)
                state.persist(self.STATE_PATH)
            except Exception as e:
                state.errors.append(f"{node_id}: {e}")
                state.persist(self.STATE_PATH)

        HealthChecker.refresh(status="done")
        return state
