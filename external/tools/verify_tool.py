"""verify_tool.py - Verificación determinista de código.
Todas las funciones devuelven dict con 'ok'. Nunca lanzan excepción."""
import ast
import json
from pathlib import Path
from external.tools.shell_tool import run_shell


def py_compile(path: str) -> dict:
    """Compila el archivo Python con py_compile."""
    if not Path(path).exists():
        return {"ok": False, "error": "not_found"}
    return run_shell(f"python -m py_compile {path}", timeout=15)


def ast_parse(path: str) -> dict:
    """Parsea el archivo con ast sin ejecutarlo."""
    try:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": "not_found"}
        ast.parse(p.read_text("utf-8"))
        return {"ok": True, "path": path}
    except SyntaxError as e:
        return {"ok": False, "error": f"syntax:{e.lineno}:{e.msg}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}


def run_tests(path: str = ".") -> dict:
    """Ejecuta pytest con maxfail=3."""
    return run_shell(f"pytest -q {path} --maxfail=3", timeout=60)


def run_lint(path: str = ".") -> dict:
    """Ejecuta ruff check."""
    return run_shell(f"ruff check {path}", timeout=30)


def run_types(path: str = ".") -> dict:
    """Ejecuta mypy con ignore-missing-imports."""
    return run_shell(f"mypy --ignore-missing-imports {path}", timeout=60)


def json_load(path: str) -> dict:
    """Carga un JSON y devuelve el data."""
    try:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": "not_found"}
        return {"ok": True, "data": json.loads(p.read_text("utf-8"))}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}


def yaml_load(path: str) -> dict:
    """Carga un YAML si pyyaml está instalado."""
    try:
        import yaml
    except ImportError:
        return {"ok": False, "error": "yaml_not_installed"}
    try:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": "not_found"}
        return {"ok": True, "data": yaml.safe_load(p.read_text("utf-8"))}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}
