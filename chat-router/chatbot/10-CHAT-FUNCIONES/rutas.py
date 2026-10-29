"""Rutas FastAPI de las funciones del chat."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter,FastAPI,HTTPException
try:
 from . import action_registry,council,rewind,compact,archify_cmd,work
except ImportError:
 import action_registry,council,rewind,compact,archify_cmd,work

def build_router()->FastAPI:
    app=FastAPI(title="YAIWES Chat Functions")
    @app.post("/acciones/{action_id}")
    def accion(action_id:str,payload:dict):
        try:return action_registry.ejecutar(action_id,payload)
        except KeyError as e:raise HTTPException(404,str(e))
    @app.post("/council")
    async def council_route(payload:dict):return await council.ask_council(str(payload.get("pregunta","")),int(payload.get("modelos",3)))
    @app.post("/rewind")
    def rewind_route(payload:dict):return {"estado":rewind.volver(str(payload["conv_id"]),int(payload.get("pasos",1)))}
    @app.post("/compact")
    def compact_route(payload:dict):return compact.compactar(payload.get("historial",[]))
    @app.post("/archify")
    def archify_route(payload:dict):return {"mermaid":archify_cmd.archify(str(payload.get("texto","")))}
    @app.get("/work")
    def work_get():return work.listar()
    @app.post("/work")
    def work_post(payload:dict):
        job_id=str(payload["id"]); op=payload.get("op","crear")
        if op=="crear":return work.crear(job_id)
        if op=="pausar":return work.pausar(job_id)
        if op=="cancelar":return work.cancelar(job_id)
        if op=="reintentar":return work.reintentar(job_id)
        if op=="aprobar":return work.aprobar(job_id)
        raise HTTPException(400,"op inválida")
    return app
