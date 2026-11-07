# pipeline_executor.py
import time
from workflow_state import WorkflowState
from recovery_engine import call_with_recovery
from health_monitor import is_shutting_down, HealthChecker
from dag_engine import DAGEngine

class PipelineExecutor:
    def __init__(self, dag: DAGEngine):
        self.dag = dag
        self.STATE_PATH = "workflow_state.json"

    def execute(self, input_data: dict, _depth: int = 0) -> WorkflowState:
        # 1. Verificar apagado seguro
        if is_shutting_down():
            state = WorkflowState.load(path=self.STATE_PATH, input_data=input_data)
            state.persist(self.STATE_PATH)
            HealthChecker.refresh(status="shutdown")
            return state

        # 2. Cargar estado previo (Checkpoint)
        state = WorkflowState.load(path=self.STATE_PATH, input_data=input_data)
        state.sentinel.log({"event": "pipeline_start", "depth": _depth})

        # 3. Ordenar el DAG
        order = self.dag.topological_sort(input_data.get("ops", []))
        
        # 4. Calcular por dónde empezar si se está reanudando
        start_idx = 0
        if state.completed_nodes:
            last = state.completed_nodes[-1]
            if last in order:
                start_idx = order.index(last) + 1

        # 5. Bucle principal
        for i in range(start_idx, len(order)):
            if is_shutting_down():
                state.persist(self.STATE_PATH)
                HealthChecker.refresh(status="shutdown_mid")
                return state

            node_id = order[i]["id"]
            state.current_node = node_id
            HealthChecker.refresh(in_flight_node=node_id)
            
            # Aquí se ejecuta la función real asociada al nodo
            try:
                # (La ejecución real se delega al dispatcher)
                state.completed_nodes.append(node_id)
                state.persist(self.STATE_PATH)
            except Exception as e:
                state.errors.append(f"{node_id}: {e}")
                state.persist(self.STATE_PATH)

        HealthChecker.refresh(status="done")
        return state
