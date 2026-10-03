"""riu_conectar.py — conecta CUALQUIER agente al Router Inteligente Universal con solo su token. Sin dependencias.

    from riu_conectar import Router
    r = Router("riu_...")                          # el token que te dio el Director (o variable RIU_TOKEN)
    r.chat("hola")                                 # chat por el Router (model="auto")
    r.memoria_guardar("notas", "k1", {"x": 1})     # memoria propia (nadie mas la ve)
    r.memoria_leer("notas", "k1")
    r.espacio_guardar("informe.md", "texto")       # almacenamiento propio en HF
    r.espacio_leer("informe.md")
    r.seccion("mi-ficha", "entrada")               # pasar algo por una ficha/seccion
    r.computo(["python", "-c", "print(1)"])        # procesador HF (si el token tiene permiso computo)
    r.terminal("ls -la && nvidia-smi")              # terminal remota (permiso terminal; reemplaza SSH)
    r.yo()                                         # quien soy y que permisos tengo

Otras formas con el MISMO token: cliente OpenAI con base_url=<puerta>/v1/router; MCP en <puerta>/mcp/ (Bearer token).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PUERTA = "https://comand-center-1-claude-github-mcp-backup.hf.space"


class RouterError(RuntimeError):
    pass


class Router:
    def __init__(self, token: str | None = None, url: str | None = None, timeout: float = 300.0) -> None:
        self.token = token or os.environ.get("RIU_TOKEN", "")
        if not self.token:
            raise RouterError("Falta el token (Router('riu_...') o variable RIU_TOKEN)")
        self.url = (url or os.environ.get("RIU_URL") or PUERTA).rstrip("/")
        self.timeout = timeout

    # ---- base
    def _call(self, method: str, path: str, body: Any = None, raw: bytes | None = None) -> Any:
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/json"}
        data = raw
        if body is not None:
            data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
        req = urllib.request.Request(self.url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                payload = resp.read()
                ctype = resp.headers.get("content-type", "")
                return json.loads(payload) if "json" in ctype else payload
        except urllib.error.HTTPError as exc:
            raise RouterError(f"{exc.code} {exc.read().decode('utf-8', 'replace')[:300]}") from None

    # ---- usar
    def yo(self) -> dict[str, Any]:
        return self._call("GET", "/tokens/yo")

    def chat(self, texto: str, model: str = "auto", system: str = "", max_tokens: int = 1024) -> str:
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": texto}]
        out = self._call("POST", "/v1/router/chat/completions", {"model": model, "messages": msgs, "max_tokens": max_tokens})
        return out["choices"][0]["message"]["content"]

    def memoria_guardar(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        return self._call("POST", "/memoria/save", {"scope": scope, "key": key, "data": data})

    def memoria_leer(self, scope: str, key: str) -> dict[str, Any]:
        return self._call("GET", "/memoria/load?" + urllib.parse.urlencode({"scope": scope, "key": key}))

    def memoria_buscar(self, scope: str, query: str, k: int = 10) -> dict[str, Any]:
        return self._call("GET", "/memoria/search?" + urllib.parse.urlencode({"scope": scope, "query": query, "k": k}))

    def espacio_guardar(self, ruta: str, contenido: str | bytes) -> dict[str, Any]:
        raw = contenido.encode("utf-8") if isinstance(contenido, str) else contenido
        return self._call("PUT", "/espacio/" + urllib.parse.quote(ruta), raw=raw)

    def espacio_leer(self, ruta: str) -> bytes:
        return self._call("GET", "/espacio/" + urllib.parse.quote(ruta))

    def espacio_lista(self) -> list[str]:
        return self._call("GET", "/espacio")["archivos"]

    def secciones(self) -> list[dict[str, Any]]:
        return self._call("GET", "/secciones")["secciones"]

    def seccion(self, nombre: str, entrada: str) -> dict[str, Any]:
        return self._call("POST", f"/secciones/{urllib.parse.quote(nombre)}/run", {"input": entrada})

    def computo(self, comando: list[str], flavor: str = "cpu-basic", imagen: str = "python:3.12", timeout: str = "30m") -> dict[str, Any]:
        return self._call("POST", "/hf/compute/run", {"command": comando, "flavor": flavor, "image": imagen, "timeout": timeout})

    def terminal(self, comando: str, flavor: str = "cpu-basic", timeout: str = "30m") -> dict[str, Any]:
        return self._call("POST", "/terminal/run", {"comando": comando, "flavor": flavor, "timeout": timeout})

    def terminal_ver(self, job_id: str, logs: int = 60) -> dict[str, Any]:
        return self._call("GET", f"/terminal/{job_id}?logs={logs}")

    # ---- datos para otros clientes
    def openai_base_url(self) -> str:
        return self.url + "/v1/router"

    def mcp_config(self) -> dict[str, Any]:
        return {"url": self.url + "/mcp/", "headers": {"Authorization": "Bearer " + self.token}, "transport": "streamable-http"}


if __name__ == "__main__":
    print(json.dumps(Router().yo(), indent=2, ensure_ascii=False))
