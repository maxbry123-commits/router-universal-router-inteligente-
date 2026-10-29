"""Pieza faltante: JSON de planificador Qwen -> DAG tipado Ricardo meta+ops.

NO reemplaza motor_cli.py ni las fichas existentes; se invoca DESPUÉS de que
el modelo haya devuelto una propuesta JSON, ANTES del intérprete real.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

class ModelPlanError(ValueError):pass

ARG_KEYS={
    'inspect_workspace':set(),
    'create_directory':{'path'},
    'write_text':{'path','text'},
    'read_text':{'path'},
    'verify_exists':{'path'},
    'verify_contains':{'path','text'},
    'finish':set(),
}
FORBIDDEN={'exec','eval','bash','shell','python_code','install_package','delete_recursive','modify_router','hf_job'}


def parse_planner_steps(response:dict, *, task_id:str, allowed_ops:set[str],
                        max_steps:int=32) -> dict:
    """Puente exacto al formato general de SYSTEM_QWEN_JSON_PROPUESTO.md."""
    if not isinstance(response,dict):raise ModelPlanError('Respuesta no es JSON objeto')
    if response.get('task_id')!=task_id:raise ModelPlanError('task_id incorrecto')
    if response.get('status')!='READY':raise ModelPlanError('READY requerido')
    if response.get('constraints_respected') is not True:
        raise ModelPlanError('Sin confirmación de restricciones')
    if set(response)-{'task_id','status','goal','steps','inputs_missing','expected_artifacts',
                       'evidence_required','constraints_respected'}:
        raise ModelPlanError('Campos adicionales prohibidos')
    steps=response.get('steps')
    if not isinstance(steps,list) or not 1<=len(steps)<=max_steps:
        raise ModelPlanError('Número de pasos fuera de límite')
    if response.get('inputs_missing'):raise ModelPlanError('Insumos críticos pendientes')
    ops=[]
    for step in steps:
        if not isinstance(step,dict):raise ModelPlanError('Paso no es objeto')
        if set(step)-{'id','tool','args','depends_on','checks'}:
            raise ModelPlanError('Campos desconocidos de step')
        uid=step.get('id')
        if not isinstance(uid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',uid):
            raise ModelPlanError('ID no válido')
        op=step.get('tool')
        if not isinstance(op,str) or op in FORBIDDEN or op not in allowed_ops:
            raise ModelPlanError('Operación no autorizada: '+str(op))
        args=step.get('args')
        if not isinstance(args,dict):raise ModelPlanError('args debe ser objeto')
        if op not in ARG_KEYS or set(args)-ARG_KEYS[op]:
            raise ModelPlanError('Argumentos de operación inválidos')
        if 'path' in ARG_KEYS[op] and (not isinstance(args.get('path'),str) or not args['path']):
            raise ModelPlanError('Ruta requerida')
        if 'text' in ARG_KEYS[op] and (not isinstance(args.get('text'),str) or len(args['text'])>10000):
            raise ModelPlanError('Texto requerido o muy grande')
        depends=step.get('depends_on',[])
        if not isinstance(depends,list) or any(not isinstance(x,str) for x in depends):
            raise ModelPlanError('depends_on inválido')
        checks=step.get('checks')
        if not isinstance(checks,list) or not checks:raise ModelPlanError('checks requeridas')
        # Todos los argumentos viajan tipados; no convertir contenido en Python libre.
        ops.append({'id':uid,'op':op,**args,'depends_on':depends})
    ids={o['id'] for o in ops}
    if len(ids)!=len(ops):raise ModelPlanError('IDs duplicados')
    def visit(node,active,seen):
        if node in active:raise ModelPlanError('DAG cíclico')
        if node in seen:return
        active.add(node)
        for dep in next(o for o in ops if o['id']==node)['depends_on']:
            if dep not in ids:raise ModelPlanError('Dependencia inexistente')
            visit(dep,active,seen)
        active.remove(node);seen.add(node)
    seen=set()
    for key in ids:visit(key,set(),seen)
    return {'meta':{'name':task_id,'note':response.get('goal','')[:150]},'ops':ops}


async def invoke_and_translate(*, model_port,block:str, task_id:str,goal:str,
                               allowed_ops:set[str], evidence:dict,acceptance:list[dict]):
    """Reutiliza el puerto LLM existente; no crea un proveedor de modelos."""
    if not allowed_ops:raise ModelPlanError('El host no aprobó ninguna operación')
    request={'task_id':task_id,'goal':goal,'stage':'PLAN_JSON','format':'JSON_ONLY',
             'allowed_tools':sorted(allowed_ops),'environment_evidence':evidence,
             'acceptance':acceptance,
             'response_contract':'SYSTEM_QWEN_JSON_PROPUESTO'}
    answer=await model_port.invoke(block,request)
    return parse_planner_steps(answer,task_id=task_id,allowed_ops=allowed_ops)
