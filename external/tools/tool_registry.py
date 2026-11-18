"""tool_registry.py - Registro determinista de tools disponibles."""
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Tool:
    name: str
    fn: Callable
    schema: dict = field(default_factory=dict)
    tags: tuple = ()

class _Registry:
    def __init__(self): self._t = {}
    def register(self, name, fn, schema=None, tags=()):
        self._t[name] = Tool(name, fn, schema or {}, tuple(tags))
    def get(self, name): return self._t.get(name)
    def list(self): return sorted(self._t.keys())
    def invoke(self, name, **kw):
        t = self.get(name)
        if not t: return {"ok": False, "error": f"unknown_tool:{name}"}
        try: return t.fn(**kw)
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}:{e}"}

REGISTRY = _Registry()

def _bootstrap():
    from external.tools import fs_tools, shell_tool, verify_tool
    REGISTRY.register("read_file", fs_tools.read_file, {"path": "str"}, ("fs",))
    REGISTRY.register("write_file", fs_tools.write_file,
                      {"path": "str", "content": "str"}, ("fs",))
    REGISTRY.register("list_dir", fs_tools.list_dir, {"path": "str"}, ("fs",))
    REGISTRY.register("grep", fs_tools.grep,
                      {"pattern": "str", "path": "str"}, ("fs",))
    REGISTRY.register("run_shell", shell_tool.run_shell,
                      {"cmd": "str", "timeout": "int"}, ("shell",))
    REGISTRY.register("run_tests", verify_tool.run_tests, {"path": "str"}, ("verify",))
    REGISTRY.register("run_lint", verify_tool.run_lint, {"path": "str"}, ("verify",))
    REGISTRY.register("run_types", verify_tool.run_types, {"path": "str"}, ("verify",))
    REGISTRY.register("py_compile", verify_tool.py_compile, {"path": "str"}, ("verify",))
    REGISTRY.register("ast_parse", verify_tool.ast_parse, {"path": "str"}, ("verify",))
    REGISTRY.register("json_load", verify_tool.json_load, {"path": "str"}, ("verify",))
    REGISTRY.register("yaml_load", verify_tool.yaml_load, {"path": "str"}, ("verify",))

_bootstrap()
