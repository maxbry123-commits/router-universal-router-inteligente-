"""Router FastAPI para funciones del chat."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from action_registry import ejecutar
from council import ask_council
from rewind import guardar, volver
from compact import compactar
from archify_cmd import archify
import work

class Payload(BaseModel):
    payload: dict = {}

class CouncilReq(BaseModel):
    pregunta: str
    modelos: int = 3

class RewindReq(BaseModel):
    conv_id: str
    estado: dict | None = None
    pasos: int = 1

class CompactReq(BaseModel):
    historial: list

class ArchifyReq(BaseModel):
    texto: str

class WorkReq(BaseModel):
    work_id: str
    action: str = "create"
    progress: int | None = None

def build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/acciones/{action_id}")
    def acciones_route(action_id: str, req: Payload):
        try:
            return ejecutar(action_id, req.payload)
        except (KeyError, ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.post("/council")
    async def council_route(req: CouncilReq):
        return await ask_council(req.pregunta, req.modelos)

    @router.post("/rewind")
    def rewind_route(req: RewindReq):
        try:
            if req.estado is not None:
                guardar(req.conv_id, req.estado)
                return {"status": "PASS", "saved": True}
            return {"status": "PASS", "estado": volver(req.conv_id, req.pasos)}
        except (ValueError, IndexError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.post("/compact")
    def compact_route(req: CompactReq):
        return compactar(req.historial)

    @router.post("/archify")
    def archify_route(req: ArchifyReq):
        return archify(req.texto)

    @router.get("/work")
    def work_get():
        return {"status": "PASS", "items": work.listar()}

    @router.post("/work")
    def work_post(req: WorkReq):
        try:
            if req.action == "create":
                return work.crear(req.work_id)
            if req.action == "pause":
                return work.pausar(req.work_id)
            if req.action == "cancel":
                return work.cancelar(req.work_id)
            if req.action == "retry":
                return work.reintentar(req.work_id)
            if req.action == "approve":
                return work.aprobar(req.work_id)
            if req.action == "progress" and req.progress is not None:
                return work.progreso(req.work_id, req.progress)
            raise ValueError("acción WORK inválida")
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    return router
