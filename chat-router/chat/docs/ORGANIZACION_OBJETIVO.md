# Raíz de organización — cómo debería quedar

Leyenda: ✅ ya está así hoy · ➜ propuesta (hoy está en la ruta de la derecha; no se movió nada de esta parte).

```
/ (raíz del repositorio)
│
├── RAÍZ ROUTER MVP
│   └── mvp/  ✅  (enlace a chat/backend/mvp; el Space arranca `python -m mvp.run`)
│
└── RAÍZ CHAT ROUTER (main)
    │
    ├── Chat router / Deepseek harness
    │   └── chat/backend/deepseek_harness/  ✅   (enlace: plugins/deepseek_harness)
    │
    ├── Chat router / Agentes
    │   └── plugins/agentes/  ✅   05-AGENTES · 07-SENTINELAS · agent-microkernel · agents · agents-yaiwes · workflow-agentes
    │
    ├── Chat / RAÍZ DEL CHAT  ✅  (chat/)
    │   ├── frontend/   ✅  chat/frontend/   → lo que sirve Vercel (70 módulos .js, Root Directory = chat/frontend)
    │   ├── backend/    ✅  chat/backend/    → mvp/ · deepseek_harness/ · router_api_cliente.py
    │   ├── e2e/        ✅  pruebas en navegador
    │   ├── auditoria/  ✅  cableado.py · indice.py · cambios.py
    │   └── docs/       ✅  frontend/ · backend/ · HANDOFF · INDICE · CAMBIOS · GROK_PRUEBA_TOTAL
    │
    ├── Chat router / Chatbot
    │   └── ➜ chat-router/chatbot/   ← hoy: plugins/chat-router/10-CHAT-FUNCIONES · 13-CHAT-UI-SUITE · chat_space · space · plugins/puente_chat
    │
    ├── Chat router / Workflow Loop code Yaiwes
    │   └── plugins/workflow-loop-yaiwes/  ✅   code/ · contratos/  (+ plugins/chat-router/frontend-yaiwes ➜ aquí)
    │
    └── Chat router / Otros
        └── ➜ chat-router/otros/   ← hoy: plugins/chat-router/09-CLAUDE-CODE · 11-EVIDENCIA · 12-FABRICA-MOTORES · espejos
            y plugins/{connectivity, hf_compute, hf_datasets, hf_skills, hf_storage, lifeguard, memoria, motores,
                      motores-descarga, orquestador, parallel, ssh_bridge}
```

## Fuera de estas raíces (no se tocan)
`router/` (Router universal original) · `raiz_router/` y `raiz_fichas_prompt/` (arquitectura y handoff) · `fichas/` · `componentes/` (336 mil archivos) · `docs/` · `Prueba/`.

## Qué falta para completar la propuesta (➜)
1. **Chatbot** y **Otros**: mover las carpetas de `plugins/chat-router/` y los plugins sueltos a `chat-router/chatbot/` y `chat-router/otros/`. Cada plugin se carga por `plugins.<nombre>` y por `ficha.json`, así que cada movimiento necesita su enlace de compatibilidad o actualizar los imports (se verifica con `chat/auditoria/cableado.py`, `pytest` y la batería e2e).
2. **Workflow Loop code Yaiwes**: ya está en su carpeta; solo falta traer `frontend-yaiwes`.
3. **Agentes**: ya está agrupado en `plugins/agentes/`.
4. Decisión tuya: qué carpetas exactas van en **Chatbot** y en **Otros** (arriba pongo mi mejor lectura).
