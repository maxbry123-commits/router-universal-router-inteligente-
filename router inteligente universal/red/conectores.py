"""CONECTORES — adaptadores concretos de la red. Todos cumplen el mismo
Protocol: enviar(payload)→dict, sondear()→bool. La red no distingue si el
nodo es MCP, GitHub, un VPS o el propio orquestador: todo es un Conector.
Secretos SIEMPRE por env (Railway Variables), jamás en código.
"""
from __future__ import annotations
import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import unquote, urlparse

import httpx


class Conector(Protocol):
    conector_id: str
    async def enviar(self, payload: dict) -> dict: ...
    async def sondear(self) -> bool: ...


@dataclass
class ConectorHTTP:
    """API genérica REST (base de casi todo)."""
    conector_id: str
    base_url: str
    headers_env: dict[str, str] = field(default_factory=dict)
    timeout_s: float = 30.0

    def _headers(self) -> dict:
        return {h: (f"Bearer {os.environ[v]}" if h == "Authorization"
                    else os.environ[v])
                for h, v in self.headers_env.items() if v in os.environ}

    async def enviar(self, payload: dict) -> dict:
        ruta = payload.pop("_ruta", "")
        metodo = payload.pop("_metodo", "POST")
        async with httpx.AsyncClient(timeout=self.timeout_s) as cli:
            r = await cli.request(metodo, f"{self.base_url}{ruta}",
                                  json=payload, headers=self._headers())
            r.raise_for_status()
            return {"status": "DONE", "code": r.status_code,
                    "output": r.json() if "json" in
                    r.headers.get("content-type", "") else r.text}

    async def sondear(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as cli:
                return (await cli.get(self.base_url)).status_code < 500
        except Exception:  # noqa: BLE001
            return False


@dataclass
class ConectorMCP:
    """Servidor MCP (Model Context Protocol) vía JSON-RPC sobre HTTP/SSE."""
    conector_id: str
    endpoint: str
    token_env: str = ""
    _id: int = 0

    async def enviar(self, payload: dict) -> dict:
        self._id += 1
        rpc = {"jsonrpc": "2.0", "id": self._id,
               "method": payload.get("_metodo", "tools/call"),
               "params": {"name": payload.get("_tool", ""),
                          "arguments": payload.get("args", {})}}
        headers = ({"Authorization": f"Bearer {os.environ[self.token_env]}"}
                   if self.token_env in os.environ else {})
        async with httpx.AsyncClient(timeout=60) as cli:
            r = await cli.post(self.endpoint, json=rpc, headers=headers)
            data = r.json()
        if "error" in data:
            return {"status": "FAIL", "error": data["error"]}
        return {"status": "DONE", "output": data.get("result", {})}

    async def sondear(self) -> bool:
        try:
            r = await self.enviar({"_metodo": "tools/list"})
            return r["status"] == "DONE"
        except Exception:  # noqa: BLE001
            return False


@dataclass
class ConectorGitHub:
    """GitHub API: commits, PRs, issues, contents, dispatch de Actions."""
    conector_id: str
    repo: str
    token_env: str = "GITHUB_TOKEN"

    def _api(self) -> ConectorHTTP:
        return ConectorHTTP(
            self.conector_id, "https://api.github.com",
            headers_env={"Authorization": self.token_env})

    async def enviar(self, payload: dict) -> dict:
        accion = payload.get("_accion", "get_file")
        rutas = {
            "get_file": ("GET", f"/repos/{self.repo}/contents/"
                                f"{payload.get('path','')}"),
            "create_issue": ("POST", f"/repos/{self.repo}/issues"),
            "create_pr": ("POST", f"/repos/{self.repo}/pulls"),
            "dispatch": ("POST", f"/repos/{self.repo}/actions/workflows/"
                                 f"{payload.get('workflow','')}/dispatches"),
            "commit_file": ("PUT", f"/repos/{self.repo}/contents/"
                                   f"{payload.get('path','')}"),
        }
        metodo, ruta = rutas.get(accion, rutas["get_file"])
        body = {k: v for k, v in payload.items() if not k.startswith("_")}
        return await self._api().enviar(
            {**body, "_ruta": ruta, "_metodo": metodo})

    async def sondear(self) -> bool:
        r = await self._api().enviar({"_ruta": f"/repos/{self.repo}",
                                      "_metodo": "GET"})
        return r["status"] == "DONE"


@dataclass
class ConectorHuggingFace:
    """Hugging Face Hub adapter defined by the v6 router contract."""
    conector_id: str
    token_env: str = "HF_TOKEN"

    def _api(self) -> ConectorHTTP:
        return ConectorHTTP(
            self.conector_id,
            "https://huggingface.co/api",
            headers_env={"Authorization": self.token_env},
        )

    async def enviar(self, payload: dict) -> dict:
        accion = payload.get("_accion", "model_info")
        repo_id = payload.get("repo_id", "")
        rutas = {
            "model_info": ("GET", f"/models/{repo_id}"),
            "dataset_info": ("GET", f"/datasets/{repo_id}"),
            "inference": ("POST", f"/models/{repo_id}"),
            "list_spaces": ("GET", "/spaces"),
        }
        metodo, ruta = rutas.get(accion, rutas["model_info"])
        body = {k: v for k, v in payload.items() if not k.startswith("_")}
        return await self._api().enviar(
            {"_ruta": ruta, "_metodo": metodo, **body}
        )

    async def sondear(self) -> bool:
        return await self._api().sondear()


@dataclass
class ConectorDB:
    """DB v6: Postgres/MySQL/Redis con DSN secreto leído solo desde entorno."""
    conector_id: str
    dsn_env: str
    motor: str = "postgres"

    def _dsn(self) -> str:
        dsn = os.environ.get(self.dsn_env, "")
        if not dsn:
            raise RuntimeError(f"env_faltante:{self.dsn_env}")
        return dsn

    @staticmethod
    def _mysql_config(dsn: str) -> dict:
        parsed = urlparse(dsn)
        if parsed.scheme not in {"mysql", "mysql+aiomysql"}:
            raise ValueError("dsn_mysql_invalido")
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "db": parsed.path.lstrip("/"),
        }

    async def _postgres(self, accion: str, sql: str, params: list) -> object:
        import asyncpg
        conn = await asyncpg.connect(self._dsn())
        try:
            if accion == "query":
                return [dict(row) for row in await conn.fetch(sql, *params)]
            if accion in {"execute", "migrate"}:
                return await conn.execute(sql, *params)
            if accion == "healthcheck":
                return await conn.fetchval("SELECT 1")
            raise ValueError(f"accion_no_soportada:{accion}")
        finally:
            await conn.close()

    async def _mysql(self, accion: str, sql: str, params: list) -> object:
        import aiomysql
        conn = await aiomysql.connect(**self._mysql_config(self._dsn()))
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if accion == "query":
                    await cur.execute(sql, tuple(params))
                    return list(await cur.fetchall())
                if accion in {"execute", "migrate"}:
                    await cur.execute(sql, tuple(params))
                    await conn.commit()
                    return {"rowcount": cur.rowcount}
                if accion == "healthcheck":
                    await cur.execute("SELECT 1")
                    return await cur.fetchone()
                raise ValueError(f"accion_no_soportada:{accion}")
        finally:
            conn.close()

    async def _redis(self, accion: str, sql: str, params: list) -> object:
        import redis.asyncio as redis
        client = redis.from_url(self._dsn())
        try:
            if accion == "healthcheck":
                return await client.ping()
            if accion == "query":
                if not sql:
                    raise ValueError("redis_command_faltante")
                return await client.execute_command(sql, *params)
            raise ValueError(f"accion_no_soportada:{accion}")
        finally:
            await client.aclose()

    async def enviar(self, payload: dict) -> dict:
        accion = payload.get("_accion", "query")
        sql = payload.get("sql", "")
        params = payload.get("params", [])
        if not isinstance(params, list):
            return {"status": "FAIL", "error": "params_debe_ser_lista"}
        handlers = {
            "postgres": self._postgres,
            "mysql": self._mysql,
            "redis": self._redis,
        }
        handler = handlers.get(self.motor)
        if handler is None:
            return {"status": "FAIL",
                    "error": f"motor_no_soportado:{self.motor}"}
        try:
            output = await handler(accion, sql, params)
            return {"status": "DONE", "output": output}
        except Exception as exc:  # noqa: BLE001
            return {"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"}

    async def sondear(self) -> bool:
        result = await self.enviar({"_accion": "healthcheck"})
        return result["status"] == "DONE"


