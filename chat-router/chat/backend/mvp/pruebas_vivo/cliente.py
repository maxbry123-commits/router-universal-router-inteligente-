"""Cliente MCP minimo (solo biblioteca estandar) para probar el Router en vivo. La clave va en la cabecera X-API-Key, nunca en la URL ni en disco."""
import json
import time
import urllib.error
import urllib.request


class Cliente:
    def __init__(self, base, clave):
        self.base, self.clave, self.n = base.rstrip("/"), clave, 0

    def post(self, ruta, cuerpo, timeout=60):
        sol = urllib.request.Request(self.base + ruta, data=json.dumps(cuerpo).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "X-API-Key": self.clave})
        try:
            with urllib.request.urlopen(sol, timeout=timeout) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read() or b"{}")
            except ValueError:
                return exc.code, {}

    def health(self):
        sol = urllib.request.Request(self.base + "/health", headers={"X-API-Key": self.clave})
        with urllib.request.urlopen(sol, timeout=30) as r:
            return json.loads(r.read())

    def mcp(self, metodo, params=None):
        self.n += 1
        return self.post("/mcp", {"jsonrpc": "2.0", "id": self.n, "method": metodo, "params": params or {}})

    def herramienta(self, nombre, args):
        """(ok, dict): ok=False si el MCP devolvio error JSON-RPC o isError."""
        codigo, doc = self.mcp("tools/call", {"name": nombre, "arguments": args})
        if "error" in doc:
            return False, {"error": doc["error"], "http": codigo}
        res = doc.get("result") or {}
        try:
            return not res.get("isError"), json.loads(res["content"][0]["text"])
        except (KeyError, IndexError, ValueError):
            return False, {"http": codigo, "bruto": str(doc)[:300]}

    def chat(self, modelo, mensaje=None, rid="x", vueltas=20, **extra):
        """Lanza el chat y espera el resultado (long-poll de 8 s). Devuelve el JSON final o {'error': ...}."""
        args = {"ficha_qwen": "1", "modelo": modelo, "request_id": rid, **extra}
        if mensaje is not None:
            args["message"] = mensaje
        ok, r = self.herramienta("chat", args)
        if not ok:
            return {"estado": "error", "error": r}
        for _ in range(vueltas):
            if r.get("estado") != "procesando":
                return r
            ok, r = self.herramienta("resultado", {"proceso_id": r["proceso_id"], "espera": 8})
            if not ok:
                return {"estado": "error", "error": r}
            time.sleep(0.2)
        return {"estado": "error", "error": "tiempo agotado esperando el resultado"}


def texto(r):
    try:
        return r["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""
