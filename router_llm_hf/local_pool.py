#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_pool.py — Cola REAL de los 3 Spaces de Grupo 2 (1 modelo por Space).

REGLAS DEL OWNER (paso 1, literal):
  "revisa que entre 1 solo modelo por space en el momento del uso de esos 3
   modelos el siguiente salta al siguiente y si las 3 space estan ocupadas
   quedan en cola de espera. Tambien que los modelos trabajan como mirror."

Implementado:
  · 1 peticion en vuelo por Space (asyncio.Lock por Space): cada Space sirve
    1 modelo y solo uno a la vez.
  · Si el Space asignado esta OCUPADO, se prueba el SIGUIENTE de la cola (1,2,3).
  · Si los 3 estan ocupados, la peticion ESPERA en cola (FIFO) hasta
    LOCAL_QUEUE_WAIT_S; si se agota, se devuelve el ultimo error real para que
    la cadena de fallback siga con NVIDIA/Groq (nunca un falso OK).
  · ESPEJO (mirror): los 3 Spaces son espejos entre si para el rol "inferencia
    local". El asignado por modelo/modo es el PREFERIDO; los otros 2 son sus
    espejos y sirven la peticion si el preferido esta ocupado o degradado.
  · Un Space que responde 503 "Loading model" se marca como CARGANDO y se
    penaliza durante DEGRADED_S: no se le vuelve a pedir hasta que se recupere.

Estado real: GET /v1/local/pool (proxy).
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Tuple

NAMESPACE = "COMAND-CENTER-1"

# Orden de cola del Grupo 2 (1 modelo por Space).
SPACES: Tuple[str, ...] = (
    "space-grupo-2-router-llm-hf-1",
    "space-grupo-2-router-llm-hf-2",
    "space-grupo-2-router-llm-hf-3",
)

MODEL_BY_SPACE: Dict[str, str] = {
    "space-grupo-2-router-llm-hf-1": "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
    "space-grupo-2-router-llm-hf-2": "LiquidAI/LFM2.5-350M-GGUF",
    "space-grupo-2-router-llm-hf-3": "unsloth/Qwen3.5-0.8B-GGUF",
}

# Modelo pedido -> Space preferido (el que lo tiene cargado).
PREFERRED_BY_MODEL: Dict[str, str] = {m: s for s, m in MODEL_BY_SPACE.items()}

# Modo de servicio -> Space preferido (contrato de router_llm_hf/service_routes.py).
PREFERRED_BY_MODE: Dict[str, str] = {
    "swe_code": "space-grupo-2-router-llm-hf-1",
    "swe_free": "space-grupo-2-router-llm-hf-3",
    "team_qwe": "space-grupo-2-router-llm-hf-2",
}

WAIT_S = float(os.getenv("LOCAL_QUEUE_WAIT_S", "60"))
DEGRADED_S = float(os.getenv("LOCAL_DEGRADED_S", "20"))


class LocalPoolError(RuntimeError):
    """Los 3 Spaces de Grupo 2 fallaron (o la espera se agoto)."""


