## RIU-0105 — CHAT MVP CONECTADO (proveedores, GitHub multi-cuenta, almacenamiento en 4 sistemas) — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Entrada pendiente de fusionar al final de `BITACORA-CRAZY-WALL.md`
(no se reescribió el archivo de la bitácora para no arriesgar historial; ver `Claude notas/CONSEJOS-CONTINUIDAD-Y-RECUPERACION.md` §8 y §15).

### Input literal del Director
`Claude notas/INPUT-VERBATIM-2026-09-20-chat-mvp.md`

### Trabajo y evidencia
- Chat: `router inteligente universal/integration/chat_mvp/` (app, router, providers, github_tools, store, chat_ui.html) + selector HF en `integration/huggingface/chat_catalog.py` y `chat_executor.py`.
- Runner `ubuntu`, workflow `RIU Chat MVP Verify`, run `35504526944` (commit `abd1696`): E2E por `/chat/send` → Enchufe → RedUniversal → proveedor: Kimi K3, DeepSeek V4 Flash, DeepSeek V4 Pro y MiniMax M3 = 200. Documento adjunto leído por el modelo, modo con agente 200, caché 2.º envío `cached=True`, historial persistido, cuentas GitHub `ci-a`/`ci-b` 200, almacenamiento 18 msgs / 21 aristas / 1 hit / 2 docs.
- Tests: 47 passed + 1 failed (aserción propia, corregida en `e6afe76`).
- Detalle completo y flags: `Claude notas/RIU-0105-registro-chat-mvp.md`.

### GAPs / flags
`GAP-HF-WRITE-TOKEN-001` (sin `HF_WRITE_TOKEN`: no se despliega el Space ni se sincroniza el bucket) ·
`GAP-NVIDIA-GROQ-KEYS-001` · `GAP-CEREBRAS-402-001` · `GAP-LOCAL-BASE-URL-001` · `GAP-GITHUB-SECOND-ACCOUNT-001` ·
`GAP-GRAPHITI-REAL-001` · `GAP-BENCH-NANBEIGE-QWEN9B-001` (runner de 4 vCPU, se pidió 8) · `GAP-AGENT-POOL-DEFINITION-001` · `GAP-CONTRACT-VERSION-V3-V4-001`.

### Estado del nodo
`CHAT_MVP_EJECUTADO_EN_RUNNER; DESPLIEGUE_HF_BLOQUEADO_POR_CREDENCIAL`. Ningún PASS global. `global_closed=false`.

### Próximo delta seguro
Verify posterior a `e6afe76` → con `HF_WRITE_TOKEN` despachar `Deploy Chat MVP Space` → repetir E2E con NVIDIA/Groq → Paso 3 (router por grupos) solo con el chat desplegado.
