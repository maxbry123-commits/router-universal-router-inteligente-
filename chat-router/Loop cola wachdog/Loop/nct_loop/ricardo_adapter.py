"""Fusión REAL del patrón Ricardo: JSON meta+ops -> intérprete Python -> recibos.
Usa una copia SIN CAMBIOS del motor_cli.py aportado por el usuario, solo offline.
En producción conectar al EXISTENTE ejecutor de herramientas del harness.
"""
from __future__ import annotations
from pathlib import Path
import json, hashlib, re
from .contracts import NCTError, stable_hash
from referencia_ricardo.motor_cli import Motor

class RicardoOpsDemo:
    def __init__(self,root:Path,policy_file:Path):
        self.root=Path(root).resolve()
        self.policy=json.loads(Path(policy_file).read_text(encoding='utf8'))
        self.root.mkdir(parents=True,exist_ok=True)
    async def execute(self,validated_ops:dict,task_id:str)->dict:
        """La autorización real también debe existir en harness; la allowlist JSON sola no basta."""
        if not isinstance(validated_ops,dict):raise NCTError('propuesta debe ser JSON objeto')
        if set(validated_ops)-{'meta','ops'}:raise NCTError('claves raíz extras')
        meta=validated_ops.get('meta')
        ops=validated_ops.get('ops')
        if not isinstance(meta,dict) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',str(meta.get('name',''))):
            raise NCTError('meta.name inválido')
        if not isinstance(ops,list) or not (1<=len(ops)<=self.policy.get('max_ops',32)):
            raise NCTError('tamaño de operaciones inválido')
        allowed=set(self.policy['allowed_ops'])
        allowed_keys={
           'inspect_workspace':{'id','op','depends_on'},
           'create_directory':{'id','op','depends_on','path'},
           'write_text':{'id','op','depends_on','path','text'},
           'read_text':{'id','op','depends_on','path'},
           'verify_exists':{'id','op','depends_on','path'},
           'verify_contains':{'id','op','depends_on','path','text'},
           'finish':{'id','op','depends_on'}}
        for op in ops:
            if not isinstance(op,dict):raise NCTError('operación no objeto')
            name=op.get('op')
            if name not in allowed or name not in allowed_keys:raise NCTError('op no autorizada: '+str(name))
            if set(op)-allowed_keys[name]:raise NCTError('argumento desconocido en '+name)
            if 'path' in op and (not isinstance(op['path'],str) or not op['path']):raise NCTError('path inválido')
            if 'text' in op and (not isinstance(op['text'],str) or len(op['text'])>self.policy['max_text_chars']):
                raise NCTError('texto excesivo')
        result=Motor(self.root,self.policy).run(validated_ops)
        return {'ok':result['ok'], 'receipts':result['receipts'],
                'errors':result['errors'],'executed_count':result['ops_executed'],
                'ops_total':result['ops_total'], 'report_origin':'MOTOR_CLI_LOCAL_REAL',
                'plan_sha256':stable_hash(validated_ops)}

class FileCheckerDemo:
    """Comprobación independiente de archivos físicos + SHA de recibos; no LLM judge."""
    def __init__(self,root:Path):self.root=Path(root).resolve()
    async def check(self,task,receipts:list[dict])->dict:
        if not receipts:return {'ok':False,'errors':['NO_RECEIPTS']}
        good=[];errors=[]
        for receipt in receipts:
            if receipt.get('status')!='PASS' or receipt.get('task_id')!=task.id:
                errors.append('RECEIPT_INVALID');continue
            evidence=receipt.get('evidence',{})
            if evidence.get('report_origin')!='MOTOR_CLI_LOCAL_REAL':errors.append('SOURCE_NOT_TRUSTED');continue
            tool_receipts=evidence.get('receipts',[])
            if len(tool_receipts)!=evidence.get('ops_total') or not all(x.get('ok') for x in tool_receipts):
                errors.append('OP_RECEIPT_MISSING');continue
            for op_r in tool_receipts:
                res=op_r.get('result',{});p=res.get('path');expected_sha=res.get('sha256')
                if p and expected_sha:
                    target=(self.root/p).resolve()
                    if not target.is_relative_to(self.root) or not target.is_file():errors.append('FILE_OUTSIDE_OR_MISSING');continue
                    if hashlib.sha256(target.read_bytes()).hexdigest()!=expected_sha:errors.append('HASH_MISMATCH')
            good.append(receipt['id'])
        for rule in task.acceptance:
            if set(rule)-{'op','path','text'} or rule.get('op') not in ('verify_exists','verify_contains'):
                errors.append('UNSUPPORTED_ACCEPTANCE');continue
            path=rule.get('path')
            if not isinstance(path,str) or not path:errors.append('BAD_PATH');continue
            target=(self.root/path).resolve()
            if not target.is_relative_to(self.root) or not target.is_file():errors.append('FILE_NOT_FOUND');continue
            if rule.get('op')=='verify_contains':
                needle=rule.get('text')
                if not isinstance(needle,str) or not needle or needle not in target.read_text(encoding='utf8'):
                    errors.append('CONTENT_MISMATCH')
        ok=not errors and len(good)==len(receipts)
        return {'ok':ok,'receipt_ids':good,'errors':errors,
                'three_layers':{'adversarial_contract':ok,'cross_file_hash':ok,
                                'maker_checker_acceptance':ok},
                'kind':'DETERMINISTIC_3_CHECKS_NO_ADVERSARIAL_LLM'}
