"""Conexion universal (Director 2026-10-03): un token por agente/instancia, sin cablear nada.

- Un token ("riu_...") sirve igual por HTTP (/v1/router, /memoria, /espacio, /secciones, /terminal...) y por MCP (/mcp/).
- El registro vive en el banco: router-inteligente-universal/banco/tokens.json, SOLO huellas sha256 (nunca el token).
  El token se entrega una sola vez al crearlo. Pensado para 10.000+ tokens: buscar uno es O(1).
- Cada token tiene: nombre (instancia/agente), permisos, limite por minuto, ficha amarrada opcional, activo.
  Permisos: chat, memoria, almacenamiento, fichas (por defecto) + computo, terminal (solo si el Director los da).
- Crear, apagar, encender y listar tokens exige la clave del Director (candado.py).
- Cada token tiene su propio almacenamiento (/espacio) y su propia memoria (scope por dueno): nadie pisa a nadie.
- /terminal reemplaza a SSH (HF Jobs no aceptan SSH): ejecuta comandos en un procesador HF pagado con el mismo token.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import os
import re
import secrets
import threading
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import rutas

log = logging.getLogger("riu")
PREFIX = "riu_"
PERMISOS = ("chat", "memoria", "almacenamiento", "fichas", "computo", "terminal")
PERMISOS_BASE = ["chat", "memoria", "almacenamiento", "fichas"]
RPM_BASE = int(os.getenv("RIU_TOKEN_RPM", "600"))
REFRESH_S = float(os.getenv("RIU_TOKENS_REFRESH_S", "60"))
NOMBRE_RE = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}(/[A-Za-z0-9][A-Za-z0-9._-]{0,63}){0,2}$"
MAX_ESPACIO = int(os.getenv("RIU_ESPACIO_MAX_BYTES", str(20 * 1024 * 1024)))


def huella(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hf_token() -> str:
    return os.getenv("HF_TOKEN") or os.getenv("HF_CONTROL_JOBS_TOKEN") or ""


def _fs():
    from huggingface_hub import HfFileSystem

    return HfFileSystem(token=_hf_token(), skip_instance_cache=True)


class Registro:
    """Cache en memoria del archivo de tokens; se relee solo cada REFRESH_S (tokens nuevos sin reiniciar)."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.data: dict[str, dict[str, Any]] = {}
        self.loaded_at = 0.0
        self.error: str | None = None
        self._ventanas: dict[str, list[float]] = {}  # nombre -> [inicio_minuto, llamadas]

    # ---- archivo en el banco
    def cargar(self) -> None:
        if not _hf_token():
            return
        try:
            raw = json.loads(_fs().cat_file(rutas.full(rutas.TOKENS)))
            with self.lock:
                self.data = dict(raw.get("tokens") or {})
                self.loaded_at = time.time()
                self.error = None
        except FileNotFoundError:
            with self.lock:
                self.loaded_at = time.time()
        except Exception as exc:  # noqa: BLE001 - keep the last good copy
            self.error = type(exc).__name__

    def guardar(self) -> None:
        with self.lock:
            body = {"version": 1, "actualizado": time.time(), "nota": "solo huellas sha256; los tokens no se guardan",
                    "tokens": self.data}
        _fs().pipe_file(rutas.full(rutas.TOKENS), json.dumps(body, ensure_ascii=False).encode())

    def bucle(self) -> None:
        while True:
            self.cargar()
            time.sleep(REFRESH_S)

    # ---- uso
    def buscar(self, candidato: str | None) -> dict[str, Any] | None:
        if not candidato or not candidato.startswith(PREFIX):
            return None
        if not self.loaded_at:
            self.cargar()
        rec = self.data.get(huella(candidato))
        return rec if rec and rec.get("activo", True) else None

    def por_nombre(self, nombre: str) -> tuple[str, dict[str, Any]] | None:
        with self.lock:
            for h, rec in self.data.items():
                if rec.get("nombre") == nombre:
                    return h, rec
        return None

    def permitir(self, rec: dict[str, Any]) -> bool:
        """Limite por minuto de cada token: un agente ruidoso no le quita turno a los demas."""
        limite = int(rec.get("limite_rpm") or RPM_BASE)
        now = time.time()
        with self.lock:
            w = self._ventanas.setdefault(rec["nombre"], [now, 0])
            if now - w[0] >= 60:
                w[0], w[1] = now, 0
            w[1] += 1
            return w[1] <= limite


