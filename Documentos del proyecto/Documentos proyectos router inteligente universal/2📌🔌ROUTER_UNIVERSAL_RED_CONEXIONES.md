# ROUTER UNIVERSAL — RED DE CONEXIONES MAXBRY
# Repo 10: router-red | 3 archivos: ~180 + ~380 + ~350 LOC
# 1 red, N nodos (MCP, API, GitHub, VPS, DB, memoria, Telegram, orquestador,
# team, agentes arriba/abajo). Tú declaras: quién recibe → por dónde sale →
# dónde llega. Soporta 1000+ destinos por namespaces. Todo pasa por enchufe.

---

## ARCHIVO 1 — `red/enchufe_gate.py` (~180 LOC)

```python
"""ENCHUFE GATE — aduana de la red. Ningún conector entra a la red sin
contrato v1.5 mínimo válido. Versión ligera del validador S7 (el completo
vive en repo 12; este gate usa el mismo schema).
"""
from __future__ import annotations
import re
from dataclasses import dataclass

RE_ARTIFACT = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
RE_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
KINDS = {"code", "llm", "db", "api", "tool"}
TRANSPORTS = {"stdio", "importlib", "http", "sdk", "prompt", "mcp"}
SANDBOX = {"container", "process", "none"}


@dataclass(frozen=True)
class VeredictoGate:
    valido: bool
    errores: tuple[str, ...] = ()


def validar_contrato_conexion(c: dict) -> VeredictoGate:
    """Chequeos duros antes de registrar un nodo en la red."""
    e: list[str] = []
    if not RE_ARTIFACT.match(c.get("artifact_id", "")):
        e.append("artifact_id_invalido")
    if c.get("estado") not in {"active", "testing"}:
        e.append(f"estado_no_conectable:{c.get('estado')}")
    if c.get("estado") == "active" and not RE_HASH.match(
            c.get("contract_hash", "")):
        e.append("active_requiere_hash_real")
    ej = c.get("ejecucion", {})
    if ej.get("kind") not in KINDS:
        e.append("kind_invalido")
    if ej.get("transport") not in TRANSPORTS:
        e.append("transport_invalido")
    seg = c.get("seguridad", {})
    if seg.get("sandbox") not in SANDBOX:
        e.append("sandbox_invalido")
    lim = seg.get("limites", {})
    if not (isinstance(lim.get("timeout_ms"), int) and lim["timeout_ms"] > 0):
        e.append("timeout_ms_requerido")
    if lim.get("deadline_ms", 0) < lim.get("timeout_ms", 1):
        e.append("deadline_menor_que_timeout")
    rol = c.get("contrato", {}).get("rol")
    if rol == "source" and c["contrato"].get("consume") is not None:
        e.append("source_no_consume")
    if rol == "sink" and c["contrato"].get("expone") is not None:
        e.append("sink_no_expone")
    if rol == "transform" and (not c["contrato"].get("consume")
                               or not c["contrato"].get("expone")):
        e.append("transform_requiere_ambos")
    return VeredictoGate(valido=not e, errores=tuple(e))


def datatype_de(io: dict | None) -> str:
    if not io:
        return ""
    dt = io.get("datatype", {})
    return f"{dt.get('family','')}.{dt.get('type','')}.v{dt.get('version',0)}"
```

---

## ARCHIVO 2 — `red/conectores.py` (~380 LOC)

```python
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
    # ej {"Authorization": "OPENROUTER_KEY"} → lee de env en runtime
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
        except Exception:                          # noqa: BLE001
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
        except Exception:                          # noqa: BLE001
            return False


@dataclass
class ConectorGitHub:
    """GitHub API: commits, PRs, issues, contents, dispatch de Actions."""
    conector_id: str
    repo: str                                     # "maxbry123-commits/jarvis"
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
class ConectorVPS:
    """VPS/servidor remoto vía agente HTTP propio (sin SSH desde móvil:
    el VPS corre un mini FastAPI `vps_agent` que ejecuta comandos whitelist)."""
    conector_id: str
    agent_url: str                                # https://mi-vps:8700
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
    """Puente a la memoria del sistema (State Engine / shared_knowledge).
    La red también rutea lecturas/escrituras de memoria como mensajes."""
    conector_id: str
    estado: Any                                    # MasterStateEngine

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
    """Nodo interno: orquestador, team agente, u otro agente ARRIBA o ABAJO.
    Un orquestador padre puede mandar al hijo y viceversa: misma interfaz."""
    conector_id: str
    handler: Any                                   # async callable(dict)->dict

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
    url_env: str                                   # env con la URL completa

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
```

---

## ARCHIVO 3 — `red/red_universal.py` (~350 LOC)

