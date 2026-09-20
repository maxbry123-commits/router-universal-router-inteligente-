# RIU-0106 — Caché para bajar costo, Claude como cerebro (DSL DAG), banco de claves y despliegue — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Solo se escribió en este repo (P3).

## Input del Director (verbatim, con las credenciales REDACTADAS a propósito)
"Resuelve que podamos usar cache para pagar menos precio no se cómo se hace pero hazlo para mantener menor costo.
También necesito que tú puedas conectarte con el chat es decir tú eres el cerebro yo te digo lo que quiero y el plan tú lo eleboras luego tu le ordenas e el modelo que yo te diga las instrucciones en una DSL Dag shema como el plan que te dije que hicieras que te pase el link que hizo Fables tu réplicas exacto 1 a 1 imput block verbartin el mismo modelo y le das las instrucciones como dsl Dag shema me entiendes ?
Que paso con las api key de Nvidia las probaste funciona ?"
Después el Director pegó tokens de Hugging Face y GitHub (5 GitHub + 2 HF + 1 fine-grained) y dijo: "No te la paso más las claves ... tú verás donde la pones con el banco de claves secretas lo mismo la de Nvidia resuleve. Que te falta".
Los valores NO se copian aquí ni en ningún archivo. Se guardaron cifrados (sealed box) solo en GitHub Actions Secrets; HF_TOKEN_1, GH_PAT_FINE_FULL y GH_ACCOUNT_3 también en Codespaces Secrets del repo.

## Banco de claves (nombres, sin valores)
Actions Secrets: `HF_TOKEN_1` (ya existía), `HF_TOKEN_1B`, `HF_TOKEN_MAXBRY123`, `GH_ACCOUNT_1`, `GH_ACCOUNT_2`, `GH_ACCOUNT_3`, `GH_CLASSIC_FULL_1`, `GH_CLASSIC_FULL_2`, `GH_PAT_FINE_FULL`, `RIU_SECRET_SELFTEST`, más los previos (`CEREBRAS_API_KEY_1..6`, `RIU_GITHUB_PAT_FULL_ACCESO`).
Regla de GitHub: un secret no puede empezar por `GITHUB_`; por eso `GH_*`.
Sonda `riu-credential-probe.yml` (run `35522318736`): HF_TOKEN_1 = HF_TOKEN_1B (mismo hash), cuenta `COMAND-CENTER-1`, `repo.write` en su espacio de usuario. `HF_TOKEN_MAXBRY123` también `COMAND-CENTER-1` con `repo.write` en Spaces. GitHub: `GH_CLASSIC_FULL_1/2` y `GH_PAT_FINE_FULL` = `maxbry123-commits` con admin; `GH_ACCOUNT_3` = `planeta123-usa` (sin push en este repo); `GH_ACCOUNT_1` y `GH_ACCOUNT_2` = 401 (inválidas o revocadas). `GH_PAT_FINE_FULL` = `RIU_GITHUB_PAT_FULL_ACCESO` (mismo hash). Faltan: `NVIDIA_API_KEY_1`, `GROQ_API_KEY_1`, `DEEPSEEK_API_KEY`, `MOONSHOT_API_KEY`, `MINIMAX_API_KEY`.
Recomendación: rotar todas las pegadas en chat (quedaron en el transcript).

## NVIDIA
NO probada: no existe ninguna clave NVIDIA que Claude pueda leer (las secrets de GitHub no se leen de vuelta; el Space `owner_HF_1` es una plantilla estática sin claves). Hace falta el valor una vez.

## Caché y costo (código en `integration/chat_mvp/core.py`, `usage.py`)
1. Caché exacta de respuestas: ON por defecto (TTL `RIU_CACHE_TTL`, 24 h); no aplica con temperature > 0; `refresh` la salta y la reescribe conservando el contador de aciertos.
2. Prompts con prefijo estable (agente, documentos ordenados por id, historial solo-append, turno nuevo al final) para que el caché nativo del proveedor cobre el prefijo repetido como entrada en caché.
3. Presupuesto de historial (24 000 caracteres): al pasarse recorta de golpe hasta el 60 % para no romper el prefijo cada turno.
4. Proveedores directos con caché nativa: `deepseek`, `moonshot`, `minimax` (necesitan sus claves).
5. Registro de uso `/chat/usage`: tokens, tokens de entrada en caché del proveedor, aciertos de caché de respuestas, ahorro/costo estimado con `RIU_PRICES_JSON`.
Evidencia (runner): en el DAG ORDER-000, 794 tokens de entrada de los cuales 192 llegaron como caché del proveedor a través del router HF (24 %). En el E2E del chat: `usage calls=7 input=838 cached_input=192 resp_cache_hits=2`.

## Claude como cerebro: DSL DAG `riu.dag/v1`
Protocolo: Claude escribe `chat_orders/<ID>.dag.json` → despacha `RIU DAG Run` → el Router ejecuta cada nodo con el modelo indicado → resultado en `chat_orders/results/<ID>.result.json` → Claude lo lee y audita.
Reglas: `input_block` literal en cada nodo; el modelo tiene autoridad NONE y no se autocertifica; PASS solo por comprobaciones deterministas (`expect`); sin `expect` = `DONE_UNVERIFIED`; reintento con las comprobaciones fallidas → `escalate_to` → FAIL (dependientes BLOCKED); ledger encadenado por hash.
Evidencia: `ORDER-000-smoke` PASS con DeepSeek V4 Flash (JSON con claves exigidas), Kimi K3 (validador SI/NO) y MiniMax M3; `ledger_valid=true`; archivo `chat_orders/results/ORDER-000-smoke.result.json`.
🚩 El esquema es PROVISIONAL: falta el link de Fables para replicar su DSL 1 a 1.

## Despliegue del chat
- Hugging Face: crear un Space Docker devuelve `402`: hoy exige suscripción PRO; solo los Spaces estáticos son gratis (sonda `riu-hf-create-probe.yml`, run `35522692158`). El workflow `Deploy Chat MVP Space` queda listo y funcionará cuando exista PRO (usa `HF_TOKEN_MAXBRY123`).
- Codespace `riu-chat-mvp-v6x6j9544g752x4gp` (devcontainer `.devcontainer/devcontainer.json`, puerto 7860 privado): seguía en `Provisioning` tras 16 min (probable clon lento del repo grande). No confirmado.
- Alternativa inmediata: en cualquier máquina, `pip install -r "router inteligente universal/chat_space/requirements.txt"` y `uvicorn integration.chat_mvp.app:app --port 7860` dentro de `router inteligente universal/`.

## Tests
Antes de este nodo: 48 passed. Con el nodo: 56 passed + 1 failed (el contador de aciertos se reseteaba al refrescar; corregido en `33f191c`). Nueva corrida despachada.

## Flags 🚩
1. NVIDIA/Groq/DeepSeek/Moonshot/MiniMax: faltan claves. 2. Link de Fables. 3. Hosting: HF PRO o Codespace/local. 4. `GH_ACCOUNT_1/2` inválidas. 5. Rotar claves expuestas. 6. STATE/CHECKPOINT/PLAN/Handoff siguen desfasados; bitácora sin fusionar.

## Próximo delta seguro
Leer la corrida verify posterior a `33f191c`/`6bce6bd`; estado del Codespace; con el link de Fables, ajustar `riu.dag/v1` al esquema exacto; con las claves faltantes repetir el E2E y anotar catálogos.
