'''Mini kernel LLM (el 5%): un solo punto para las funciones que de verdad necesitan redactar.
Endpoint compatible con OpenAI (el Router, NVIDIA o Groq) por variables: RIU_LLM_URL (termina en /v1), RIU_LLM_KEY,
RIU_LLM_MODEL, RIU_LLM_MAX_TOKENS (256). Sin RIU_LLM_URL devuelve None y quien llama usa su respuesta determinista.'''
from __future__ import annotations

import json
import os
import urllib.request


def disponible() -> bool:
    return bool(os.environ.get('RIU_LLM_URL'))


def pedir(prompt: str, sistema: str = 'Responde breve, en espanol, solo con la informacion dada.', max_tokens: int | None = None):
    url = os.environ.get('RIU_LLM_URL', '')
    if not url:
        return None
    body = {'model': os.environ.get('RIU_LLM_MODEL', 'auto'), 'temperature': 0,
            'max_tokens': int(max_tokens or os.environ.get('RIU_LLM_MAX_TOKENS', '256')),
            'messages': [{'role': 'system', 'content': sistema}, {'role': 'user', 'content': prompt}]}
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=json.dumps(body).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.environ.get('RIU_LLM_KEY', '')})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 endpoint configurado por el operador
            return json.loads(r.read())['choices'][0]['message']['content']
    except Exception:  # noqa: BLE001
        return None
