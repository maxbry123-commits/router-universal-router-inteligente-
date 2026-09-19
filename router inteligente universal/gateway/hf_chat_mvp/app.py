"""
RIU Chat MVP - banco de pruebas de modelos/latencia para el Router Inteligente
Universal. NO reemplaza a RedUniversal como owner de routing: es una capa de
prueba manual para que el Director compare modelos/proveedores antes de que
el Router los promueva a REMOTE20/READY.

Secretos esperados como Space secrets (Settings -> Variables and secrets del
Space, NUNCA en este archivo):
  HF_TOKEN_1        -> Hugging Face (Inference Providers, incluye DeepSeek V4,
                        Kimi K2/K2.5/K2.6, GLM, Qwen, etc. via router.huggingface.co)
  GROQ_API_KEY_1     -> Groq (Llama, Qwen, GPT-OSS, Kimi K2 instruct)
  NVIDIA_API_KEY_1   -> NVIDIA NIM (MiniMax M2, Llama, etc.)
  CEREBRAS_API_KEY_1 -> Cerebras (Llama, Qwen)
"""
import os
import time
import json
import gradio as gr
from openai import OpenAI

PROVIDERS = {
    "Hugging Face (router)": {
        "base_url": "https://router.huggingface.co/v1",
        "env_key": "HF_TOKEN_1",
        "models": [
            "deepseek-ai/DeepSeek-V4.1-Flash",
            "deepseek-ai/DeepSeek-V4-Pro",
            "moonshotai/Kimi-K2.6",
            "moonshotai/Kimi-K2.5",
            "zai-org/GLM-5.3",
            "Qwen/Qwen3.5-9B",
        ],
    },
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY_1",
        "models": [
            "llama-3.3-70b-versatile",
            "qwen/qwen3-32b",
            "openai/gpt-oss-120b",
            "moonshotai/kimi-k2-instruct",
        ],
    },
    "NVIDIA NIM": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "env_key": "NVIDIA_API_KEY_1",
        "models": [
            "minimaxai/minimax-m2.7",
        ],
    },
    "Cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY_1",
        "models": [
            "llama-3.3-70b",
            "qwen-3-32b",
        ],
    },
}


def get_client(provider_name: str) -> OpenAI:
    cfg = PROVIDERS[provider_name]
    api_key = os.environ.get(cfg["env_key"], "")
    if not api_key:
        raise gr.Error(
            f"Falta el secreto '{cfg['env_key']}' en la configuracion del Space "
            "(Settings -> Variables and secrets)."
        )
    return OpenAI(base_url=cfg["base_url"], api_key=api_key)


def update_model_choices(provider_name: str):
    return gr.update(
        choices=PROVIDERS[provider_name]["models"],
        value=PROVIDERS[provider_name]["models"][0],
    )


def chat(message, history, provider_name, model_name, system_prompt):
    client = get_client(provider_name)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=1024,
        )
        latency_ms = int((time.time() - t0) * 1000)
        reply = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        footer = f"\n\n---\n`{provider_name} / {model_name}` · {latency_ms} ms"
        if usage:
            footer += f" · tokens in/out: {usage.prompt_tokens}/{usage.completion_tokens}"
        return reply + footer
    except Exception as exc:  # noqa: BLE001 - MVP de pruebas, mostrar el error crudo
        latency_ms = int((time.time() - t0) * 1000)
        return f"ERROR ({latency_ms} ms) llamando a {provider_name}/{model_name}:\n\n```\n{exc}\n```"


with gr.Blocks(title="RIU Chat MVP - banco de pruebas") as demo:
    gr.Markdown(
        "# Router Inteligente Universal - Chat MVP\n"
        "Banco de pruebas manual de modelos/proveedores (latencia, calidad, "
        "disponibilidad) antes de promoverlos al Router. No es el Router en "
        "produccion; RedUniversal sigue siendo el unico owner de routing real."
    )
    with gr.Row():
        provider_dd = gr.Dropdown(
            choices=list(PROVIDERS.keys()),
            value=list(PROVIDERS.keys())[0],
            label="Proveedor",
        )
        model_dd = gr.Dropdown(
            choices=PROVIDERS[list(PROVIDERS.keys())[0]]["models"],
            value=PROVIDERS[list(PROVIDERS.keys())[0]]["models"][0],
            label="Modelo",
        )
    system_prompt_tb = gr.Textbox(
        label="System prompt (opcional)", placeholder="Eres un asistente..."
    )
    provider_dd.change(update_model_choices, provider_dd, model_dd)

    gr.ChatInterface(
        fn=chat,
        additional_inputs=[provider_dd, model_dd, system_prompt_tb],
        type="messages",
    )

if __name__ == "__main__":
    demo.launch()
