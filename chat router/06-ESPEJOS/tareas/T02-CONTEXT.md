# T02 — CONTEXTO COMPACTO DE EJECUCIÓN

Fuente: documentos 22/23 + `05-AGENTES/AGENTES.yaml`.
Este archivo NO cambia el diseño; elimina texto histórico para reducir latencia del ejecutor.

## Objetivo operativo

### YaiwesHive — doc 23

`goal`
→ Rowboat.submit
→ Hermes.plan + OpenClaw.plan
→ crítica cruzada
→ Hermes.synthesize
→ OpenClaw.review_plan
→ Sheriff.validate
→ Ruflo.init_swarm
→ Ruflo.dispatch por task
→ Sentinel.inspect
→ Hermes.review + OpenClaw.review
→ si discrepan: reconsider máximo 2 rondas
→ Judge.decide
→ PASS / REVISE / BLOCK

Autoridad:
- Rowboat: entrada/contexto/delegación; no ejecuta.
- Hermes/OpenClaw: planificación, debate y revisión.
- Sheriff: código determinista.
- Ruflo: orquestación/dispatch.
- Sentinel: watchdog determinista.
- Judge: cierre determinista.

### EngineeringLoop — doc 22

`request`
→ ClaudeArquitecto.design
→ GrokEjecutor.execute
→ ClaudeRevisor.review
→ si no PASS: GrokEjecutor.correct; máximo 3 rondas
→ MetaEquipo.review_parallel ×4 con `asyncio.gather`
→ agregar findings
→ si hace falta: MetaFixer.correct UNA vez
→ MetaEquipo.review_parallel ×4 nuevamente
→ todos PASS = PASS; si no = REVISE

Los cuatro Meta inspeccionan en paralelo. No editan en paralelo.

## Contrato de Router

Todos los adaptadores llaman a `RouterCliente.chat(prompt, rol)`.
- POST `<LIVE_URL>/chat/send`
- JSON: `{"message": prompt, "max_tokens": ...}`
- headers: Bearer HF_TOKEN + X-API-Key RIU_ROUTER_API_KEY cuando existan
- 3 intentos
- `SIMULADO=1`: CERO red, respuestas JSON deterministas por rol

Si la respuesta de un adaptador no es JSON válido:
`{"approve": false, "status": "REVISE", "issues": ["json"]}`

## Reglas de implementación rápida

1. No vuelvas a leer/reescribir documentos 22/23.
2. Implementa primero `router_cliente.py` + `agentes.py`.
3. Luego `colmena.py`.
4. Después tests.
5. Ejecuta una sola suite completa.
6. Corrige únicamente el fallo observado.
7. No regeneres archivos que ya pasan.
8. Mantén cada archivo <500 líneas.
