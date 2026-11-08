class MotorError(Exception):
    pass

class DAGEngine:
    def topological_sort(self, operations: list) -> list:
        if not operations:
            raise MotorError("DAG vacio")
        table = {}
        for item in operations:
            if item['id'] in table:
                raise MotorError(f"ID duplicado: {item['id']}")
            table[item['id']] = item

        for item in operations:
            for dep in item.get('depends_on', []):
                if dep not in table:
                    raise MotorError(f"Dependencia inexistente: {dep}")

        status = {}
        result = []

        def visit(node_id):
            if status.get(node_id) == 'active':
                raise MotorError("Ciclo detectado")
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
