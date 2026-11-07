# dag_engine.py

class MotorError(Exception):
    pass

class DAGEngine:
    def __init__(self):
        pass

    def topological_sort(self, operations: list) -> list:
        """
        Extraído de motor_cli.py.
        Ordena las operaciones de un DAG respetando depends_on.
        """
        if not isinstance(operations, list) or not operations:
            raise MotorError("El DAG no tiene operaciones.")

        table = {}
        for item in operations:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str):
                raise MotorError("ID inválido en operación.")
            if item['id'] in table:
                raise MotorError(f"ID duplicado: {item['id']}")
            
            deps = item.get('depends_on', [])
            if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
                raise MotorError(f"depends_on inválido en {item['id']}")
            
            table[item['id']] = item

        for item in operations:
            for dep in item.get('depends_on', []):
                if dep not in table:
                    raise MotorError(f"Dependencia inexistente: {dep}")

        status = {}
        result = []

        def visit(node_id):
            if status.get(node_id) == 'active':
                raise MotorError("Ciclo detectado en el DAG.")
            if status.get(node_id) == 'done':
                return
            
            status[node_id] = 'active'
            for dep in table[node_id].get('depends_on', []):
                visit(dep)
            status[node_id] = 'done'
            result.append(table[node_id])

        for item in operations:
            visit(item['id'])

        return result
