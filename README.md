# Router Universal · NCT

Router que conecta **Nodos** (modelos, agentes, satélites) con **Conectores** (HTTP, SSE, WebSocket, archivos) bajo un contrato común validado por `enchufe_gate.py`.

## Arquitectura

```
Nodos (origen) ──► Router ──► Conectores (transporte) ──► Sandbox ──► Salida
                       │
                       ├── Manifests (declaración)
                       ├── Policy (enforcement)
                       ├── Cost (tracking)
                       └── Consensus (multi-agente)
```

## Estructura

```
router-universal/
├── red/
│   ├── enchufe_gate.py   # validación de contratos
│   ├── router.py          # core routing logic
│   └── connectors.py      # HTTP/SSE/WS/file transports
├── docs/
│   ├── contratos.md       # schema artifact, hash, kinds, transports
│   └── ejemplos.md        # 3 ejemplos de uso
├── examples/
│   └── ejemplo_basico.py
└── README.md
```

## Contrato

Cada artifact tiene:
- `artifact_id` (UUID)
- `estado` (pending|approved|rejected|completed)
- `kind` (text|code|file|image|consensus)
- `transport` (http|sse|ws|file)
- `sandbox` (pyodide|wasm|native|none)
- `timeout_ms` (default 30000)
- `payload` (contenido)
- `hash` (SHA256 del payload)
- `signature` (HMAC opcional)

## Uso desde el chat frontend

```js
import { Router } from 'https://cdn.example.com/router.js';
const r = new Router({ base: 'http://95.111.232.89:7000' });
await r.send({ kind: 'text', to: 'openclaw', payload: { text: 'hola' } });
```
