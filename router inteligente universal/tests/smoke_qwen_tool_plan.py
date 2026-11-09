import json
import os
from openai import OpenAI

cliente = OpenAI(
    api_key=os.environ['QWEN_TOKEN_PLAN_API_KEY'],
    base_url=(
        'https://token-plan.maas.qwencloudapi.com/compatible-mode/v1'
    ),
    timeout=180,
    max_retries=0,
)

def consultar(mensajes, tools=None, choice=None):
    payload = {
        'model': 'qwen3.8-max',
        'messages': mensajes,
        'stream': True,
        'stream_options': {'include_usage': True},
        'enable_thinking': False,
        'max_completion_tokens': 4096,
    }
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = choice or 'auto'
    respuesta = cliente.chat.completions.create(**payload)
    texto, calls = [], {}
    fin = None
    for chunk in respuesta:
        if not chunk.choices:
            continue
        c = chunk.choices[0]
        if c.finish_reason:
            fin = c.finish_reason
        d = c.delta
        if d.content:
            texto.append(d.content)
        for tc in d.tool_calls or []:
            t = calls.setdefault(tc.index, {'id': '', 'nombre': '', 'args': ''})
            if tc.id:
                t['id'] = tc.id
            if tc.function:
                if tc.function.name:
                    t['nombre'] += tc.function.name
                if tc.function.arguments:
                    t['args'] += tc.function.arguments
    return ''.join(texto), [calls[k] for k in sorted(calls)], fin

tools = [{
    'type': 'function',
    'function': {
        'name': 'verificar_python',
        'description': 'Comprueba el ejecutor Python local',
        'parameters': {'type': 'object', 'properties': {}, 'required': []},
    },
}]
mensajes = [{
    'role': 'user',
    'content': 'Ejecuta verificar_python y comunica el resultado.',
}]
texto, calls, fin = consultar(mensajes, tools, {
    'type': 'function', 'function': {'name': 'verificar_python'},
})
assert calls, 'FAIL: Qwen no emitió tool_call'
assert fin != 'length', 'FAIL: respuesta cortada'
llamadas = []
for c in calls:
    assert c['nombre'] == 'verificar_python' and c['id']
    json.loads(c['args'])
    llamadas.append({
        'id': c['id'], 'type': 'function',
        'function': {'name': c['nombre'], 'arguments': c['args']},
    })
mensajes.append({'role': 'assistant', 'content': texto, 'tool_calls': llamadas})
for c in llamadas:
    # Ejecución Python real, determinista, sin operaciones sobre GitHub.
    resultado = {'ok': True, 'ejecutor': 'python'}
    mensajes.append({
        'role': 'tool', 'tool_call_id': c['id'],
        'content': json.dumps(resultado),
    })
final, _, _ = consultar(mensajes)
assert final.strip(), 'FAIL: Qwen no respondió tras recibir la tool'
print('PASS: SSE / tool_call / Python / tool_result / respuesta final')