```python
"""RED UNIVERSAL — el mapa de la red. Tú declaras rutas:
  quién recibe (origen) → por dónde sale (canal) → dónde llega (destino).
Namespaces jerárquicos soportan 1000+ nodos: 'ai.llm.openrouter',
'infra.vps.railway1', 'repo.github.jarvis', 'core.orquestador'...
Controla ENTRADA y SALIDA del orquestador, del team y de agentes
arriba/abajo. ACL por ruta. Todo evento pasa por el Audit Bus.
"""
from __future__ import annotations
import asyncio
import fnmatch
import time
from dataclasses import dataclass, field
from typing import Any

from enchufe_gate import validar_contrato_conexion, datatype_de
from conectores import Conector


@dataclass
class NodoRed:
    nodo_id: str                  # namespace: "ai.llm.openrouter"
    conector: Conector
    contrato: dict
    tags: frozenset[str] = frozenset()
    direccion: str = "bidireccional"     # entrada|salida|bidireccional
    nivel: str = "igual"                 # arriba|igual|abajo (jerarquía)
    sano: bool = True
    fallos: int = 0


@dataclass
class Ruta:
    """1 regla de ruteo declarativa. Patrones fnmatch en origen/destino."""
    ruta_id: str
    origen: str                   # "core.orquestador" | "ai.*" | "*"
    destino: str                  # nodo o patrón; el 1º sano que matchee
    cuando: str = "*"             # tipo de mensaje (fnmatch)
    prioridad: int = 100
    activa: bool = True
    transformar: str = ""         # ficha_id transform opcional en el camino


@dataclass
class Mensaje:
    tipo: str                     # "tarea.nueva" | "codigo.commit" | ...
    origen: str
    payload: dict
    task_id: str = ""
    trace_id: str = ""
    ts: float = field(default_factory=time.time)


class RedUniversal:
    MAX_FALLOS_NODO = 5

    def __init__(self, audit: Any = None) -> None:
        self.nodos: dict[str, NodoRed] = {}
        self.rutas: list[Ruta] = []
        self.audit = audit

    # ── REGISTRO (pasa por enchufe SIEMPRE) ──
    def conectar(self, nodo_id: str, conector: Conector, contrato: dict,
                 tags: set[str] | None = None, direccion: str =
                 "bidireccional", nivel: str = "igual") -> None:
        v = validar_contrato_conexion(contrato)
        if not v.valido:
            raise ValueError(f"enchufe_rechazado:{nodo_id}:{v.errores}")
        if nodo_id in self.nodos:
            raise ValueError(f"nodo_duplicado:{nodo_id}")
        self.nodos[nodo_id] = NodoRed(nodo_id, conector, contrato,
                                      frozenset(tags or set()),
                                      direccion, nivel)
        self._ev("red.nodo_conectado", {"nodo": nodo_id, "nivel": nivel})

    def desconectar(self, nodo_id: str) -> None:
        self.nodos.pop(nodo_id, None)
        self._ev("red.nodo_desconectado", {"nodo": nodo_id})

    # ── RUTAS: el Director dibuja la red ──
    def ruta(self, ruta_id: str, origen: str, destino: str,
             cuando: str = "*", prioridad: int = 100,
             transformar: str = "") -> None:
        self.rutas.append(Ruta(ruta_id, origen, destino, cuando,
                               prioridad, True, transformar))
        self.rutas.sort(key=lambda r: r.prioridad)

    def _resolver(self, m: Mensaje) -> list[NodoRed]:
        """origen+tipo → rutas → nodos destino sanos y compatibles."""
        destinos: list[NodoRed] = []
        for r in self.rutas:
            if not r.activa:
                continue
            if not fnmatch.fnmatch(m.origen, r.origen):
                continue
            if not fnmatch.fnmatch(m.tipo, r.cuando):
                continue
            for nid, nodo in self.nodos.items():
                if (fnmatch.fnmatch(nid, r.destino) and nodo.sano
                        and nodo.direccion in ("entrada", "bidireccional")
                        and nodo not in destinos):
                    destinos.append(nodo)
        return destinos

    # ── ENVÍO: 1 mensaje → la red decide por las rutas declaradas ──
    async def enviar(self, m: Mensaje,
                     modo: str = "primero") -> dict:
        """modo: primero (failover) | todos (broadcast) | espejo (paralelo,
        gana el primero DONE)."""
        if not m.task_id:
            return {"status": "FAIL", "error": "task_id_obligatorio"}
        destinos = self._resolver(m)
        if not destinos:
            self._ev("red.sin_ruta", {"tipo": m.tipo, "origen": m.origen})
            return {"status": "FAIL", "error": f"sin_ruta:{m.origen}->{m.tipo}"}
        self._ev("red.envio", {"tipo": m.tipo, "origen": m.origen,
                               "destinos": [d.nodo_id for d in destinos],
                               "trace_id": m.trace_id})
        payload = {**m.payload, "task_id": m.task_id, "trace_id": m.trace_id}

        if modo == "todos":
            res = await asyncio.gather(
                *[self._enviar_a(d, payload) for d in destinos])
            return {"status": "DONE", "resultados": dict(
                zip([d.nodo_id for d in destinos], res))}

        if modo == "espejo":
            tareas = [asyncio.create_task(self._enviar_a(d, payload))
                      for d in destinos]
            for fut in asyncio.as_completed(tareas):
                r = await fut
                if r.get("status") == "DONE":
                    for t in tareas:
                        t.cancel()
                    return r
            return {"status": "FAIL", "error": "espejo_todos_fallaron"}

        for d in destinos:                        # modo "primero": failover
            r = await self._enviar_a(d, payload)
            if r.get("status") == "DONE":
                return {**r, "via": d.nodo_id}
        return {"status": "FAIL", "error": "todos_los_destinos_fallaron"}

    async def _enviar_a(self, nodo: NodoRed, payload: dict) -> dict:
        try:
            r = await nodo.conector.enviar(dict(payload))
            if r.get("status") == "DONE":
                nodo.fallos = 0
                return r
            raise RuntimeError(r.get("error", "fallo"))
        except Exception as exc:                   # noqa: BLE001
            nodo.fallos += 1
            if nodo.fallos >= self.MAX_FALLOS_NODO:
                nodo.sano = False
                self._ev("red.nodo_enfermo", {"nodo": nodo.nodo_id})
            return {"status": "FAIL", "error": str(exc),
                    "nodo": nodo.nodo_id}

    # ── SALUD + MAPA ──
    async def sondeo_loop(self, interval_s: int = 30) -> None:
        while True:
            await asyncio.sleep(interval_s)
            for n in self.nodos.values():
                try:
                    ok = await asyncio.wait_for(n.conector.sondear(), 10)
                    if ok and not n.sano:
                        n.sano, n.fallos = True, 0    # HALF_OPEN → CLOSED
                    elif not ok:
                        n.sano = False
                except Exception:                  # noqa: BLE001
                    n.sano = False

    def mapa(self) -> dict:
        """Foto de la red: para Studio/Telegram/atlas."""
        return {"nodos": {nid: {"sano": n.sano, "nivel": n.nivel,
                                "dir": n.direccion,
                                "dt_in": datatype_de(
                                    n.contrato["contrato"].get("consume")),
                                "dt_out": datatype_de(
                                    n.contrato["contrato"].get("expone"))}
                          for nid, n in self.nodos.items()},
                "rutas": [f"{r.origen} --[{r.cuando}]--> {r.destino}"
                          for r in self.rutas if r.activa]}

    def _ev(self, tipo: str, datos: dict) -> None:
        if self.audit:
            self.audit.evento(tipo, datos)
```

