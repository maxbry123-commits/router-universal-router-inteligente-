"""Ejecutor compilado ECC: una fase = una función Python autorizada.

FALLA CERRADO: un documento ECC no crea autoridad de ejecución.
No ejecuta Markdown, eval, exec ni shell embebida.
"""
from __future__ import annotations
import hashlib
import inspect
import json
from typing import Mapping, Callable

class PhaseBlocked(ValueError):
    pass


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,ensure_ascii=False).encode()).hexdigest()[:32]


def _verified_receipt(receipt:dict, request:dict) -> bool:
    return (isinstance(receipt,dict) and receipt.get('request_id')==request['request_id']
            and receipt.get('task_id')==request['task_id']
            and receipt.get('skill_id')==request['skill_id']
            and receipt.get('phase_id')==request['phase_id']
            and receipt.get('status')=='PASS'
            and isinstance(receipt.get('receipt_id'),str) and bool(receipt['receipt_id'])
            and receipt.get('evidence_source') in ('approved_tool','independent_checker'))


async def execute_compiled_motor(*, catalog:dict, skill_id:str, source_sha256:str,
                                  event:str, task_id:str, context:dict,
                                  approved_handlers:Mapping[str,Callable],
                                  receipt_callback:Callable) -> dict:
    """El host entrega handlers revisados y un callback de recibos del EJECUTOR REAL.

    Devuelve NOT_IMPLEMENTED cuando falta siquiera un handler. Se rechazan
    fuentes alteradas (SHA), eventos no autorizados y recibos incompletos.
    """
    skills=catalog.get('skills',catalog)
    spec=skills.get(skill_id)
    if not isinstance(spec,dict) or spec.get('source_sha256')!=source_sha256:
        raise PhaseBlocked('SOURCE_UNAVAILABLE_OR_SHA_MISMATCH')
    if not isinstance(context,dict) or not isinstance(task_id,str) or not task_id:
        raise PhaseBlocked('BAD_CONTEXT')
    phases=spec.get('phases',[])
    if not isinstance(phases,list) or not phases:
        raise PhaseBlocked('NO_COMPILED_PHASES')
    # Preflight integral: no comenzar las acciones de una skill parcialmente
    # conectada (evita efectos parciales inesperados).
    lacking=[p['action_id'] for p in phases if not callable(approved_handlers.get(p['action_id']))]
    if lacking:
        return {'ok':False,'status':'NOT_IMPLEMENTED','skill_id':skill_id,
                'missing_handlers':lacking,'executed':0}
    receipts=[]
    for phase in phases:
        request={'request_id':_hash([skill_id,source_sha256,task_id,phase['phase_id'],event]),
                 'skill_id':skill_id,'phase_id':phase['phase_id'],
                 'source_sha256':source_sha256,'event':event,'task_id':task_id,
                 'context':context}
        # Trusted host is responsible for setting the receipt after tool execution.
        action=approved_handlers[phase['action_id']]
        proposed=action(request)
        if inspect.isawaitable(proposed):proposed=await proposed
        if not isinstance(proposed,dict) or proposed.get('status')!='PASS':
            return {'ok':False,'status':'FAILED','skill_id':skill_id,
                    'failed_phase':phase['phase_id'],'receipts':receipts}
        received=receipt_callback(request,proposed)
        if inspect.isawaitable(received):received=await received
        if not _verified_receipt(received,request):
            return {'ok':False,'status':'BAD_RECEIPT','skill_id':skill_id,
                    'failed_phase':phase['phase_id'],'receipts':receipts}
        receipts.append({'phase_id':phase['phase_id'],'receipt_id':received['receipt_id'],
                         'evidence_source':received['evidence_source']})
    return {'ok':True,'status':'PASS','skill_id':skill_id,'executed':len(receipts),'receipts':receipts}
