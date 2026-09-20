# RIU-0107 — INPUT BLOCK 05: CHAT MVP + ALMACENAMIENTO MVP + GRUPOS 0/1/2 — 2026-09-19/20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Alcance de escritura: solo este repo (P3). Entrada de la bitácora en archivo propio (la API de GitHub no permite append; reescribir `BITACORA-CRAZY-WALL.md` arriesga el historial). Copiar a la bitácora principal cuando el Director autorice la partición.
Numeración: RIU-0105 (chat MVP) y RIU-0106 (verificación hot-path HF, otro chat) ya existen; este nodo es RIU-0107. Fidelidad del verbatim: ver `Claude notas/REFERENCIAS-ADJUNTAS-INPUT-05-ERRATA.md`.

## Input literal del Director (verbatim)

---INICIO---

Ok 
Paso 1 dieme qué hay que decidir para que puedas terminar con referente al chat 
Necesitas que pueda tu colocar los api key de mis modelos locales y los modelos de deepsek v4 flash y pro y Kimi k 3 mínimax M3 
Que puedan operar en Github y huggueface 100%
 autorizado 
📌Que con el selector pueda cambiar de cuenta de Github diferente 
📌Que los  modelos que yo seleccione trabaje con el pool de agente que yo te voy a decir pueda operar con agente y sin agente 
📌 Le conectas al chat dentro de huggueface almacenamiento su propio espacio y fusionas para crear un entorno llamado Mvp almacenamiento para ai 
Data base 
SQL Little 
Graphiti y graphyty 
Caché 
Que pueda subir archivos adjuntos y tener una ventana de documentos en almacenamiento y conectados cableado por medio de los 4 sistema de almacenamiento para agentes 
Hasta que no termines esto no pasas a paso 2 
Grupo para el chat 📌 
comand Center y 
Neuro-Orchestrator-8B — 8B — orquestación/agentic.
MiroThinker-8B — 8B — razonamiento.
LFM2.5-8B-A1B — 8B total / ~1B activo — subagentes, loops agentic.
OpenThinker3-7B — 7B — razonamiento.
LFM2-2.6B — 2.6B — worker rápido, clasificación y extracción
Nemotron Nano 9B v2 — 9B — razonamiento, arquitectura y reparación.
Nanbeige4.2-3B — 3B — 🧑‍💻 MODELO DE CODE / agentic
Neuro-Orchestrator-8B — 8B — orquestación/agentic.
MiroThinker-8B — 8B — razonamiento.
LFM2.5-8B-A1B — 8B total / ~1B activo — subagentes, loops agentic.
OpenThinker3-7B — 7B — razonamiento.
Modelos que deben trabajar local por máximo 26 de ram  quanrificado para no saturar el procesador + caché 
Muse Glimmer 30B — 30B — 🧑‍💻 MODELO DE CODE / agentic, multimodal.
Laguna XS 2.1 — 33B total / 3B activos — 🧑‍💻 MODELO DE CODE / agentic, router y long-horizon.
DeepSeek-Coder — variante/peso no especificado en tus archivos — 🧑‍💻 MODELO DE CODE.
DeepSeek v4 flash 


Paso 2📌 



Paso 3 📌 

Necesito que revises el router en el repo de router universal usa el router que hizo Fables los code están en los archivos 
Luego necesito que uses lo que adelanto sol gpt y íntegras los componentes mínimos componentes para conseguir el siguiente objetivo 
1. Vasmos a tener más de 50 agente con el nombre de agente Seals Team YAIWES necesito que operen con las api locales que te voy a define esos modelos locales no deben estar instalado a huggueface deben llamar al modelo remoto como lo indica hugguenface para no descargar el modelo y deben trabajar como mirror y duplicarse sines necesario 50 o 100 veces 
Deben usar el dataset y los aceleradores que deberían o fueron instalados en huggueface 
Necesito que si se satura los 3 procesadores de cómputo no se caiga salte a 7 procesadores más y si llega al número 10 o existe mucha latencia solo escala a deepsek v4 flash para el grupo 2 


📌Para que sepas cómo vas a tener que clasificar el router o varios router ➡️➡️

