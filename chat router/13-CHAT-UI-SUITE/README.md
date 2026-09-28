# T09 — Suite multi-chat YAIWES

Objetivo: mantener **Open WebUI** como chat base y colocar debajo las otras tres UIs ya descargadas: **LibreChat, big-AGI y Jan**, sin reescribir su código. Hermes y OpenClaw se consumen como backends/agentes mediante un gateway OpenAI-compatible común.

## Disposición

- Open WebUI existente: `router inteligente universal/Componente open soure router inteligente universal/open-webui/code`
- LibreChat: `router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/LibreChat`
- big-AGI: `router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/big-AGI`
- Jan: `router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/Jan`

Las tres alternativas están fijadas a los mismos commits que las copias verificadas de `frontend/main/UI YAIWES/componentes open soure UI YAIWES/`. Se usan gitlinks/submódulos para conservar el árbol completo, incluidos blobs binarios, sin recortar ni regenerar código.

## Cableado Hermes/OpenClaw

`gateway.py` expone:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `GET /health`

Modelos lógicos:

- `yaiwes/hermes` → `planner_supervisor`
- `yaiwes/openclaw` → `guardian_supervisor`

El gateway reutiliza **exactamente** `chat router/05-AGENTES/asistentes/puente_asistentes.py`. No usa ni copia las UIs propias de Hermes/OpenClaw y no modifica el código de Open WebUI, LibreChat, big-AGI o Jan.

Cada UI debe apuntar su proveedor OpenAI-compatible a `http://127.0.0.1:8099/v1` y elegir uno de los dos modelos anteriores.

## Arranque

```bash
bash "chat router/13-CHAT-UI-SUITE/start_gateway.sh"
```

Para materializar las tres UIs tras clonar el repo:

```bash
git submodule update --init --recursive -- "router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/LibreChat" "router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/big-AGI" "router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/Jan"
```

## Aceptación

```bash
SIMULADO=1 python -m pytest "chat router/13-CHAT-UI-SUITE/tests" -q
bash -n "chat router/13-CHAT-UI-SUITE/start_gateway.sh"
python -m py_compile "chat router/13-CHAT-UI-SUITE/gateway.py"
git ls-tree HEAD "router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/LibreChat" | grep -q 968950a4bdb3929c9381b80290720972cb936134
git ls-tree HEAD "router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/big-AGI" | grep -q 7413983159ddb7056bde035d98446d33573bfa0a
git ls-tree HEAD "router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat/Jan" | grep -q e2185dbc7db3a002da35b3688b57910ec6fd87b2
```

PASS exige todas las comprobaciones anteriores con exit 0.
