"""Puertos. En producción NO usar InlineQueue/DemoMemory/DemoModel; conectar EXISTENTES."""
from __future__ import annotations
import asyncio, json
from pathlib import Path
from typing import Any
from .contracts import NCTError,stable_hash

class MissingPort:
    def __getattr__(self,name):
        raise NCTError('Puerto existente NO CONECTADO: '+name)

class InlineQueueDemo:
    """Solo pruebas locales; invoca callback una vez, NO agenda, NO es cola persistente."""
    async def submit_and_wait(self,task,perform):
        return await perform()

class DemoMemory:
    """Solo pruebas aisladas, memoria volátil; NUNCA instalar como memoria nueva."""
    def __init__(self):self.data={}
    async def load(self,key):return self.data.get(key)
    async def checkpoint(self,key,value):self.data[key]=json.loads(json.dumps(value))

class DemoModel:
    """Respuestas estáticas predecibles: NO simula inferencia real ni auditor independiente."""
    def __init__(self, proposals:dict):self.proposals=proposals;self.calls=[]
    async def invoke(self,block,payload):
        self.calls.append((block,payload['stage'],payload['task_id']))
        response={'status':'READY','notes':'Demo determinista (NO IA)'}
        if payload['stage']=='IMPLEMENT':
            proposal=self.proposals.get(payload['task_id'])
            if proposal is None:return {'status':'BLOCKED','reason':'Sin respuesta fixture'}
            response['proposal']=proposal
        return response

class ExistingMemoryHooks:
    """Wire sin persistencia propia: inyectar funciones REALES del storage/memoria existente."""
    def __init__(self,load_callback,save_callback):
        if not (callable(load_callback) and callable(save_callback)):
            raise NCTError('callbacks memoria ausentes')
        self._load=load_callback;self._save=save_callback
    async def load(self,key):return await self._load(key)
    async def checkpoint(self,key,data):await self._save(key,data)

class ExistingQueueHooks:
    def __init__(self,submit_wait_callback):
        if not callable(submit_wait_callback):raise NCTError('callback cola ausente')
        self._submit=submit_wait_callback
    async def submit_and_wait(self,task,perform):return await self._submit(task,perform)

class ExistingModelHooks:
    def __init__(self,invoke_callback):
        if not callable(invoke_callback):raise NCTError('callback modelos ausente')
        self._invoke=invoke_callback
    async def invoke(self,block,payload):return await self._invoke(block,payload)
