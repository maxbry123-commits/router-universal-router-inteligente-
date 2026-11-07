import asyncio, httpx

async def call_plugin(plugin_name, config, prompt):
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    payload = {"model": config["model"], "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
    # Timeout largo para permitir que modelos lentos terminen
    async with httpx.AsyncClient(timeout=300) as client:
        try:
            r = await client.post(f"{config['base_url']}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            return plugin_name, r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return plugin_name, f"ERROR: {e}"

async def run_parallel_agents(plugins: dict, prompt: str):
    tasks = [call_plugin(name, config, prompt) for name, config in plugins.items()]
    for future in asyncio.as_completed(tasks):
        name, result = await future
        if "ERROR" not in result:
            return name, result
    return "Ninguno", "Todos fallaron."
