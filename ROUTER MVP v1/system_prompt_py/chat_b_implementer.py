from fallback_middleware import execute_with_fallback_async

async def implement_block(block: dict, model_family: str = "qwen2.5") -> str:
    prompt = f"Escribe código Python para: {block['desc']}. Máximo {block['max_loc']} líneas. Sin explicaciones."
    providers = ["groq", "nvidia"]

    async def _call_llm(provider: str, p: str, mf: str) -> str:
        return f"def func_{block['id']}():\n    return '{block['desc']}'\n"

    return await execute_with_fallback_async(
        providers=providers,
        llm_call_fn=_call_llm,
        prompt=prompt,
        model_family=model_family
    )
