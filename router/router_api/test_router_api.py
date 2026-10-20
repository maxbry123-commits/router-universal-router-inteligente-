"""Pruebas offline de router_api (edificio 1) y de su cliente (edificio 2). Sin red ni modelos."""
import importlib.util, os, sys, types

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _Sq:
    def __init__(self): self.d = {}
    def save(self, s, k, v): self.d[(s, k)] = v; return True
    def load(self, s, k): return [{"data": self.d[(s, k)]}] if (s, k) in self.d else []
    def health(self): return {"ok": True}


class _Mem:
    def __init__(self): self.sqlite = _Sq()
    def save(self, s, k, v): return self.sqlite.save(s, k, v)
    def load(self, s, k): return self.sqlite.load(s, k)
    def search(self, *a, **k): return ["x"]


def _falsos():
    mem = _Mem()
    pk = types.ModuleType("integration.chat_mvp.providers")
    pk.env_keys = lambda p: ["k1"] if p == "hf" else []
    pk.base_url = lambda p: "https://u/" + p
    pk.chat = lambda p, c, m, ms, mt: {"reply": "hola " + c}
    import contextvars
    pk.ATTEMPT_DEADLINE = contextvars.ContextVar("d", default=None)
    ml = types.ModuleType("integration.chat_mvp.memoria_loader"); ml._memory = lambda: mem
    vh = types.ModuleType("integration.chat_mvp.vault_hook"); vh.provider_keys = lambda p: ["v-" + p]
    for n in ("integration", "integration.chat_mvp"):
        sys.modules.setdefault(n, types.ModuleType(n))
    sys.modules.update({"integration.chat_mvp.providers": pk, "integration.chat_mvp.memoria_loader": ml, "integration.chat_mvp.vault_hook": vh})
    sys.modules["integration.chat_mvp"].providers, sys.modules["integration.chat_mvp"].vault_hook = pk, vh
    return _cargar("router_api_plugin", os.path.join(AQUI, "plugin.py"))


def test_acciones_y_memoria():
    h = _falsos().handle
    assert h("status", {})["status"] == "ok"
    assert h("memoria", {"op": "borrar_todo"})["status"] == "degraded"
    assert h("memoria", {"op": "save", "args": ["s", "k", {"a": 1}]})["status"] == "ok"
    assert h("memoria", {"op": "sqlite_load", "args": ["s", "k"]})["valor"] == [{"data": {"a": 1}}]
    assert h("env_keys", {"proveedor": "hf"})["claves"] == ["k1"]
    assert h("base_url", {"proveedor": "hf"})["url"] == "https://u/hf"
    assert h("provider_keys", {"proveedor": "github"})["claves"] == ["v-github"]
    assert h("chat", {"proveedor": "hf", "modelo": "m", "mensajes": []})["respuesta"] == {"reply": "hola k1"}
    assert h("chat", {"proveedor": "zz"})["respuesta"]["error"] == "SIN_CLAVES_ZZ"
    assert h("nada", {})["status"] == "degraded"


def test_cliente_http_simulado():
    cl = _cargar("cliente_t", os.path.join(RAIZ, "plugins", "router_api_cliente.py"))
    mem = _Mem(); plug = _falsos()
    cl.llamar = lambda plugin, accion, payload=None, timeout=120.0: plug.handle(accion, payload)  # el HTTP se sustituye por la llamada directa
    m = cl.memory()
    m.sqlite.save("s", "k", 5)
    assert m.sqlite.load("s", "k") == [{"data": 5}]
    assert cl.env_keys("hf") == ["k1"] and cl.base_url("hf") == "https://u/hf" and cl.provider_keys("x") == ["v-x"]
    assert cl.chat("hf", "m", [], 10, 5) == {"reply": "hola k1"}


def test_cliente_sin_router_degrada():
    cl = _cargar("cliente_t2", os.path.join(RAIZ, "plugins", "router_api_cliente.py"))
    os.environ.pop("RIU_ROUTER_URL", None)
    assert cl.llamar("router_api", "status")["status"] == "degraded"
    try:
        cl.env_keys("hf"); assert False
    except RuntimeError:
        pass
