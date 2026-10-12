# PARCHE DE RECUPERACION 1 - ROUTER (2026-10-12)
No lleva claves. Los secretos viven como secretos del job.

1. Donde esta el codigo: bucket COMAND-CENTER-1/yaiwes-memoria-storage, ruta router-inteligente-universal/codigo/router-bundle.tar.gz (respaldo: router-bundle.tar.gz.bak-20261011-pre-banco-unico). Se rehace desde GitHub main (carpetas integration, plugins, security, red, Banco de claves, chat router/04-MEMORIA).
2. Job en HF: imagen python:3.12, flavor cpu-basic (2 CPU, 16 GB), timeout 172800 s, puerto 8000 publico. Comando: instala dependencias, baja el bundle a /app, abre el banco viejo, lanza `python riu_kernel.py --watch &` y `uvicorn public_chat_app:app --host 0.0.0.0 --port 8000`.
3. Variables: HF_BUCKET_ID, RIU_AUTOSYNC_SECONDS=60, RIU_CHAT_ALLOW_PROVIDER_LIVE=1, RIU_CODE_BUNDLE, RIU_CORS_ORIGINS=*, RIU_DATA_DIR=/tmp/riu-data, RIU_FLAVOR, RIU_JOB_ROLE=main, RIU_ROOT, RIU_VAULT_PATH, RIU_VAULT_SOURCE, RIU_VAULT_PROVIDERS_SOURCE.
4. Secretos del job (solo nombres): HF_TOKEN, HF_CONTROL_JOBS_TOKEN, GITHUB_PERSONAL_ACCESS_TOKEN, RIU_VAULT_PASSPHRASE, FICHA_CLAVE_BANCO, RIU_ROUTER_API_KEY, RIU_AGENT_API_KEYS, RIU_AGENT_API_KEYS_2, RIU_DIRECTOR_KEY_HASH, RIU_PUBLIC_CHAT_KEY.
5. Relanzar: el kernel (riu_kernel.py, launch()) reabre el banco con RIU_VAULT_PASSPHRASE, rearma los secretos y lanza el job; luego publica LIVE_URL.json.
6. La pantalla (Vercel riu-jev-bridge) lee LIVE_URL.json y exige una direccion de 24 caracteres hex + --8000.hf.jobs. Job vivo al 2026-10-12: 6acc638dfee2c900701a1ad0.
7. Comprobar: GET /health = ok; POST /plugins/puente_chat/call/status = 22 modelos; chat_async + resultado con un modelo NVIDIA y uno Groq.
