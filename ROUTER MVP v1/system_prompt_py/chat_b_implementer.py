from generic_model_adapter import GenericModelAdapter
from tool_call_validator import ToolCallValidator

class ChatBImplementer:
    def __init__(self):
        self.adapter = GenericModelAdapter()

    async def implement(self, block: dict, prompt_context: str, session_id: str = 'default') -> dict:
        prompt = f"{prompt_context}\n\n[INSTRUCCIÓN]\nEscribe codigo para: {block['desc']}. Maximo {block['max_loc']} lineas. Si necesitas una herramienta, responde JSON: {{\"tool\": \"nombre\", \"args\": {{}}}}. Si escribes codigo, responde JSON: {{\"code\": \"...\", \"tests\": \"...\"}}."
        response_text = await self.adapter.generate_raw(prompt, session_id)
        parsed = ToolCallValidator.validate(response_text)
        if parsed['type'] == 'code':
            if len(parsed['code'].splitlines()) > block['max_loc']:
                raise ValueError(f"LOC_EXCEEDED: {len(parsed['code'].splitlines())} > {block['max_loc']}")
            return {'code': parsed['code'], 'tests': parsed.get('tests', '')}
        elif parsed['type'] == 'tool_call':
            raise NotImplementedError(f"Tool call: {parsed['tool']}")
        else:
            raise ValueError(f"Respuesta no valida: {parsed}")
