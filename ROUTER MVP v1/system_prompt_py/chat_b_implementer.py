from generic_model_adapter import GenericModelAdapter
from tool_call_validator import ToolCallValidator
from tool_executor import ToolExecutor
from loc_limits import MAX_BLOCK_LOC, MAX_CONTINUATIONS

class IncompleteResponse(Exception):
    def __init__(self, partial: str):
        super().__init__("RESPUESTA_INCOMPLETA")
        self.partial = partial

class ChatBImplementer:
    def __init__(self):
        self.adapter = GenericModelAdapter()
        self.executor = ToolExecutor()

    async def _collect(self, prompt: str, session_id: str) -> str:
        text, finish = await self.adapter.generate_raw_meta(prompt, session_id)
        rounds = 0
        while finish == "length" and rounds < MAX_CONTINUATIONS:
            tail = "\n".join(text.splitlines()[-40:])
            cont = (f"Tu respuesta se cortó por límite de tokens. Continúa EXACTAMENTE en el carácter "
                    f"siguiente, sin repetir texto ya recibido, sin prefijos ni explicaciones.\n"
                    f"Final recibido:\n{tail}")
            more, finish = await self.adapter.generate_raw_meta(cont, session_id)
            text += more
            rounds += 1
        if finish == "length":
            raise IncompleteResponse(text)
        return text

    async def implement(self, block: dict, prompt_context: str, session_id: str = 'default', partial: str = '') -> dict:
        max_loc = min(int(block.get('max_loc', MAX_BLOCK_LOC)), MAX_BLOCK_LOC)
        prompt = f"{prompt_context}\n\n[INSTRUCCIÓN]\nEscribe codigo para: {block['desc']}. Maximo {max_loc} lineas. Si necesitas una herramienta, responde JSON: {{\"tool\": \"nombre\", \"args\": {{}}}}. Si escribes codigo, responde JSON: {{\"code\": \"...\", \"tests\": \"...\"}}."
        if partial:
            prompt += f"\n[PARCIAL YA RECIBIDO: continua exactamente despues de este texto, sin repetirlo]\n{partial[-3000:]}"
        text = await self._collect(prompt, session_id)
        if partial:
            text = partial + text
        parsed = ToolCallValidator.validate(text)

        if parsed['type'] == 'code':
            return {'type': 'code', 'code': parsed['code'], 'tests': parsed.get('tests', ''),
                    'loc': len(parsed['code'].splitlines())}
        elif parsed['type'] == 'tool_call':
            result = await self.executor.execute(parsed['tool'], parsed['args'])
            return {'type': 'tool_result', 'tool': parsed['tool'], 'args': parsed['args'], 'result': result}
        else:
            raise ValueError(f"Respuesta no valida: {parsed}")
