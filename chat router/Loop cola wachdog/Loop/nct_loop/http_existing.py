"""Conector optativo a BLOQUE ya EXISTENTE. Nunca define un endpoint inventado."""
from __future__ import annotations
import asyncio,json,os
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from .contracts import NCTError

class ConfiguredBlockHTTP:
    def __init__(self,endpoint:str,*,api_key_env:str,timeout_s:int=120):
        parts=urlsplit(endpoint)
        is_local=parts.hostname in ('localhost','127.0.0.1','::1')
        if parts.scheme!='https' and not (parts.scheme=='http' and is_local):
            raise NCTError('endpoint explícito HTTPS requerido (HTTP solo localhost)')
        if not parts.hostname or parts.username or parts.password or parts.fragment:
            raise NCTError('URL de bloque inválida')
        if timeout_s<=0 or timeout_s>180:raise NCTError('timeout incorrecto')
        self.endpoint=endpoint;self.env=api_key_env;self.timeout=timeout_s
    async def invoke(self,block:str,payload:dict)->dict:
        key=os.getenv(self.env)
        if not key:raise NCTError('secreto de bloque NO CONFIGURADO en vault/entorno')
        data=json.dumps({'block':block,'payload':payload},ensure_ascii=False).encode('utf8')
        def invoke_sync():
            req=Request(self.endpoint,data=data,headers={'Content-Type':'application/json',
               'X-API-Key':key},method='POST')
            try:
                with urlopen(req,timeout=self.timeout) as resp:
                    if resp.status!=200:raise NCTError('HTTP_STATUS_'+str(resp.status))
                    raw=resp.read(512*1024+1)
                    if len(raw)>512*1024:raise NCTError('RESPUESTA_TOO_LARGE')
                    body=json.loads(raw)
                    if not isinstance(body,dict):raise NCTError('respuesta JSON inválida')
                    return body
            except HTTPError as ex:raise NCTError('BLOCK_HTTP_'+str(ex.code)) from ex
            except URLError as ex:raise NCTError('BLOCK_UNREACHABLE') from ex
        return await asyncio.to_thread(invoke_sync)
