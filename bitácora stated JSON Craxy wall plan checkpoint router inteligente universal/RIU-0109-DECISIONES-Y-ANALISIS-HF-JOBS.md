# RIU-0109 — DECISIONES D1-D7 DEL DIRECTOR + ANÁLISIS DE HF JOBS COMO FALLBACK — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Alcance de escritura: solo este repo (P3). Continúa `RIU-0108-PLAN-MAESTRO-CHAT-MVP.md`.
Input textual: `Claude notas/INPUT-BLOCK-07-VERBATIM.md` y `Readme arquitectura router inteligente universal/ADENDA-RIU-0109-HF-JOBS-FALLBACK-y-decisiones.md` (mismo texto, más el análisis completo). Este mensaje no traía credenciales.
Estado del nodo: DECISIONES REGISTRADAS + ANÁLISIS HECHO. No se construyó código del stack (el plan sigue en S0).

## Trazabilidad instrucción por instrucción
| # | Cita textual | Atención |
|---|---|---|
| I-07.01 | "Anota todo esto en los archivos de ➡️📂 readme arquitectura router inteligente universal. Md" | ADENDA-RIU-0109 en esa carpeta |
| I-07.02 | "Todo imput block verbartin 1 a 1" | verbatim en `Claude notas/INPUT-BLOCK-07-VERBATIM.md` y en la adenda |
| I-07.03 | Respuesta 1: "Revisa Claude WebUI, o Claude.ai UI Clone … LibreChat o open WebUI … más rápido menos trabajo de programación … conectar MCp para intervenir en la conversión" | D1, sección 1 |
| I-07.04 | Respuesta 2: "Almacenamiento en huggueface" | D2, sección 2 |
| I-07.05 | Respuesta 3: "AES-256-GCM + contraseña maestra … passkey/WebAuthn después" | D3 aprobado; S2 sin cambios |
| I-07.06 | Respuesta 4: "Si" | D4: `HF_TOKEN_1` se queda en GitHub solo para el despliegue |
| I-07.07 | Respuesta 5: "Revisa a ver si está en el repo de agentes o fromtend o router" | D5, sección 3 |
| I-07.08 | Respuesta 6: "Ambas" | D6: `LiquidAI/LFM2-2.6B` y `LiquidAI/LFM2.5-2.6B` en `groups.yaml` |
| I-07.09 | Respuesta 7: "dime si eso lo resolveria / Analiza" | D7, sección 4 (análisis completo en la adenda) |
| I-07.10 | Texto sobre HF Jobs (montar `hf://`, costes por minuto, puerto expuesto, fallback tras Inference Providers) | adenda; arquitectura de fallback en la sección 4 |

## 1. D1 — Chat open source: Open WebUI
Evidencia (motor de búsqueda, sin LLM; `ws-35493826829`, `ws-35493834208`, `ws-35495178189`, `ws-35495181602`):
- "Claude WebUI / Claude.ai UI clone": lo que hay no sirve como base. `13point5/open-artifacts` es de octubre de 2024 y llama a Anthropic/OpenAI con claves del usuario; `Damienchakma/Open-claude` es una réplica mínima; `siteboon/claudecodeui` es una interfaz para Claude Code/CLI, no un chat sobre un endpoint propio. Ninguno ofrece endpoint OpenAI-compatible propio + RAG + MCP.
- Open WebUI: conexión OpenAI-compatible (apunta al gateway del Router), RAG y gestión de archivos, API REST, Pipelines/Functions/Tools en Python para intervenir en la conversación, y MCP nativo por Streamable HTTP (lo añade un administrador una vez y se limita con control de acceso; stdio vía proxy `mcpo`). Existe una función comunitaria de Artifacts y un preset "Claude Clone". Un solo contenedor. Licencia con cláusula de marca desde v0.6.6: la doc dice que no aplica con 50 usuarios o menos en 30 días.
- LibreChat (alternativa válida): MIT, `librechat.yaml` para endpoints custom, agentes con MCP, RAG API; exige MongoDB y servicios extra.
- Decisión: Open WebUI. Menos programación: se configura, no se escribe un chat. La intervención en la conversación se hace con MCP (servidor del Router, S3.6) y con un Filter/Pipeline. Respaldo: LibreChat si la licencia molesta.
- No verificado en esta sesión: que Open WebUI arranque en un Space Docker de HF con volumen de bucket (lo comprueba S3.5).