@dataclass
class ConectorVPS:
    """VPS/servidor remoto vía agente HTTP propio."""
    conector_id: str
    agent_url: str
    token_env: str = "VPS_AGENT_TOKEN"
    comandos_permitidos: tuple[str, ...] = ("status", "deploy", "restart",
                                            "logs", "run_script")

    async def enviar(self, payload: dict) -> dict:
        if payload.get("_cmd") not in self.comandos_permitidos:
            return {"status": "FAIL",
                    "error": f"cmd_no_permitido:{payload.get('_cmd')}"}
        api = ConectorHTTP(self.conector_id, self.agent_url,
                           headers_env={"Authorization": self.token_env},
                           timeout_s=120)
        return await api.enviar({**payload, "_ruta": "/exec"})

    async def sondear(self) -> bool:
        api = ConectorHTTP(self.conector_id, self.agent_url,
                           headers_env={"Authorization": self.token_env})
        return await api.sondear()


@dataclass
class ConectorMemoria:
    """Puente a la memoria del sistema (State Engine / shared_knowledge)."""
    conector_id: str
    estado: Any

    async def enviar(self, payload: dict) -> dict:
        op = payload.get("_op", "leer")
        if op == "leer":
            return {"status": "DONE",
                    "output": self.estado.leer(payload["path"])}
        if op == "commit":
            h = self.estado.commit(payload["proposals"],
                                   actor=payload.get("actor", "red"))
            return {"status": "DONE", "output": {"commit": h}}
        if op == "snapshot":
            return {"status": "DONE", "output": self.estado.snapshot()}
        return {"status": "FAIL", "error": f"op_desconocida:{op}"}

    async def sondear(self) -> bool:
        return self.estado.verificar_hash_chain()


@dataclass
class ConectorInterno:
    """Nodo interno: orquestador, team agente, u otro agente ARRIBA o ABAJO."""
    conector_id: str
    handler: Any

    async def enviar(self, payload: dict) -> dict:
        try:
            out = await asyncio.wait_for(self.handler(payload), timeout=300)
            return out if isinstance(out, dict) and "status" in out \
                else {"status": "DONE", "output": out}
        except asyncio.TimeoutError:
            return {"status": "FAIL", "error": "timeout_interno"}

    async def sondear(self) -> bool:
        return True


@dataclass
class ConectorWebhook:
    """Notifica hacia afuera (Telegram, Discord, n8n, Zapier...)."""
    conector_id: str
    url_env: str

    async def enviar(self, payload: dict) -> dict:
        url = os.environ.get(self.url_env, "")
        if not url:
            return {"status": "FAIL", "error": f"env_faltante:{self.url_env}"}
        async with httpx.AsyncClient(timeout=15) as cli:
            r = await cli.post(url, json=payload)
            return {"status": "DONE" if r.status_code < 300 else "FAIL",
                    "code": r.status_code}

    async def sondear(self) -> bool:
        return self.url_env in os.environ