Grupo 1 📌  del wordflow loop code Yaiwes con el ejambre de agente Seals Team YAIWES 

Grupo 2 📌 con los agente de el wordflow loops code Yaiwes con el pool de 20 agentes
Solo para el grupo 2 si se satura el cómputo o hay mucha latencia el router cambia la api por al de deepsek v4 pero son 6 grupos de trabajo que requieren api key  especializada que te voy a decir 
Como funciona o deberia funcionar router para grupo 2 
1. Las 4 api de Nvidia y cerebras si no responde o los modelos no están disponibles el router Salta para mis api locales 
2. Api locales del grupo 2 .
Si las api locales de esta lista están saturadas o con latencia salta a 
Deepsek v4 flash api 
3. Usa deepsek v4 
Así debería funcionar el router de grupo 2 
También la biblioteca de skills de huggueface instalada para grupo 2 
Caché 
Limite de ram 


➡️➡️➡️➡️➡️➡️


Grupo 0📌 osquestador 
comand Center y 
Neuro-Orchestrator-8B — 8B — orquestación/agentic.
MiroThinker-8B — 8B — razonamiento.
LFM2.5-8B-A1B — 8B total / ~1B activo — subagentes, loops agentic.
OpenThinker3-7B — 7B — razonamiento.
➡️ 

Grupo 1 📌 
Para trabajo de arquitectura decidir y funciones sin generar code el router usa solo usa ➡️
LFM2-2.6B — 2.6B — worker rápido, clasificación y extracción
Nemotron Nano 9B v2 — 9B — razonamiento, arquitectura y reparación.
Nanbeige4.2-3B — 3B — 🧑‍💻 MODELO DE CODE / agentic.
Qwen3-0.6B — 0.6B — ultraligero/router/worker.
Qwen2.5-1.5B-Instruct — 1.5B — worker ligero.
Qwen2.5-0.5B-Instruct — 0.5B — worker ultraligero.

📌Para trabajo de code el router canbia ➡️
Qwen3.5-9B — 9B — 🧑‍💻 MODELO DE CODE principal local.
KAT-Coder Q5 KAT-Coder Q5, Seed-Coder 8B, parámetros no indicados; Q5 = cuantización — 🧑‍💻 MODELO DE CODE, reparación/escalamiento

➡️➡️➡️➡️➡️➡️➡️

Grupo 2 📌
Modelos que deben trabajar local por máximo 26 de ram  quanrificado para no saturar el procesador + caché 
Muse Glimmer 30B — 30B — 🧑‍💻 MODELO DE CODE / agentic, multimodal.
Laguna XS 2.1 — 33B total / 3B activos — 🧑‍💻 MODELO DE CODE / agentic, router y long-horizon.
DeepSeek-Coder — variante/peso no especificado en tus archivos — 🧑‍💻 MODELO DE CODE.
DeepSeek v4 flash 
➡️➡️➡️➡️➡️➡️



📌Grupo fromtend y fábrica de UI y interface UI staff pendientes por clasificación 
OLMo-3-7B-RL-Zero — 7B — razonamiento/RL.
Ternary-Bonsai-27B-GGUF — 27B — general; GGUF.
OTel-2.0-LLM-31B-IT — 31B —
debe estar instalado 
Kandinsky-5.0-T2I-Lite — peso exacto no indicado — generación de imagen.
Qwen-Image —
FLUX.1-schnell —
Wan2.2-Animate-14B — 14B — vídeo/animación.
LTX-Video — peso exacto no indicado en tus archivos — vídeo.
HunyuanVideo —
OPT-125M — 125M — ultraligero/pruebas.
Skywork-OR1-Math-7B — 7B — matemáticas/razonamiento.
MiroThinker-8B — 8B — razonamiento.
Neuro-Orchestrator-8B — 8B — orquestación/agentic.
CrystalSonic-4B — 4B — ligero.
Hunyuan-7B-Instruct — 7B — general.
Yuan3.0-Flash — 40B total / ~3.7B activos — MoE.
IBM todos los modelos 
Granite-4.0-7B — 7B — general/enterprise.
Granite-4.2-3B — 3B — ligero/general.
Ling-3.0-flash
Ling-3.0-flash-VL
Qwen3-0.6B — 0.6B — ultraligero/router/worker.
Qwen2.5-1.5B-Instruct — 1.5B — worker ligero.
Gemma 4 e2a 
LFM2.5-8B-A1B — 8B total / ~1B activo — subagentes, loops agentic.
LFM2-2.6B — 2.6B — worker rápido, clasificación y extracción.


