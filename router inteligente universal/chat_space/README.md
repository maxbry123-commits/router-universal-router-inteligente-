---
title: RIU Chat MVP
emoji: 💬
colorFrom: orange
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# RIU Chat MVP

Chat del Router Inteligente Universal: proveedores (Hugging Face Router, Cerebras, NVIDIA NIM, Groq y API local),
modo sin agente / con agente, documentos adjuntos, cuentas GitHub seleccionables y almacenamiento en 4 sistemas
(SQL SQLite, grafo de procedencia, caché y documentos).

Cada turno pasa por el hot-path certificado: FastAPI → Enchufe Gate → RedUniversal → proveedor.

## Secrets y variables del Space (los pone el workflow `Deploy Chat MVP Space`)

Secrets: `HF_TOKEN`, `CEREBRAS_API_KEY`, `NVIDIA_API_KEY`, `GROQ_API_KEY`, `GITHUB_TOKEN_1` (opcional).
Variables: `RIU_CHAT_ALLOW_PROVIDER_LIVE=1`, `RIU_DATA_DIR=/data`, `HF_BUCKET_ID`, `RIU_GITHUB_ACCOUNTS`, `RIU_LOCAL_BASE_URL`.

## Acceso

La página `/chat` pide una API key del Router (las 100 keys MAXBRY-001..100 validan contra el keystore de solo hashes).
Nunca se guardan claves en el repo: las de proveedores viven como secrets o se pegan por petición (BYOK) en la pestaña Claves.
