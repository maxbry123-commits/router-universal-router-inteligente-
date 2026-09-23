"""install_report — solo máquina 32 GB RAM (flavor técnico cpu-upgrade).
cpu-basic (=16GB) se rechaza. GPU se rechaza.
"""
from __future__ import annotations

import json
import re
from typing import Any


ALLOWED = frozenset({"cpu-upgrade"})  # solo 32 GB RAM


def _extract_json(text: str) -> Any:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    blob = m.group(1).strip() if m else text
    # try whole blob, else first {...}
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        i, j = blob.find("{"), blob.rfind("}")
        if i >= 0 and j > i:
            return json.loads(blob[i : j + 1])
        raise


def validate_orders(text: str) -> dict:
    data = _extract_json(text)
    orders = data.get("orders", data if isinstance(data, list) else [])
    ok, rejected = [], []
    for order in orders:
        if not isinstance(order, dict):
            rejected.append(order)
            continue
        flavor = order.get("flavor")
        if flavor in ALLOWED:
            ok.append(order)
        else:
            rejected.append(order)
    return {"ok": ok, "rejected": rejected, "count": len(orders)}
