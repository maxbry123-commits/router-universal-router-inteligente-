"""/memoria del chat (contrato de chat-ancla.js): historial y pestañas por scope, un JSON por scope en el bucket HF.
save {scope,key,data} -> registro con id creciente; load {scope,key} -> {records}; search {scope} -> {results:{sqlite}}."""
import asyncio
import json
import re
import time
from fastapi import Depends, HTTPException, Query
from mvp import hf_store

CACHE, CANDADOS = {}, {}  # scope -> lista de registros {id,key,data}; un candado por scope (escrituras en orden)
TOPE = 900_000  # bytes por scope (hf_store admite 1 MB): se descartan los registros más viejos


def _nombre(scope):
    if not isinstance(scope, str) or not scope.strip() or len(scope) > 120:
        raise HTTPException(status_code=400, detail="scope invalido")
    return "memoria/" + re.sub(r"[^A-Za-z0-9_-]", "_", scope) + ".json"


def _limpio(data):  # hf_store rechaza credenciales: se ocultan para que la cola del navegador no se atasque
    return json.loads(hf_store.PATRON_CLAVE.sub("[CLAVE OCULTA]", json.dumps(data, ensure_ascii=False)))


async def _cargar(clave, scope):
    if scope not in CACHE:
        try: CACHE[scope] = json.loads((await asyncio.to_thread(hf_store.leer, clave, _nombre(scope)))["valor"])
        except hf_store.NoExiste: CACHE[scope] = []  # scope nuevo
        except RuntimeError as error: raise HTTPException(status_code=502, detail=str(error)) from None  # no se cachea vacío: guardar encima borraría el historial
        while len(CACHE) > 50: CACHE.pop(next(iter(CACHE)))  # tope de memoria: los scopes más viejos se releen del bucket
    return CACHE[scope]


def _recortar(registros):
    while len(registros) > 1 and len(json.dumps(registros, ensure_ascii=False).encode("utf-8")) > TOPE:
        registros.pop(0)
    return registros


def rutas(app, verificar, credencial):
    @app.post("/memoria/save", dependencies=[Depends(verificar)])
    async def guardar(cuerpo: dict):
        scope, key = cuerpo.get("scope"), cuerpo.get("key")
        nombre = _nombre(scope)
        if not isinstance(key, str) or not key or len(key) > 200:
            raise HTTPException(status_code=400, detail="key invalida")
        clave = credencial()
        async with CANDADOS.setdefault(scope, asyncio.Lock()):
            registros = await _cargar(clave, scope)
            nuevo = {"id": max([r["id"] for r in registros] + [time.time_ns() // 1000]) + 1, "key": key, "data": _limpio(cuerpo.get("data"))}
            registros[:] = _recortar([r for r in registros if r["key"] != key] + [nuevo])
            try: await asyncio.to_thread(hf_store.guardar, clave, nombre, json.dumps(registros, ensure_ascii=False))
            except (ValueError, RuntimeError) as error: CACHE.pop(scope, None); raise HTTPException(status_code=502, detail=str(error)) from None
        return {"ok": True, "id": nuevo["id"]}

    @app.get("/memoria/load", dependencies=[Depends(verificar)])
    async def cargar(scope: str = Query(""), key: str = Query("")):
        _nombre(scope)
        return {"records": [r for r in await _cargar(credencial(), scope) if r["key"] == key]}

    @app.get("/memoria/search", dependencies=[Depends(verificar)])
    async def buscar(scope: str = Query(""), query: str = Query(""), k: int = Query(500)):
        _nombre(scope)
        rs = [r for r in await _cargar(credencial(), scope) if not query or query.lower() in json.dumps(r["data"], ensure_ascii=False).lower()]
        return {"results": {"sqlite": rs[-max(1, min(k, 100000)):]}}
