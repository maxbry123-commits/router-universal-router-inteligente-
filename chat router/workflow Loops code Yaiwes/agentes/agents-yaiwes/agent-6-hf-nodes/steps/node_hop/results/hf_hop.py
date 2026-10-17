# hf_hop.py

from typing import Optional

def node_state(ram_pct: float, cpu_pct: float) -> str:
    load = max(ram_pct, cpu_pct)
    if load < 80:
        return "GREEN"
    if load < 90:
        return "YELLOW"
    if load < 95:
        return "DRAIN"
    return "CLOSED"

def choose_node(nodes: list, need_mb: float) -> Optional[str]:
    for node in nodes:
        state = node_state(node["ram_pct"], node["cpu_pct"])
        if state in ("GREEN", "YELLOW") and node["active"] < node["max_parallel"] and node["free_mb"] >= need_mb:
            return node["id"]
    return None

def next_action(nodes: list, need_mb: float) -> dict:
    node_id = choose_node(nodes, need_mb)
    if node_id is not None:
        return {"node": node_id}
    has_drain = any(node_state(node["ram_pct"], node["cpu_pct"]) == "DRAIN" for node in nodes)
    if has_drain:
        return {"node": None, "action": "QUEUE"}
    return {"node": None, "action": "SCALE_OUT"}
