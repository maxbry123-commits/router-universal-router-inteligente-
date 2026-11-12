/Main/
├── memoria/                          ← renombrar desde Memoria/ (G1)
│   ├── memoria-yaiwes/
│   ├── hf_datasets/
│   └── componentes/                  ← 18 componentes (verificar postgres)
├── ROUTER MVP v1/                    ← plano de datos (sin cambios)
├── router_llm_hf/                    ← plano de control (sin cambios)
├── control huggueface/               ← control de Spaces
├── llm system HF/                    ← modelos
├── chat-router/
│   └── chat/
│       ├── backend/deepseek_harness/ ← harness + tools MCP
│       └── frontend/                 ← UI + panel Memory OS
├── SATÉLITE CENTRAL CONECCION/       ← registro de cableado
├── connections/                      ← registry.yaml
├── handoff central/                  ← handoff README
└── engine/                           ← NUEVO: orquestador
    ├── orchestrator.py               ← ejecuta F1→F10
    ├── adapters.py                   ← aisla firmas de componentes
    ├── swe_code_free_tool.py         ← tool MCP “SWE CODE FREE”
    └── tests/                        ← pruebas de integración

Handoff de URLs para auditar el cierre

Todas las rutas del sistema, con su URL canónica. El handoff central está en handoff central/README.md y el registro de conexiones en connections/registry.yaml.

| # | Componente | Rama / Ruta | URL de handoff |
|---|---|---|---|
| 1 | Router 1 · plano de datos | ccr-f01c3de9-bmry0s / ROUTER MVP v1/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1 |
| 2 | Router 2 · plano de control (router_llm_hf) | ccr-f01c3de9-bmry0s / router_llm_hf/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/ccr-f01c3de9-bmry0s/router_llm_hf |
| 3 | Control HF (Spaces) | ccr-f01c3de9-bmry0s / control huggueface/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/ccr-f01c3de9-bmry0s/control%20huggueface |
| 4 | LLM System HF (modelos) | ccr-f01c3de9-bmry0s / llm system HF/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/ccr-f01c3de9-bmry0s/llm%20system%20HF |
| 5 | Chat backend · Harness DeepSeek | main / chat-router/chat/backend/deepseek_harness/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/chat/backend/deepseek_harness |
| 6 | Chat frontend | main / chat-router/chat/frontend/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/chat/frontend |
| 7 | Satélite Central de Conexión | main / SATÉLITE CENTRAL CONECCION/ | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/SAT%C3%89LITE%20CENTRAL%20CONECCION |
| 8 | Registro maestro de cableado | main / SATÉLITE CENTRAL CONECCION/SATÉLITE CENTRAL CONECCION.yaml | https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/SAT%C3%89LITE%20CENTRAL%20CONECCION/SAT%C3%89LITE%20CENTRAL%20CONECCION.yaml |
| 9 | Inventario de pares (38, pending_audit) | main / connections/registry.yaml | https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/connections/registry.yaml |
| 10 | Handoff central | main / handoff central/README.md | https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/handoff%20central/README.md |
