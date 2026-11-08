from generic_model_adapter import GenericModelAdapter

class ChatBImplementer:
    def __init__(self):
        self.adapter = GenericModelAdapter()

    async def implement(self, block: dict, prompt_context: str, session_id: str = "default") -> dict:
        prompt = f"{prompt_context}\n\n[INSTRUCCIÓN DE CHAT B]\nEscribe código Python para: {block['desc']}.\nLímite estricto: {block['max_loc']} líneas.\nAdemás, escribe un archivo de test con pytest para verificar que funciona.\nSin explicaciones."

        schema_hint = '{"status": "ok", "code": "def func():\\n    return True", "tests": "def test_func():\\n    assert func() == True"}'
        response = await self.adapter.generate_json(prompt, schema_hint, session_id)

        code = response.get("code", "")
        tests = response.get("tests", "")

        if len(code.splitlines()) > block['max_loc']:
            raise ValueError(f"LOC_EXCEEDED: {len(code.splitlines())} > {block['max_loc']}")

        return {"code": code, "tests": tests}
