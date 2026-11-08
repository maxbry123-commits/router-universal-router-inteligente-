from generic_model_adapter import GenericModelAdapter
from tool_call_validator import ToolCallValidator
from tool_executor import ToolExecutor

class ChatBImplementer:
    def __init__(self):
        self.adapter = GenericModelAdapter()
        self.executor = ToolExecutor()

    async def implement(self, block: dict, prompt_context: str, session_id: str = 'default') -> dict:
        prompt = f"{prompt_context}\n\n[INSTRUCCIÓN]\nEscribe codigo para: {block['desc']}. Maximo {block['max_loc']} lineas. Si necesitas una herramienta, responde JSON: {{\"tool\": \"nombre\", \"args\": {{}}}}. Si escribes codigo, responde JSON: {{\"code\": \"...\", \"tests\": \"...\"}}."
        response_text = await self.adapter.generate_raw(prompt, session_id)
        parsed = ToolCallValidator.validate(response_text)

        if parsed['type'] == 'code':
            if len(parsed['code'].splitlines()) > block['max_loc']:
                raise ValueError(f"LOC_EXCEEDED: {len(parsed['code'].splitlines())} > {block['max_loc']}")
            return {'type': 'code', 'code': parsed['code'], 'tests': parsed.get('tests', '')}

        elif parsed['type'] == 'tool_call':
            result = await self.executor.execute(parsed['tool'], parsed['args'])
            return {'type': 'tool_result', 'tool': parsed['tool'], 'result': result}

        else:
            raise ValueError(f"Respuesta no valida: {parsed}")
