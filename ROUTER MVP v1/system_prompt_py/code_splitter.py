import ast

class NodeTooLargeError(ValueError):
    pass

def _lines(text: str) -> int:
    return len(text.splitlines())

def split_code(code: str, max_loc: int, block_id: str) -> dict:
    if _lines(code) <= max_loc:
        return {"aggregator": None, "parts": [(block_id, code)]}
    tree = ast.parse(code)
    imports = [ast.get_source_segment(code, n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    body = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    segs = [(ast.get_source_segment(code, n), n.end_lineno - n.lineno + 1) for n in body]

    def header_len(i: int) -> int:
        return len(imports) + i + 2

    groups, cur, cur_len = [], [], 0
    for seg, ln in segs:
        if ln + header_len(0) > max_loc:
            raise NodeTooLargeError(f"NODO_MAYOR_QUE_BLOQUE: {ln} lineas > {max_loc}")
        i = len(groups)
        if cur and cur_len + ln + 1 + header_len(i) > max_loc:
            groups.append(cur)
            cur, cur_len = [], 0
            i = len(groups)
        cur.append(seg)
        cur_len += ln + 1

    if cur:
        groups.append(cur)

    names = [f"{block_id}_p{k + 1}" for k in range(len(groups))]
    parts = []
    for i, group in enumerate(groups):
        header = list(imports) + [f"from {names[j]} import *" for j in range(i)]
        text = "\n".join(header) + "\n\n" + "\n\n".join(group) + "\n"
        if _lines(text) > max_loc:
            raise NodeTooLargeError(f"PARTE {names[i]} excede {max_loc} LOC")
        parts.append((names[i], text))

    aggregator = "\n".join(f"from {n} import *" for n in names) + "\n"
    return {"aggregator": (block_id, aggregator), "parts": parts}
