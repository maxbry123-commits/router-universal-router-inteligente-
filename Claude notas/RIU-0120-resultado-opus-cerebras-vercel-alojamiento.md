# RIU-0120 — Resultado de la instrucción (l): Opus, Cerebras/Groq, Vercel y dónde alojar el chat — 2026-09-21

Instrucción textual: `INPUT-VERBATIM-2026-09-21-l-opus-cerebras-groq-vercel-chat.md`.

## L1 — Opus y el archivo cifrado de las claves NVIDIA
Opus necesita tres cosas: (1) el archivo cifrado `banco-nvidia-equipo.b64` (2.060 caracteres; solo el Director lo tiene, no está en el repo), (2) la contraseña de ese banco (la que el Director recibió) y (3) `vault.py` (`Chat Mvp/secret_bank/vault.py`, público) más `nvidia_team_client.py` (`Claude notas/KIT-EQUIPO-NVIDIA/`). Pasos en el README del kit. El archivo cifrado NO se publicó en el repo (repo público).

## L2 — Cerebras y Groq
- Cerebras (6 claves guardadas en GitHub Secrets; run `35569598666`): catálogo `gpt-oss-120b` y `qwen-3.8-27b`. Claves 1, 3, 4 y 6 autentican pero responden `402` (pago requerido) en los dos modelos. Claves 2 y 5: error de formato (`ValueError`: el valor guardado tiene un carácter no válido, probablemente un salto de línea o espacio). Es decir, con las claves guardadas Cerebras NO responde. El Director dice que sí funcionaron: esas claves no están en el repo.
- Groq: no hay ninguna clave guardada; no se pudo probar.

## L4 — ¿Acceso a Vercel?
SÍ. Corrección de Claude: antes dije que solo tenía lectura; era falso (las herramientas de Vercel estaban sin cargar). Cuenta `maxbry123-8833`, plan Hobby (gratis), equipo `team_hG9df7zIgfZFY0oxFFsIRr1u`.

## L5 — Chat: dónde alojarlo
- Preparado en el repo (`router inteligente universal/`): `api/index.py`, `vercel.json` (60 s por petición), `requirements.txt`, `.vercelignore`.
- BLOQUEO: crear el proyecto enlazado al repo falló con `400`: la cuenta de Vercel no tiene una "Login Connection" a GitHub. Acción del Director: en Vercel, conectar su cuenta de GitHub (Account Settings → Authentication / Login Connections) y permitir el repo. Después, un solo comando crea el proyecto y despliega.
- Evaluación (sin validar todavía):
  - Vercel Hobby: gratis y rápido; PERO es sin estado: el Router guarda en memoria la salud de las claves, la concurrencia adaptativa y el banco desbloqueado; en Vercel cada instancia empieza de cero, así que esas protecciones se pierden; sin disco persistente; límite de tiempo por petición. Sirve como demo provisional con claves por petición (pestaña Claves), no como chat definitivo.
  - Hugging Face Space (Docker, requiere PRO): un proceso permanente, disco/bucket persistente, mantiene el banco desbloqueado y la salud de las claves. Es la mejor opción técnica para el chat definitivo.
- Recomendación: Vercel ya (provisional) + Hugging Face PRO para el definitivo. Nada de esto está validado: no hay URL desplegada.

## L3 — Descargar agentes y SmolAgents con los motores
NO iniciado. Hallazgos: los motores de descarga viven en `agentes` (carpeta `motores de descarga extracción copiado movimiento archivos agentes`) y en los workflows `research-download-chain-router-components-*.yml` de este repo (para componentes del Router). Falta decidir el destino y ejecutar.