➡️➡️➡️➡️➡️➡️➡️➡️

los 3 métodos de procesamiento 
Los necesito pero primero necesito resolver la prioridad de el chat con los requisitos que. Te puse como primer paso Mónico chat + deepsek v4 flash y pro + Kimi k 3+ Nvidia api + mínimax M3 + agentes que pasan por medio de el router con agente y sin agente   coneccion con el Github y huggueface Now 

Después todo lo demás la prioridad CHat tu objetivo principal 

Mis instrucciones imput block verbartin 1 a 1 la escribes en el claude notas + readme  arquitectura router inteligente universal+ Craxy wall bitácora stated JSON handoff 


Alguna duda ? 

Dieme si te quedo claro ? 

Dime qué te falta para completar el chat ?

---FIN---

(Los tres documentos adjuntos a este mensaje están en `Claude notas/REFERENCIAS-ADJUNTAS-INPUT-05-VERBATIM.md`.)

## Trabajo realizado
- Registro verbatim: `Claude notas/INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md` (commit `6f48f156`) y `Claude notas/REFERENCIAS-ADJUNTAS-INPUT-05-VERBATIM.md` (commit `c87e2e24`).
- Auditoría del catálogo del router HF frente a las listas del Director: `.github/workflows/riu-router-catalog-audit.yml` (commit `bd60dd58`), run `35489878690`, check-run `106022882650`.
- IDs del Hub resueltos con búsqueda (`hf_fs`, 2026-09-19): `yasserrmd/Neuro-Orchestrator-8B` (repo de un usuario, 69 descargas), `LiquidAI/LFM2.5-8B-A1B`, `open-thoughts/OpenThinker3-7B`, `nvidia/NVIDIA-Nemotron-Nano-9B-v2`, `Nanbeige/Nanbeige4.2-3B`, `Qwen/Qwen3.5-9B`, `Kwaipilot/KAT-Coder-V2.5-Dev` (+ GGUF de terceros), `ByteDance-Seed/Seed-Coder-8B-Instruct`, `poolside/Laguna-XS-2.1` (+ GGUF oficial), `meta-models/Muse-Glimmer-30B` (+ GGUF unsloth, NVFP4 nvidia). Sin repo original claro: MiroThinker-8B (solo GGUF de terceros de v0.1 SFT/DPO); LFM2-2.6B (aparece `LiquidAI/LFM2.5-2.6B`).

## Evidencia (runner real)
- Run `35489744898` (check-run `106022524659`, HEAD `8717a385`): 36 tests passed; E2E por el gateway HTTP 200 con `moonshotai/Kimi-K3`, `deepseek-ai/DeepSeek-V4-Flash`, `-V4-Flash-0731`, `-V4.1-Flash`, `-V4-Pro`, `-V4-Pro-0813`, `MiniMaxAI/MiniMax-M3` (y M2/M2.1/M2.5/M2.7/M1-80k). `Qwen/Qwen3-0.6B` y `openai-community/gpt2`: 503.
- `HF_TOKEN_1`: cuenta `COMAND-CENTER-1`, token fine-grained, `global=discussion.write,post.write`, 1 scope. Hace inferencia; NO puede crear Spaces ni escribir repos/buckets desde un workflow.
- Catálogo del router HF: 138 modelos. De las listas del Director SIRVEN: `Qwen/Qwen3.5-9B`, `meta-models/Muse-Glimmer-30B`, `ibm-granite/granite-4.2-{3b,8b,30b}`, `google/gemma-4-{26B-A4B,31B}-it`, `inclusionAI/Ling-3.0-flash{,-Fin,-VL}`, `prism-ml/Ternary-Bonsai-27B-{AWQ-4bit,gguf}`. NO SIRVEN (0 providers): Neuro-Orchestrator-8B, MiroThinker-8B, LFM2.5-8B-A1B, OpenThinker3-7B, LFM2-2.6B, Nemotron Nano 9B v2, Nanbeige4.2-3B, Qwen3-0.6B, Qwen2.5-1.5B/0.5B-Instruct, KAT-Coder, Seed-Coder, Laguna XS 2.1, DeepSeek-Coder, OLMo-3, Hunyuan, Yuan3, Skywork-OR1, OPT-125M, OTel-2.0, y los de imagen/vídeo (FLUX, Qwen-Image, Kandinsky, Wan, LTX).
- Secrets del repo (nombres): `CEREBRAS_API_KEY_1..6`, `HF_TOKEN_1`, `RIU_GITHUB_PAT_FULL_ACCESO`. NO existen: `NVIDIA_API_KEY_*`, `GROQ_API_KEY_*`, `DEEPSEEK_API_KEY`, secrets de otras cuentas de GitHub, endpoint de modelos locales.

