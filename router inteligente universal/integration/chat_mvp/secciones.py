"""Fichas como secciones vivas (Director 2026-10-03): una ficha = un archivo .json en router-inteligente-universal/fichas/.

El Router revisa la carpeta cada RIU_FICHAS_REFRESH_S (60 s). Cada ficha nueva aparece sola como seccion nueva:
  GET  /secciones                 lista (nombre, pasos, estado, error si la ficha esta mal escrita)
  GET  /secciones/_plantilla      la plantilla vacia para copiar
  GET  /secciones/{nombre}        la ficha
  POST /secciones/{nombre}/run    {"input": "..."} -> pasa por todos los pasos (permiso "fichas")
  POST /secciones                 subir/cambiar una ficha (clave del Director)
  DELETE /secciones/{nombre}      quitarla (clave del Director)
Un token amarrado a una ficha (tokens.ficha) hace que TODO su chat por /v1/router pase por esa ficha, sin cablear nada.
La composicion (que hace cada IA) la define el Director o sus agentes dentro de "pasos"; el Router solo la ejecuta.
Modos: cadena (cada paso recibe la salida del anterior), paralelo, consejo (todos + juez), unico.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import rutas

log = logging.getLogger("riu")
REFRESH_S = float(os.getenv("RIU_FICHAS_REFRESH_S", "60"))
MODOS = {"cadena": "queue", "paralelo": "parallel", "consejo": "council", "unico": "single"}

PLANTILLA: dict[str, Any] = {
    "nombre": "mi-ficha",
    "descripcion": "Que hace esta ficha (una frase).",
    "modo": "cadena",
    "anclaje_system_prompt": "Reglas que valen para TODOS los pasos (opcional).",
    "pasos": [
        {"nombre": "paso-1", "modelo": "auto", "system_prompt": "", "instruccion": "{input}", "max_tokens": 1024,
         "temperature": None, "dataset": None},
    ],
    "juez": None,
    "conectividad": {"tokens_permitidos": ["*"], "vias": ["http", "mcp"], "nota": "patrones de nombres de token: 'instancia-A/*'"},
    "notas": "",
    "_ayuda": {
        "modo": "cadena = cada paso recibe la salida del anterior | paralelo = todos a la vez | consejo = todos + juez | unico = solo el primero",
        "modelo": "auto | grupo (assistants, code...) | proveedor:modelo (nvidia:moonshotai/kimi-k3, groq:qwen/qwen3.8-27b, local:...)",
        "instruccion": "texto que recibe el modelo; {input} se reemplaza por la entrada o por la salida del paso anterior",
        "dataset": "opcional {'repo': 'COMAND-CENTER-1/mi-dataset', 'file': 'anclaje.md'}: texto de anclaje desde un dataset HF",
        "pasos": "de 1 a 20 pasos; el orden es el orden de ejecucion",
    },
}


def _slug(nombre: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", nombre.strip().lower()).strip("-")
    return s[:80]


class SubirReq(BaseModel):
    ficha: dict[str, Any] = Field(default_factory=dict)


def convertir(raw: dict[str, Any]):  # noqa: ANN201 - returns control_plane.Ficha
    """Ficha del Director (pasos) -> motor de fichas del Router. Lanza ValueError con el motivo."""
    from .control_plane import Ficha, Member

    modo = MODOS.get(str(raw.get("modo") or "cadena"))
    if not modo:
        raise ValueError(f"MODO_DESCONOCIDO: usa {sorted(MODOS)}")
    pasos = raw.get("pasos") or []
    if not pasos:
        raise ValueError("SIN_PASOS: agrega al menos un paso")

    def miembro(p: dict[str, Any]) -> Any:
        return Member(model=str(p.get("modelo") or "auto"), system_prompt=str(p.get("system_prompt") or ""),
                      template=str(p.get("instruccion") or "{input}"), dataset=p.get("dataset"),
                      max_tokens=int(p.get("max_tokens") or 1024), temperature=p.get("temperature"))

    juez = raw.get("juez")
    return Ficha(name=str(raw.get("nombre") or "ficha"), mode=modo, anchor_system_prompt=str(raw.get("anclaje_system_prompt") or ""),
                 members=[miembro(p) for p in pasos], judge=miembro(juez) if isinstance(juez, dict) else None,
                 notes=str(raw.get("notas") or ""))


class Secciones:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.items: dict[str, dict[str, Any]] = {}
        self.ultima = 0.0

    def _fs(self):  # noqa: ANN202
        from .tokens import _fs

        return _fs()

    def cargar(self) -> None:
        try:
            paths = [p for p in self._fs().ls(rutas.full(rutas.FICHAS), detail=False) if p.endswith(".json")]
        except FileNotFoundError:
            paths = []
        except Exception as exc:  # noqa: BLE001
            log.warning("fichas: listado fallo %s", type(exc).__name__)
            return
        nuevos: dict[str, dict[str, Any]] = {}
        for path in paths:
            archivo = path.rsplit("/", 1)[-1]
            if archivo.startswith("_"):
                continue  # _plantilla.json y similares no se montan
            item: dict[str, Any] = {"archivo": archivo, "ruta_almacenamiento": f"{rutas.FICHAS}/{archivo}"}
            try:
                raw = json.loads(self._fs().cat_file(path))
                nombre = _slug(str(raw.get("nombre") or archivo[:-5]))
                item.update(nombre=nombre, raw=raw, ficha=convertir(raw), estado="ok", error=None)
            except Exception as exc:  # noqa: BLE001 - a broken ficha is reported, never mounted
                nombre = _slug(archivo[:-5])
                item.update(nombre=nombre, raw=None, ficha=None, estado="error", error=str(exc)[:300])
            nuevos[nombre] = item
        with self.lock:
            antes = set(self.items)
            self.items = nuevos
            self.ultima = time.time()
        for nombre in set(nuevos) - antes:
            self._fables(nombre, nuevos[nombre])

    @staticmethod
    def _fables(nombre: str, item: dict[str, Any]) -> None:
        """Cada seccion nueva tambien queda enchufada en el enchufe universal Fables."""
        try:
            from .fables_adapter import FablesCatalog
            from .router import get_fables_catalog

            get_fables_catalog().register(FablesCatalog._ficha(f"yaiwes.seccion.{nombre.replace('-', '_')}", "tool",  # noqa: SLF001
                                                               item["ruta_almacenamiento"]))
        except Exception:  # noqa: BLE001 - already registered or catalog off
            pass

    def bucle(self) -> None:
        while True:
            self.cargar()
            time.sleep(REFRESH_S)

    def get(self, nombre: str) -> dict[str, Any] | None:
        with self.lock:
            return self.items.get(_slug(nombre))

    def publico(self, item: dict[str, Any]) -> dict[str, Any]:
        raw = item.get("raw") or {}
        return {"nombre": item["nombre"], "estado": item["estado"], "error": item.get("error"),
                "descripcion": raw.get("descripcion"), "modo": raw.get("modo"),
                "pasos": [p.get("nombre") for p in raw.get("pasos") or []],
                "conectividad": raw.get("conectividad"), "ruta": f"/secciones/{item['nombre']}/run",
                "archivo": item["ruta_almacenamiento"]}

    def lista(self) -> list[dict[str, Any]]:
        with self.lock:
            return [self.publico(i) for i in sorted(self.items.values(), key=lambda x: x["nombre"])]


SECCIONES = Secciones()


def iniciar() -> None:
    threading.Thread(target=SECCIONES.bucle, name="riu-secciones", daemon=True).start()


def ejecutar(nombre: str, texto: str, owner: str) -> dict[str, Any]:
    """Corre una seccion. Respeta conectividad.tokens_permitidos para los tokens."""
    from .control_plane import run_ficha
    from .tokens import permitido, registro_de_dueno

    item = SECCIONES.get(nombre)
    if not item:
        raise HTTPException(status_code=404, detail="SECCION_NO_EXISTE")
    if item["estado"] != "ok":
        raise HTTPException(status_code=409, detail=f"SECCION_CON_ERROR:{item['error']}")
    rec = registro_de_dueno(owner)
    patrones = ((item["raw"] or {}).get("conectividad") or {}).get("tokens_permitidos")
    if rec and not permitido(rec, patrones):
        raise HTTPException(status_code=403, detail="TOKEN_NO_PERMITIDO_EN_ESTA_SECCION")
    out = run_ficha(item["ficha"], texto)
    nombres = [p.get("nombre") for p in (item["raw"] or {}).get("pasos") or []]
    for i, step in enumerate(out["steps"]):
        step["paso"] = nombres[i] if i < len(nombres) else step.get("role", "juez")
    return {"seccion": item["nombre"], **out}


def build_secciones_router(auth: Any) -> APIRouter:
    r = APIRouter()

    @r.get("/secciones")
    def lista(_owner: str = Depends(auth)) -> dict[str, Any]:
        return {"carpeta": rutas.FICHAS, "revisada": SECCIONES.ultima, "secciones": SECCIONES.lista()}

    @r.get("/secciones/_plantilla")
    def plantilla(_owner: str = Depends(auth)) -> dict[str, Any]:
        return PLANTILLA

    @r.post("/secciones/recargar")
    def recargar(_owner: str = Depends(auth)) -> dict[str, Any]:
        SECCIONES.cargar()
        return {"secciones": SECCIONES.lista()}

    @r.get("/secciones/{nombre}")
    def una(nombre: str, _owner: str = Depends(auth)) -> dict[str, Any]:
        item = SECCIONES.get(nombre)
        if not item:
            raise HTTPException(status_code=404, detail="SECCION_NO_EXISTE")
        return {**SECCIONES.publico(item), "ficha": item.get("raw")}

    @r.post("/secciones/{nombre}/run")
    async def run(nombre: str, body: dict[str, Any], owner: str = Depends(auth)) -> dict[str, Any]:
        import asyncio

        texto = str(body.get("input") or "")
        if not texto:
            raise HTTPException(status_code=422, detail="FALTA_INPUT")
        return await asyncio.to_thread(ejecutar, nombre, texto, owner)

    @r.post("/secciones")  # candado: clave del Director
    def subir(req: SubirReq, _owner: str = Depends(auth)) -> dict[str, Any]:
        raw = req.ficha
        try:
            convertir(raw)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=f"FICHA_INVALIDA:{str(exc)[:300]}") from exc
        nombre = _slug(str(raw.get("nombre") or ""))
        if not nombre or nombre.startswith("_"):
            raise HTTPException(status_code=422, detail="FALTA_NOMBRE")
        SECCIONES._fs().pipe_file(rutas.full(f"{rutas.FICHAS}/{nombre}.json"),  # noqa: SLF001
                                  json.dumps(raw, ensure_ascii=False, indent=2).encode())
        SECCIONES.cargar()
        return {"seccion": SECCIONES.publico(SECCIONES.get(nombre) or {"nombre": nombre, "estado": "pendiente",
                                                                       "ruta_almacenamiento": ""})}

    @r.delete("/secciones/{nombre}")  # candado
    def quitar(nombre: str, _owner: str = Depends(auth)) -> dict[str, Any]:
        item = SECCIONES.get(nombre)
        if not item:
            raise HTTPException(status_code=404, detail="SECCION_NO_EXISTE")
        SECCIONES._fs().rm(rutas.full(item["ruta_almacenamiento"]))  # noqa: SLF001
        SECCIONES.cargar()
        return {"quitada": nombre}

    return r
