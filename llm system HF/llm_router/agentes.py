import os
import httpx

AGENTES = {
    "hermes": {
        "base_env": "HERMES_URL",
        "key_env": "HERMES_API_KEY",
        "health": "/v1/models",
        "chat": "/v1/chat/completions",
        "runs": "/v1/runs",
        "skills": "/v1/skills",
        "toolsets": "/v1/toolsets",
    },
    "openclaw": {
        "base_env": "OPENCLAW_URL",
        "key_env": "OPENCLAW_API_KEY",
        "health": "/healthz",
        "chat": "/v1/chat/completions",
        "models": "/v1/models",
        "responses": "/v1/responses",
    },
}

TOOL_SCHEMA = {"type": "function", "function": {"name": "agente_llamar", "description": "Envía mensajes a un agente espejo (hermes u openclaw) por su API HTTP.",
    "parameters": {"type": "object", "properties": {"agente": {"type": "string", "enum": ["hermes", "openclaw"]},
        "messages": {"type": "array", "items": {"type": "object"}}, "model": {"type": "string"}},
        "required": ["agente", "messages"]}}}

def _cfg(nombre: str) -> dict:
    if nombre not in AGENTES:
        raise ValueError(f"agente desconocido: {nombre}")
    spec = AGENTES[nombre]
    base = os.getenv(spec["base_env"], "").rstrip("/")
    if not base:
        raise RuntimeError(f"{spec['base_env']} no configurada")
    key = os.getenv(spec["key_env"], "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    return {"base": base, "headers": headers, "spec": spec}

async def health(nombre: str, client=None) -> dict:
    c = _cfg(nombre)
    async with (client or httpx.AsyncClient(timeout=10)) as cl:
        r = await cl.get(c["base"] + c["spec"]["health"], headers=c["headers"])
        return {"agente": nombre, "status": r.status_code, "ok": r.status_code < 400}

async def llamar(nombre: str, messages: list, model: str = None, client=None) -> dict:
    c = _cfg(nombre)
    payload = {"messages": messages, "stream": False}
    if model:
        payload["model"] = model
    async with (client or httpx.AsyncClient(timeout=120)) as cl:
        r = await cl.post(c["base"] + c["spec"]["chat"], json=payload, headers=c["headers"])
        if r.status_code >= 400:
            return {"status": "failed", "agente": nombre, "http": r.status_code}
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return {"status": "ok", "agente": nombre, "content": content}

async def dispatch(args: dict, client=None) -> dict:
    try:
        return await llamar(args["agente"], args["messages"], args.get("model"), client=client)
    except Exception as e:
        return {"status": "failed", "error": str(e)}