## 2. D2 — Almacenamiento en Hugging Face
Space Docker de `COMAND-CENTER-1` con un Storage Bucket adjunto como volumen (soportado desde 2026-03-31). El bucket guarda archivos originales, `vault.db` cifrado y volcados. PostgreSQL y FalkorDB trabajan sobre disco local del Space y se vuelcan al bucket periódicamente y en el arranque se restauran (los buckets son almacenamiento de objetos: mi criterio de ingeniería, no verificado con fuente, es no ejecutar bases de datos directamente sobre ellos). Alternativa a evaluar si falla: servicios gratuitos externos.

## 3. D5 — Logins de las cuentas de GitHub: NO están en los repos
Búsqueda en el código de `maxbry123-commits` (incluye repos privados): `planeta` y `planeta123` → 0 resultados; `abc123` → solo coincidencias irrelevantes en la documentación de skills de `TAREA-1`. La carpeta `Github coneccion` solo contiene workflows. `Maxbry 123` corresponde al menos a `maxbry123-commits` (dueño del repo, aún sin confirmar que sea la cuenta del token que pegaste). Falta el login público de `abc123` y de `planeta 123` (no son secretos). `accounts.yaml` queda con esos dos como `PENDING_LOGIN`.

## 4. D7 — HF Jobs para los modelos sin proveedor: SÍ, con condiciones
Detalle y evidencia en la adenda. Resumen: cada modelo sin proveedor es un repo del Hub; un Job por demanda ejecuta `vllm serve` o llama.cpp sin copia persistente. Condiciones: (1) ampliar el contrato con la clase `HF_JOB_EPHEMERAL_SERVING`; (2) estados COLD/STARTING/READY/DRAINING/STOPPED y primer token en minutos; (3) `--expose` con `--api-key` del Secret Bank, timeout explícito (30 min por defecto), tope de gasto y vigilante; (4) un servidor por modelo compartido por muchos agentes; (5) no cubre imagen ni vídeo. Alternativa más simple de consumir: Inference Endpoints con escala a cero.
Permisos: `HF_TOKEN_1` tiene `job.write` y `inference.endpoints.write` (run `35493843251`).

## 5. Cambios al plan RIU-0108
- S2: D3 aprobado; D4 aprobado.
- S3.1 CERRADO = Open WebUI. Añadir S3.6: servidor MCP del Router (herramientas de lectura del estado del Router y de la memoria) conectado a Open WebUI por Streamable HTTP, más un Filter para intervenir en la conversación.
- S4: almacenamiento en HF según D2.
- S5: bloqueado hasta tener los 2 logins.
- S7: `groups.yaml` incluye ambos LFM2 y añade S7.3 (prueba de servir un modelo pequeño en un Job: lanzar, llamar `/v1/chat/completions`, medir arranque en frío y coste, cancelar; requiere aprobar un gasto de céntimos) y S7.4 (enmienda del contrato del registry `HF_JOB_EPHEMERAL_SERVING`).
- S0 sigue siendo lo primero: escáner de credenciales.

## 6. GAPs
`GAP-GH-LOGINS-001` (faltan 2 logins), `GAP-CONTRACT-JOB-SERVING-001` (enmienda del contrato), `GAP-JOB-SERVING-SMOKE-001` (prueba con gasto), `GAP-OPENWEBUI-SPACE-001` (arranque en Space sin verificar). `GAP-CHAT-OSS-CHOICE-001` cerrado. `GAP-STORAGE-HOSTING-001` cerrado (HF).

## 7. Próximo delta seguro
S0 (escáner de credenciales) → S1 (`Chat Mvp/` con `groups.yaml` y `accounts.yaml`) → S2.1-2.4 (Secret Bank).
