# README — Arquitectura Backend

> **Estado:** BORRADOR E-07. Fuente canónica: `chat router/Workflow Loop code Yaiwes/01-PLAN/ROOT-MAP-T11.yaml`.

## Política de raíces

- No crear carpeta vacía; solo rutas físicas reales verificadas por read-back.
- Nota de transporte remoto: chat router/Workflow Loop code Yaiwes/03-ESTADO/data/*.json son transporte remoto vía GitHub contents API (ui_bridge._read), no archivos locales.
- Las rutas bajo `router inteligente universal/` se documentan como referencia; esta tarea no modifica el Router.

## Mapa canónico

### 01 — Chat frontend

- `chat router/Workflow Loop code Yaiwes/13-CHAT-UI-SUITE/`
- `chat router/ui/`
- `chat router/Workflow Loop code Yaiwes/space/`
- `router inteligente universal/integration/chat_mvp/chat_ui.html`
- `router inteligente universal/chat_space/`

### 02 — Plugins Hermes harness

- `router inteligente universal/plugins/`
- `router inteligente universal/deepseek-harness-router/`
- `chat router/Workflow Loop code Yaiwes/05-AGENTES/asistentes/`
- `router inteligente universal/enchufe/`

### 03 — Agente

- `chat router/Workflow Loop code Yaiwes/05-AGENTES/`
- `router inteligente universal/agents-yaiwes/`
- `router inteligente universal/agents/`
- `router inteligente universal/agent-microkernel/`

### 04 — Input y buscadores

- `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/buscadores.py`
- `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/verificador.py`
- `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/evidence_pack.py`
- `chat router/Workflow Loop code Yaiwes/01-PLAN/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md`

### 05 — Workflow

- `chat router/Workflow Loop code Yaiwes/01-PLAN/PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml`
- `chat router/Workflow Loop code Yaiwes/01-PLAN/ORQUESTADOR-DE-TRABAJO.yaml`
- `router inteligente universal/integration/chat_mvp/dag.py`

### 06 — Memoria

- `chat router/04-MEMORIA/`
- `router inteligente universal/integration/chat_mvp/memory_runtime.py`
- `router inteligente universal/integration/chat_mvp/memoria_loader.py`

### 07 — Formato de salida

- `router inteligente universal/enchufe/`
- `router inteligente universal/integration/chat_mvp/fables_adapter.py`
- `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/puerta.py`

### 08 — Componentes asociados

- `router inteligente universal/Componente open soure router inteligente universal/`
- `router inteligente universal/Componentes del Router/`

### 09 — Tools y pools

- `router inteligente universal/integration/chat_mvp/tool_contracts.py`
- `router inteligente universal/integration/chat_mvp/model_pool.py`
- `router inteligente universal/integration/chat_mvp/providers.py`
- `chat router/Workflow Loop code Yaiwes/05-AGENTES/gobierno/mirror_factory.py`

### 10 — Otros

- `router inteligente universal/Banco de claves/`
- `router inteligente universal/scripts/`
- `chat router/Workflow Loop code Yaiwes/00-INSTRUCCIONES/`

### 11 — Wordflow LOOP Yaiwes (copiado de agentes via motor_3, VERIFIED_CLOSED)

- `chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/runtime/`
- `chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/wordflow_loop/`
- `chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/Crazy Wall Orquestador/`
- `chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/backend/`
- `chat router/Workflow Loop code Yaiwes/_copias-anteriores/➡️📂motores de descarga extracción copiado movimiento archivos agentes/`
- `chat router/Workflow Loop code Yaiwes/_copias-anteriores/➡️📂 Wordflow LOOP Yaiwes/`

## Alcance de este borrador

- Reproduce las 11 raíces y sus rutas declaradas en ROOT-MAP-T11.
- No declara componentes externos como activos por el solo hecho de existir una ruta.
- No sustituye la suite final, la evidencia global ni el cierre E-09..E-12.