REGISTRO = Registro()
_TERMINALES: dict[str, str] = {}  # job_id -> dueno (cada quien ve solo sus terminales)


def iniciar() -> None:
    threading.Thread(target=REGISTRO.bucle, name="riu-tokens", daemon=True).start()


def dueno(rec: dict[str, Any]) -> str:
    return "tok:" + rec["nombre"]


def registro_de_dueno(owner: str) -> dict[str, Any] | None:
    if not owner.startswith("tok:"):
        return None
    found = REGISTRO.por_nombre(owner[4:])
    return found[1] if found else None


def permitido(rec: dict[str, Any], patrones: list[str] | None) -> bool:
    pats = patrones or ["*"]
    return any(fnmatch.fnmatch(rec["nombre"], p) for p in pats)


# ------------------------------------------------------------------ rutas
class CrearReq(BaseModel):
    instancia: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    nombre: str | None = Field(default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")  # agente (cantidad=1)
    prefijo: str = Field(default="agente", pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,40}$")  # cantidad>1: agente-00001..
    cantidad: int = Field(default=1, ge=1, le=10000)
    permisos: list[str] = Field(default_factory=lambda: list(PERMISOS_BASE))
    limite_rpm: int = Field(default=RPM_BASE, ge=1, le=100000)
    ficha: str | None = Field(default=None, max_length=80)  # seccion amarrada: todo su chat pasa por esa ficha
    nota: str = Field(default="", max_length=300)


class TerminalReq(BaseModel):
    comando: str = Field(min_length=1, max_length=20000)
    imagen: str = Field(default="python:3.12", max_length=200)
    flavor: str = Field(default="cpu-basic", max_length=40)
    timeout: str = Field(default="30m", pattern=r"^\d+[smh]$")


def _seguro(owner: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", owner)[:120]


def _ruta_espacio(owner: str, ruta: str) -> str:
    ruta = ruta.strip("/")
    if not ruta or ".." in ruta.split("/") or len(ruta) > 300:
        raise HTTPException(status_code=400, detail="RUTA_INVALIDA")
    return rutas.full(f"{rutas.ESPACIOS}/{_seguro(owner)}/{ruta}")


def build_tokens_router(auth: Any) -> APIRouter:
    r = APIRouter()

    @r.post("/tokens")  # candado: clave del Director
    def crear(req: CrearReq) -> dict[str, Any]:
        malos = [p for p in req.permisos if p not in PERMISOS]
        if malos:
            raise HTTPException(status_code=422, detail=f"PERMISO_DESCONOCIDO:{malos}")
        REGISTRO.cargar()
        nombres = ([f"{req.instancia}/{req.nombre or req.prefijo}"] if req.cantidad == 1
                   else [f"{req.instancia}/{req.prefijo}-{i:05d}" for i in range(1, req.cantidad + 1)])
        existentes = {rec.get("nombre") for rec in REGISTRO.data.values()}
        repetidos = [n for n in nombres if n in existentes]
        if repetidos:
            raise HTTPException(status_code=409, detail=f"NOMBRE_YA_EXISTE:{repetidos[:5]}")
        salida, now = [], time.time()
        with REGISTRO.lock:
            for n in nombres:
                tok = PREFIX + secrets.token_urlsafe(30)
                REGISTRO.data[huella(tok)] = {"nombre": n, "instancia": req.instancia, "permisos": sorted(set(req.permisos)),
                                              "limite_rpm": req.limite_rpm, "ficha": req.ficha, "activo": True,
                                              "creado": now, "nota": req.nota}
                salida.append({"nombre": n, "token": tok})
        REGISTRO.guardar()
        return {"creados": len(salida), "aviso": "Guarda estos tokens ahora: el Router solo guarda su huella.", "tokens": salida}

    @r.get("/tokens")  # candado
    def listar(instancia: str | None = None) -> dict[str, Any]:
        rows = [{k: v for k, v in rec.items()} for rec in REGISTRO.data.values()
                if not instancia or rec.get("instancia") == instancia]
        return {"total": len(rows), "tokens": sorted(rows, key=lambda x: x["nombre"])[:10000]}

    def _cambiar(nombre: str, **campos: Any) -> dict[str, Any]:
        REGISTRO.cargar()
        found = REGISTRO.por_nombre(nombre)
        if not found:
            raise HTTPException(status_code=404, detail="TOKEN_NO_EXISTE")
        with REGISTRO.lock:
            found[1].update(campos)
        REGISTRO.guardar()
        return found[1]

    @r.post("/tokens/apagar/{nombre:path}")  # candado
    def apagar(nombre: str) -> dict[str, Any]:
        return _cambiar(nombre, activo=False, apagado=time.time())

    @r.post("/tokens/encender/{nombre:path}")  # candado
    def encender(nombre: str) -> dict[str, Any]:
        return _cambiar(nombre, activo=True)

    @r.post("/tokens/ficha/{nombre:path}")  # candado: amarrar/soltar una ficha
    def amarrar(nombre: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return _cambiar(nombre, ficha=(body or {}).get("ficha"))

    @r.get("/tokens/yo")
    def yo(owner: str = Depends(auth)) -> dict[str, Any]:
        rec = registro_de_dueno(owner)
        if rec:
            return {"dueno": owner, **rec}
        return {"dueno": owner, "tipo": "clave maestra (sin computo ni terminal salvo con clave del Director)"}

    # ---- almacenamiento propio de cada token
    @r.put("/espacio/{ruta:path}")
    async def espacio_put(ruta: str, request: Request, owner: str = Depends(auth)) -> dict[str, Any]:
        body = await request.body()
        if len(body) > MAX_ESPACIO:
            raise HTTPException(status_code=413, detail="ARCHIVO_DEMASIADO_GRANDE")
        path = _ruta_espacio(owner, ruta)
        import asyncio

        await asyncio.to_thread(_fs().pipe_file, path, body)
        return {"guardado": ruta.strip("/"), "bytes": len(body), "dueno": owner}

    @r.get("/espacio")
    def espacio_list(owner: str = Depends(auth)) -> dict[str, Any]:
        base = rutas.full(f"{rutas.ESPACIOS}/{_seguro(owner)}")
        try:
            files = sorted(p[len(base) + 1:] for p in _fs().find(base))
        except Exception:  # noqa: BLE001
            files = []
        return {"dueno": owner, "archivos": files[:5000]}

    @r.get("/espacio/{ruta:path}")
    def espacio_get(ruta: str, owner: str = Depends(auth)) -> Response:
        try:
            data = _fs().cat_file(_ruta_espacio(owner, ruta))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="NO_EXISTE") from exc
        return Response(content=data, media_type="application/octet-stream")

    @r.delete("/espacio/{ruta:path}")
    def espacio_del(ruta: str, owner: str = Depends(auth)) -> dict[str, Any]:
        try:
            _fs().rm(_ruta_espacio(owner, ruta))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="NO_EXISTE") from exc
        return {"borrado": ruta.strip("/")}

    # ---- terminal remota (reemplazo de SSH): permiso "terminal" o clave del Director
    @r.post("/terminal/run")
    def terminal_run(req: TerminalReq, owner: str = Depends(auth)) -> dict[str, Any]:
        from .control_plane import HF_NS, _api, _check_flavor

        _check_flavor(req.flavor)
        job = _api().run_job(namespace=HF_NS, image=req.imagen, command=["bash", "-lc", req.comando], flavor=req.flavor,
                             timeout=req.timeout)
        _TERMINALES[job.id] = owner
        return {"job_id": job.id, "flavor": req.flavor, "ver": f"/terminal/{job.id}?logs=60"}

    @r.get("/terminal/{job_id}")
    def terminal_ver(job_id: str, request: Request, logs: int = 60, owner: str = Depends(auth)) -> dict[str, Any]:
        from . import director
        from .control_plane import HF_NS, _api, job_log_tail

        if _TERMINALES.get(job_id) != owner and not director.verify(request.headers.get(director.HEADER)):
            raise HTTPException(status_code=403, detail="TERMINAL_DE_OTRO_DUENO")
        j = _api().inspect_job(namespace=HF_NS, job_id=job_id)
        return {"job_id": job_id, "stage": str(getattr(j.status, "stage", "")), "logs": job_log_tail(job_id, max(1, min(logs, 400)))}

    return r
