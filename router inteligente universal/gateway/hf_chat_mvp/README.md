---
title: RIU Chat MVP
emoji: 🧭
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: false
---

# RIU Chat MVP - banco de pruebas de modelos

Chat con selector de proveedor/modelo para probar latencia y calidad de
DeepSeek V4, Kimi K2, GLM, Qwen (via Hugging Face Inference Providers),
Groq, NVIDIA NIM y Cerebras -- antes de que el Router Inteligente Universal
los promueva a produccion.

## Despliegue (0 friccion, sin copiar codigo a mano)

1. En huggingface.co: **New Space** -> SDK **Gradio** -> conectar
   **"Sync with a GitHub repo"** apuntando a
   `maxbry123-commits/router-universal-router-inteligente-`, carpeta
   `router inteligente universal/gateway/hf_chat_mvp/`.
2. En el Space creado: **Settings -> Variables and secrets** -> agregar como
   *secret* (no variable publica): `HF_TOKEN_1`, `GROQ_API_KEY_1`,
   `NVIDIA_API_KEY_1`, `CEREBRAS_API_KEY_1`.
3. El Space se reconstruye solo y queda accesible desde una URL publica
   (`https://huggingface.co/spaces/<tu-cuenta>/riu-chat-mvp`) -- usable desde
   el navegador del telefono sin instalar nada.

## Nota de seguridad
Los secretos del Space son propios de HF (distintos de los secretos de
GitHub) -- este paso 2 debe hacerse manualmente una vez por el Director,
igual que los secretos de GitHub, porque escribir secretos de terceros
(HF o GitHub) desde una sesion de Claude esta bloqueado por diseno.