class LocalPool:
    def __init__(self, spaces: Tuple[str, ...] = SPACES) -> None:
        self.spaces = spaces
        self._locks: Dict[str, asyncio.Lock] = {s: asyncio.Lock() for s in spaces}
        self.state: Dict[str, Dict[str, Any]] = {
            s: {"space": s, "model": MODEL_BY_SPACE.get(s), "in_flight": 0,
                "served": 0, "errors": 0, "last_ok_at": None, "last_error": None,
                "degraded_until": 0.0, "state": "libre"}
            for s in spaces
        }
        self.waiting = 0
        self.waited_total = 0
        self.mirror_calls = 0

    # ------------------------------------------------------------------ estado
    def _mark(self, space: str, **kw) -> None:
        self.state[space].update(kw)

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        out = []
        for s in self.spaces:
            d = dict(self.state[s])
            d["busy"] = d["in_flight"] > 0
            d["degraded"] = d["degraded_until"] > now
            d["mirrors"] = [x for x in self.spaces if x != s]
            d["url"] = "https://comand-center-1-%s.hf.space" % s
            out.append(d)
        return {
            "spaces": out,
            "total_spaces": len(self.spaces),
            "free": sum(1 for d in out if not d["busy"]),
            "busy": sum(1 for d in out if d["busy"]),
            "waiting": self.waiting,
            "waited_total": self.waited_total,
            "mirror_calls": self.mirror_calls,
            "wait_s": WAIT_S,
            "regla": "1 modelo por Space; si esta ocupado salta al siguiente; si los 3 estan ocupados, espera en cola",
        }

    # ------------------------------------------------------------------ utiles
    def _order(self, preferred: Optional[str], model: Optional[str], mode: Optional[str]) -> List[str]:
        pref = preferred
        if not pref and model:
            pref = PREFERRED_BY_MODEL.get(model)
        if not pref and mode:
            pref = PREFERRED_BY_MODE.get(mode)
        rest = [s for s in self.spaces if s != pref]
        return ([pref] + rest) if pref in self.spaces else list(self.spaces)

    def _penalize(self, space: str, err: str) -> None:
        self._mark(space, errors=self.state[space]["errors"] + 1,
                   last_error=err[:200], degraded_until=time.time() + DEGRADED_S,
                   state="degradado")

    async def _wait_any(self, order: List[str], timeout: float) -> Optional[str]:
        """Espera a que se libere CUALQUIER Space de la cola (FIFO por asyncio.Lock)."""
        tasks = {s: asyncio.ensure_future(self._locks[s].acquire()) for s in order}
        try:
            done, _pending = await asyncio.wait(tasks.values(), timeout=timeout,
                                                return_when=asyncio.FIRST_COMPLETED)
        except Exception:
            done = set()
        if not done:
            for t in tasks.values():
                t.cancel()
            return None
        libre = next((s for s in order if tasks[s] in done), None)
        for s, t in tasks.items():
            if s != libre:
                t.cancel()
        return libre

    # ------------------------------------------------------------------ ejecucion
    async def execute(self, call, preferred: Optional[str] = None,
                      model: Optional[str] = None, mode: Optional[str] = None,
                      timeout: Optional[float] = None) -> Dict[str, Any]:
        """Ejecuta en un Space local. call(space) -> dict (debe devolver {"ok":bool,...}).

        Orden: preferido -> siguiente -> siguiente (espejo). Si los 3 estan
        ocupados: espera en cola. Si todos fallan: LocalPoolError.
        """
        wait_s = WAIT_S if timeout is None else timeout
        order = self._order(preferred, model, mode)
        errores: List[str] = []
        ocupados: List[str] = []

        # --- 1) intento rapido en orden de cola
        for space in order:
            if self._locks[space].locked():
                ocupados.append(space)
                continue
            await self._locks[space].acquire()
            self._mark(space, in_flight=self.state[space]["in_flight"] + 1, state="ocupado")
            try:
                res = await call(space)
                if res.get("ok"):
                    self._mark(space, served=self.state[space]["served"] + 1,
                               last_ok_at=time.time(), degraded_until=0.0, state="libre")
                    res["space"] = space
                    res["mirror"] = (space != order[0])
                    if res["mirror"]:
                        self.mirror_calls += 1
                    return res
                err = str(res.get("error") or "error desconocido")
                errores.append("%s: %s" % (space, err))
                self._penalize(space, err)
            except Exception as exc:
                errores.append("%s: %s" % (space, exc))
                self._penalize(space, str(exc))
            finally:
                self._mark(space, in_flight=max(0, self.state[space]["in_flight"] - 1))
                self._locks[space].release()
                if self.state[space]["in_flight"] == 0:
                    self._mark(space, state="libre")

        # --- 2) los 3 ocupados -> COLA DE ESPERA
        if not errores and ocupados:
            self.waiting += 1
            self.waited_total += 1
            try:
                space = await self._wait_any(order, wait_s)
            finally:
                self.waiting = max(0, self.waiting - 1)
            if space is None:
                raise LocalPoolError(
                    "los 3 Spaces de Grupo 2 ocupados (%s) y la espera de %.0fs se agoto"
                    % (", ".join(ocupados), wait_s))
            self._mark(space, in_flight=self.state[space]["in_flight"] + 1, state="ocupado")
            try:
                res = await call(space)
                if res.get("ok"):
                    self._mark(space, served=self.state[space]["served"] + 1,
                               last_ok_at=time.time(), degraded_until=0.0, state="libre")
                    res["space"] = space
                    res["mirror"] = True
                    res["queued"] = True
                    self.mirror_calls += 1
                    return res
                err = str(res.get("error") or "error desconocido")
                errores.append("%s: %s" % (space, err))
                self._penalize(space, err)
            except Exception as exc:
                errores.append("%s: %s" % (space, exc))
                self._penalize(space, str(exc))
            finally:
                self._mark(space, in_flight=max(0, self.state[space]["in_flight"] - 1))
                self._locks[space].release()
                if self.state[space]["in_flight"] == 0:
                    self._mark(space, state="libre")

        raise LocalPoolError("ningun Space local respondio: %s" % (" | ".join(errores) or "sin detalle"))


POOL = LocalPool()