## Decisiones que bloquean cerrar el chat (Paso 1)
1. Ejecución de los modelos sin provider (Grupos 0/1 y parte del 2): el texto del Director pide "locales ≤26 GB RAM cuantizados" y a la vez "llamar al modelo remoto de HF sin descargar". Con el catálogo real, la segunda vía solo aplica a los modelos que SÍ sirven. Para el resto: (a) local GGUF cuantizado en una máquina definida, (b) NVIDIA NIM / Cerebras si sirven ese modelo, (c) HF Inference Endpoint dedicado (de pago). Requiere decidir el host y cambiar el contrato `REMOTE_INFERENCE_ONLY` para los locales.
2. Host del chat: HF Space Docker en `COMAND-CENTER-1` (el token actual no puede crearlo) o token con `repo.write`.
3. Almacenamiento MVP (4 sistemas): motor de "Data base"; SQLite; "Graphiti y graphyty" (¿uno o dos?; Graphiti necesita backend de grafo y embeddings); caché (disco o Redis); dónde persiste (bucket nuevo o `yaiwes-v54`); tipos y tamaño de adjuntos.
4. Secrets (solo nombres; valores por Settings → Secrets; rotar los pegados en chat): `NVIDIA_API_KEY_1..4`, `DEEPSEEK_API_KEY` (¿directa o vía router HF, que ya funciona?), `GITHUB_TOKEN_<alias>` por cuenta, `LOCAL_API_URL`/`LOCAL_API_KEY`.
5. Cuentas de GitHub del selector: alias y permiso lectura/escritura por cuenta.
6. Pool de agentes: lista (id, rol, grupo, modelo) o aprobar plantilla inicial.
7. IDs exactos ambiguos: MiroThinker-8B, LFM2-2.6B, Neuro-Orchestrator-8B (¿el de `yasserrmd`?).
8. Duplicidad del chat: Gradio (`gateway/hf_chat_mvp/`, llama a proveedores directo) vs gateway del Router (`/chat`).

## GAPs nuevos/actualizados
`GAP-MODELS-NO-PROVIDER-001` (≈19 modelos del Director sin provider en el router HF), `GAP-CHAT-DEPLOY-001`, `GAP-STORAGE-MVP-001` (DB + SQLite + Graphiti + caché + adjuntos, sin construir), `GAP-GH-MULTIACCOUNT-001`, `GAP-AGENT-POOL-001`, `GAP-SECRETS-MISSING-001`. `GAP-EXTERNAL-CREDENTIAL-SCOPE-001` sigue obsoleto (HF_TOKEN_1 infiere).

## Estado del nodo
`INPUT_REGISTRADO + AUDITORIA_CATALOGO_EJECUTADA`. Sin cambios de código en este nodo. Paso 2 no iniciado (orden del Director: no pasar al Paso 2 hasta cerrar el chat). STATE/CHECKPOINT/PLAN/Handoff siguen sin este nodo.

## Próximo delta seguro
Con respuestas a 1-8: construir capa de almacenamiento del chat (SQLite + adjuntos + ventana de documentos + caché) y selector de cuenta/agente; sin ellas, avanzar solo lo independiente: SQLite + adjuntos + documentos + caché en el gateway.
