# router-universal-router-inteligente-

> **Código: GitHub (fuente única).** HuggingFace es **espejo + auto-pull mínimo** (lo mínimo para
> servir y actualizar la UI). Vercel publica la interfaz y dispara el trigger del watchdog al encender.
> Índice de navegación: [`CODE_INDEX.md`](CODE_INDEX.md) · Cableado maestro: [`SYSTEM_WIRING_REGISTRY.yaml`](SYSTEM_WIRING_REGISTRY.yaml).

app_file: router-mvp/mvp/app.py

## Qué es este repositorio

Router de聊天 y agentes con **Harness DeepSeek** como centro de distribución: el prompt raíz, las
fichas, los motores, los agentes, la cola, el loop y el watchdog. El cableado oficial vive en
`connections/` y el registro maestro en `SYSTEM_WIRING_REGISTRY.yaml`.

## Las 11 entradas

| # | Componente | Ruta |
|---|---|---|
| 1 | Chatbot | `chat-router/chatbot/` |
| 2 | Chat Router (frontend y backend Chat YAIWES) | `chat-router/chat/frontend/` · `chat-router/chat/backend/` |
| 3 | SWE CODE free | `chat-router/SWE CODE free/` |
| 4 | SWE CODE | `chat-router/SWE CODE/` |
| 5 | Router MVP | `router-mvp/` |
| 6 | Router SWE CODE | `chat-router/SWE CODE/mini_router.py` |
| 7 | Harness DeepSeek | `chat-router/harness/` |
| 8 | Sistema central de conexión y cableo | `SYSTEM_WIRING_REGISTRY.yaml` · `connections/` · `chat-router/MAPA.md` |
| 9 | Agentes | `chat-router/agentes/` |
| 10 | Loop, cola y watchdog | `chat-router/Loop cola wachdog/` |
| 11 | System prompt y motores | `router-mvp/raiz_fichas_prompt/` · `chat-router/motores/` |

## Cableado y estado

- **Registro maestro de integraciones** (centro de distribución): [`SYSTEM_WIRING_REGISTRY.yaml`](SYSTEM_WIRING_REGISTRY.yaml)
  — servicios, conexiones, contratos, healthchecks, fallback y estado de evidencia.
- **Inventario oficial de pares**: [`connections/registry.yaml`](connections/registry.yaml) ·
  [`connections/topology.yaml`](connections/topology.yaml) · [`connections/endpoints.yaml`](connections/endpoints.yaml) ·
  [`connections/healthchecks.yaml`](connections/healthchecks.yaml).
- **Informe central de conexiones** (sondas reales): [`connections/bridge_report.json`](connections/bridge_report.json).
- **Bitácora del cableado**: [`connections/wiring_changelog.md`](connections/wiring_changelog.md) ·
  [`connections/wiring_history.jsonl`](connections/wiring_history.jsonl).
- **Handoffs por área**: [`handoff/docs/`](handoff/docs/) — FRONTEND · AGENTS · MODELS · MEMORY · HARNESS.
- **Estado y plan**: [`kernel/KERNEL.yaml`](kernel/KERNEL.yaml) · [`kernel/DAG.yaml`](kernel/DAG.yaml) ·
  [`kernel/GUIDE.md`](kernel/GUIDE.md) · [`kernel/GAP_PLAYBOOK.md`](kernel/GAP_PLAYBOOK.md) ·
  [`kernel/INPUT_BLOCK.yaml`](kernel/INPUT_BLOCK.yaml) (congelado) ·
  [`kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`](kernel/INPUT_BLOCK_YAIWES_CABLEADO.md) (objetivos, verbatim).

## Umbral para marcar una conexión como `ACTIVE`

Las siete condiciones, todas obligatorias: autenticación válida · conexión real con el proveedor ·
solicitud de inferencia ejecutada · respuesta válida del modelo · tiempo de respuesta registrado ·
sin errores críticos · **nada de superficial**. Una conexión que solo está configurada **no** está activa:
las que no cumplen el umbral se quedan en `pending_audit` y su healthcheck lo refleja en el informe del puente.

## Reglas de la casa

1. GitHub es la fuente del código; HuggingFace es espejo y auto-pull; Vercel es frontend.
2. Servidores de pago con 32 GB de RAM y CPU. Cola: al 85 % salta al siguiente; 15 min sin actividad duerme;
   1 modelo local por servidor; hasta 3 servidores en cola; botón ON/OFF permanente en la UI.
3. Sin GitHub Actions, sin LFS, sin despliegue nuevo en Vercel o HuggingFace sin autorización.
4. Secretos solo por entorno. Ninguna clave se rota ni se toca sin orden expresa del owner.
5. Los motores son intocables: `research_prepass.py` sigue **sin autorizar** y por tanto **intacto**.
6. Nada se borra sin análisis de dependencias (lo que sobra va a `_quarantine/`).
7. Cada job deja su evidencia en el Dataset de auditoría (`20261104-kernel01/<job>/result.json`).

## Operación

```bash
# republicar una rama limpia (el pack thin viaja solo con los objetos nuevos)
python ops/push_parallel.py            # segmentos en paralelo + un empuje final
python ops/push_8_parts.py             # variante secuencial por tramos
# comprobaciones del cableado
python ops/wiring_check.py .           # gate de cableado del árbol actual
python ops/bridge.py                   # informe central de conexiones (sondas reales)
```

Estado y plan completo: `kernel/KERNEL.yaml`. Rollback: etiqueta `pre-reorg-20261104-kernel01` ·
`safety/pre-reorg-original-20261104-kernel01` · rama `respaldo-main-pre-swap-20261104-kernel01` ·
bundle de 8 GB en el Dataset (`backups/20261104-kernel01.bundle`).
