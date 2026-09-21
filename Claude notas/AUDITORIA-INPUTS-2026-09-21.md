# AUDITORÍA DE LAS INSTRUCCIONES DEL DIRECTOR (inputs) — 2026-09-21

Hecha por Claude (Paso 2 de `INPUT-VERBATIM-2026-09-21-p-…`). Fuente: los `INPUT-VERBATIM-*` de esta carpeta. Prioridad del Director: 1) CHAT, 2) HUGGING FACE, 3) MODELOS DE IA EN HUGGING FACE. Estados: HECHO (con evidencia), PARCIAL, PENDIENTE, BLOQUEADO.

## 1. CHAT
| Instrucción (origen) | Estado | Nota |
|---|---|---|
| Chat MVP con selector de proveedor y modelo, sin agente / con agente (chat-mvp) | HECHO | probado en runner (57 y 39 tests) |
| Cambiar de cuenta de GitHub, leer/guardar archivos (chat-mvp) | HECHO | cuentas del banco; tokens nuevos sin probar |
| Documentos adjuntos, SQL, grafo, caché (chat-mvp) | HECHO | Graphiti real PENDIENTE |
| Caché para pagar menos (`RIU-0106`) | HECHO | 24 % de entrada en caché del proveedor medido |
| NVIDIA primero en el selector (d) | HECHO | pool de claves con respaldo |
| Interfaz al día (banco, trabajos, DAG, grupos, costos) (j) | PENDIENTE | agente de chat |
| Publicarlo (e, k, l) | BLOQUEADO→LISTO | Vercel: el Director dice que ya está; puente en el Paso 3 |
| Plantilla fija YAML+JSON+Python y Crazy Wall/handoff permanentes en el chat (b) | PENDIENTE | |
| Buscador como contexto de entrada con interruptor (j) | PENDIENTE | motor existe en GitHub Actions |
| Agentes buscador, escritor web con capturas, descargas (d) | PENDIENTE | |
| Claves Groq/Cerebras en el banco (n) | HECHO | en el banco de ejecución; sin probar contra los proveedores |
## 2. HUGGING FACE
| Instrucción | Estado | Nota |
|---|---|---|
| Modelos Kimi K3 / DeepSeek V4 / MiniMax M3 cobrados en la cuenta de HF (b) | HECHO | 200 en runner; cuenta con método de pago |
| Chat en Space de HF (e, k) | BLOQUEADO | HF pide PRO para Docker |
| Modelos por pesos remotos en un Job (`hf://…:/model:ro`) (k) | PENDIENTE | agente 2 escribe el comando; falta correrlo; el Job de prueba dio ERROR |
| Probar modelos en el procesador HF de 32 GB (e) | PENDIENTE | mismo Job |
| 3 nodos HF con un servidor cada uno y salto por carga (k) | PENDIENTE | agente 3 escribe la lógica; falta desplegar |
## 3. MODELOS DE IA EN HUGGING FACE
| Instrucción | Estado | Nota |
|---|---|---|
| LFM2.5-1.2B-Thinking, Qwen3-0.6B, K2-Horizon-0.9B, Nanbeige4.2-3B, NanoJev, Decider-0.8B/2B: existencia y formato (i, j, k) | HECHO | `RIU-0119`; agente 1 los pasa a un registro |
| Laya-421M, Verdict-151M (j) | PENDIENTE | Laya parcial; Verdict no encontrado: falta el enlace |
| Nanbeige Q4 (comunidad) con el fork de llama.cpp; benchmark Nanbeige solo vs 3 nodos (k, chat-mvp) | PENDIENTE | |
| Decider/NanoJev como capa de decisión delante de DeepSeek (chat-mvp, j) | PENDIENTE | |
| Jev en Vercel AI Gateway (j) | BLOQUEADO | falta `AI_GATEWAY_API_KEY` |
## 4. ROUTER (después de las prioridades)
| Instrucción | Estado | Nota |
|---|---|---|
| Router para picos y respaldo (h) | HECHO | `resilience.py`, 39 tests |
| NVIDIA y MiniMax en hora pico, DeepSeek V4 fuera de pico (j) | EN CURSO | agente 4 |
| Enchufe Universal de Fables integrado (e) | PENDIENTE | parte 2 pasa sus pruebas; parte 1 tiene un defecto en su prueba 6 |
| Integrar Jev como "thinking" en `dataset Yaiwes` (o) | PENDIENTE | tras el Paso 3 |
| Componentes del Router integrados (o) | EN CURSO | agentes 3 y 4 |
## 5. Reglas del Director vigentes
Anotar antes de ejecutar y validar; respuestas cortas; no esperar más de 1 minuto; delegar con DSL DAG; Claude no cambia instrucciones ni herramientas sin autorización; los agentes de `agent-microkernel/` no se borran; claves solo por el banco; Claude orquesta y los agentes ejecutan.
