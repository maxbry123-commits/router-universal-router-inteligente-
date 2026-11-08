from generic_model_adapter import GenericModelAdapter

class ChatBImplementer:
    def __init__(self):
        self.adapter = GenericModelAdapter()

    async def implement(self, block: dict, prompt_context: str) -> str:
        prompt = f"{prompt_context}\n\n[INSTRUCCIÓN DE CHAT B]\nEscribe código Python para: {block['desc']}.\nLímite estricto: {block['max_loc']} líneas.\nSin explicaciones, solo el código."

        schema_hint = '{"status": "ok", "code": "def func():\\n    pass", "tests": []}'
        response = await self.adapter.generate_json(prompt, schema_hint)

        code = response.get("code", "")
        loc = len(code.splitlines())
        if loc > block['max_loc']:
            raise ValueError(f"LOC_EXCEEDED: {loc} > {block['max_loc']}")

        return code
