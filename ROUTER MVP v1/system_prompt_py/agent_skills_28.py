import os
import ast

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f: return f.read()

def write_file(path: str, content: str) -> dict:
    dirname = os.path.dirname(path)
    if dirname: os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    return {"path": path, "bytes": len(content)}

def analyze_code(code: str) -> dict:
    try:
        tree = ast.parse(code)
        return {"functions": [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)], "lines": len(code.splitlines())}
    except SyntaxError as e:
        return {"error": str(e)}

AGENT_SKILLS = {
    "read_file": read_file, "write_file": write_file, "analyze_code": analyze_code
}