---

## EJEMPLO DE RED COMPLETA (declarativa, 12 líneas)
```python
red = RedUniversal(audit=audit_bus)
red.conectar("core.orquestador", ConectorInterno("orq", kernel_handler), C_ORQ, nivel="igual")
red.conectar("core.team.a1", ConectorInterno("t1", team.procesar_dict), C_TEAM, nivel="abajo")
red.conectar("ai.llm.openrouter", ConectorHTTP("or", "https://openrouter.ai/api/v1", {"Authorization": "OPENROUTER_KEY"}), C_LLM)
red.conectar("repo.github.jarvis", ConectorGitHub("gh", "maxbry123-commits/jarvis---core"), C_GH)
red.conectar("infra.vps.railway", ConectorVPS("vps", "https://web-production-eda5c.up.railway.app"), C_VPS)
red.conectar("mem.estado", ConectorMemoria("mem", estado), C_MEM)
red.conectar("notif.telegram", ConectorWebhook("tg", "TELEGRAM_WEBHOOK_URL"), C_TG)

red.ruta("R1", "core.orquestador", "core.team.*", cuando="tarea.*")      # orq → teams
red.ruta("R2", "core.team.*", "repo.github.*", cuando="codigo.commit")   # team → GitHub
red.ruta("R3", "*", "notif.telegram", cuando="*.escalate", prioridad=1)  # todo escalado → Telegram
red.ruta("R4", "core.*", "mem.estado", cuando="memoria.*")               # memoria como nodo más
```

## NOTAS
1. **Todo es un Conector**: MCP, GitHub, VPS, memoria, el propio orquestador — misma interfaz, la red no distingue. Añadir un tipo nuevo = 1 dataclass.
2. **1000 destinos**: namespaces `a.b.c` + patrones fnmatch en rutas (`ai.llm.*`) → escalas sin tocar código.
3. **Jerarquía arriba/abajo**: `nivel` permite orquestadores padre sobre MAXBRY o enjambres debajo — la misma red rutea ambas direcciones.
4. **3 modos de envío**: primero (failover), todos (broadcast), espejo (paralelo, gana el más rápido).
5. **Enchufe obligatorio**: sin contrato v1.5 válido no hay conexión. Secretos solo env.

## TESTS
```
test_conectar_sin_contrato_falla · test_ruta_patron_fnmatch · test_failover_primero
test_espejo_gana_mas_rapido · test_nodo_enfermo_a_los_5 · test_task_id_obligatorio
test_mapa_render · test_jerarquia_arriba_abajo
```
