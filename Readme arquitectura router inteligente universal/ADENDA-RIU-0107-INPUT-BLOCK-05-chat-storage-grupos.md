# ADENDA A LA ARQUITECTURA — RIU-0107 — INPUT BLOCK 05 (chat MVP, almacenamiento, grupos 0/1/2)

Anclas: `../Claude notas/INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md` · `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0107-INPUT-BLOCK-05-chat-storage-grupos.md`.
Esta adenda NO modifica `README.md` (arquitectura consolidada hasta RIU-0094); se añade como archivo aparte porque la API de GitHub no permite append y reescribir el README arriesga el historial. Fusionar al README cuando el Director autorice.

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

## Requisitos de arquitectura que contiene el input (extracto estructurado; el verbatim de arriba manda)
| Tema | Requisito del Director | Estado al 2026-09-20 |
|---|---|---|
| Chat (Paso 1, prioridad única) | Chat MVP con DeepSeek V4 Flash y Pro, Kimi K3, MiniMax M3, API de NVIDIA; con agente y sin agente, pasando por el Router; conectado a GitHub y Hugging Face | Chat sobre el Router probado en runner (HTTP 200 con Kimi K3, DeepSeek V4, MiniMax M3); NVIDIA sin keys; sin agentes; sin host |
| Selector de cuenta GitHub | Cambiar entre cuentas de GitHub desde el selector | No construido; faltan cuentas y tokens |
| Almacenamiento MVP en HF | Entorno "Mvp almacenamiento para AI": Data base, SQLite, Graphiti/"graphyty", caché; adjuntos y ventana de documentos cableados a los 4 sistemas | No construido; decisiones pendientes (RIU-0107) |
| Grupo 0 (orquestador) | Command Center + Neuro-Orchestrator-8B, MiroThinker-8B, LFM2.5-8B-A1B, OpenThinker3-7B | Sin provider en el router HF |
| Grupo 1 (Seals Team YAIWES, 50+ agentes) | Arquitectura/decisión sin generar código: LFM2-2.6B, Nemotron Nano 9B v2, Nanbeige4.2-3B, Qwen3-0.6B, Qwen2.5-1.5B/0.5B. Código: Qwen3.5-9B principal, KAT-Coder Q5 / Seed-Coder 8B para reparación | Solo Qwen3.5-9B tiene provider; el resto no |
| Grupo 2 (pool de 20 agentes) | Cascada: 1) 4 API de NVIDIA y Cerebras; si no responden → 2) API locales del grupo 2 (≤26 GB RAM cuantizados: Muse Glimmer 30B, Laguna XS 2.1, DeepSeek-Coder, DeepSeek v4 flash); si saturan o hay latencia → 3) API DeepSeek V4 Flash | No implementado; NVIDIA sin keys |
| Cómputo | Si se saturan 3 procesadores, saltar a 7 más; al llegar a 10 o con mucha latencia, escalar solo a DeepSeek V4 Flash (grupo 2) | No implementado (existe `hf_scheduler.py` HF1→HF2→HF3, RIU-0074) |
| Agentes | 50+ agentes "Seals Team YAIWES", con "mirror"/duplicación 50-100 veces, sin descargar modelos | Keystore MAXBRY-001..100 listo y aceptado por el gateway |
| Grupo frontend / Fábrica de UI | Pendiente de clasificación (lista larga: OLMo, Bonsai, OTel, imagen/vídeo, IBM Granite, Ling, Gemma 4, Qwen, LFM) | Sin clasificar |
| Paso 3 | Revisar el router de Fables + lo que adelantó "sol gpt" + los 3 métodos de procesamiento | Referencias en `../Claude notas/REFERENCIAS-ADJUNTAS-INPUT-05-VERBATIM.md`; no iniciado |
