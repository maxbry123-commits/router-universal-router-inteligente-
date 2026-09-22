import json
import re

def validate_orders(text: str) -> dict:
    # Attempt to locate and parse JSON within the text
    start = text.find('{')
    if start == -1:
        return {"ok": [], "rejected": [], "count": 0}
    
    data = None
    # Try to parse a JSON object from start to various end positions
    for end in range(len(text), start, -1):
        substr = text[start:end]
        try:
            data = json.loads(substr)
            break
        except json.JSONDecodeError:
            continue
    
    if data is None:
        # Fallback: try to extract the "orders" array directly
        orders_key = text.find('"orders":')
        if orders_key == -1:
            return {"ok": [], "rejected": [], "count": 0}
        bracket_start = text.find('[', orders_key)
        if bracket_start == -1:
            return {"ok": [], "rejected": [], "count": 0}
        stack = 0
        for i in range(bracket_start, len(text)):
            ch = text[i]
            if ch == '[':
                stack += 1
            elif ch == ']':
                stack -= 1
                if stack == 0:
                    orders_str = text[bracket_start:i+1]
                    try:
                        orders = json.loads(orders_str)
                        data = {"orders": orders}
                    except json.JSONDecodeError:
                        data = {"orders": []}
                    break
        else:
            data = {"orders": []}
    
    orders = data.get("orders", [])
    if not isinstance(orders, list):
        orders = []
    
    ok_list = []
    rejected_list = []
    for order in orders:
        if isinstance(order, dict) and order.get("flavor") in ("cpu-basic", "cpu-upgrade"):
            ok_list.append(order)
        else:
            rejected_list.append(order)
    
    return {"ok": ok_list, "rejected": rejected_list, "count": len(orders)}
