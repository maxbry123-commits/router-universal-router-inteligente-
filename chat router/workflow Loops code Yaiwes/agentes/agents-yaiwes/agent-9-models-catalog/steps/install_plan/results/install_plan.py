"""install_plan.py — Plan de instalación de modelos en nodos.

Standard library only. Self-contained.
"""

def plan_install(models, nodes, ram_cap_gb):
    """Asigna modelos a nodos según las reglas dadas.

    Args:
        models: lista de dicts {"id": str, "size_mb": int}
        nodes: lista de ids de nodo en orden
        ram_cap_gb: capacidad RAM por nodo en GB

    Returns:
        dict {id_nodo: id_modelo}
    """
    if not models:
        return {}

    # Clasificar ligeros (<=3500) y pesados (>3500)
    ligeros = sorted(
        [m for m in models if m["size_mb"] <= 3500],
        key=lambda x: x["size_mb"]
    )
    pesados = [m for m in models if m["size_mb"] > 3500]

    if not ligeros:
        return {}

    resultado = {}
    num_nodos = len(nodes)

    # Asignación normal: ligeros rotativos
    for i, nodo in enumerate(nodes):
        idx_ligero = i % len(ligeros)
        resultado[nodo] = ligeros[idx_ligero]["id"]

    # Excepción: si hay al menos 2 nodos y existe algún pesado que cumpla size_mb + 6000 <= ram_cap_gb * 1024
    if num_nodos >= 2 and pesados:
        ram_bytes = ram_cap_gb * 1024
        candidatos = [m for m in pesados if m["size_mb"] + 6000 <= ram_bytes]
        if candidatos:
            # Elegir el pesado más grande entre los candidatos
            mejor_pesado = max(candidatos, key=lambda x: x["size_mb"])
            # El último nodo recibe el pesado
            ultimo_nodo = nodes[-1]
            resultado[ultimo_nodo] = mejor_pesado["id"]

    return resultado
