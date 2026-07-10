# Router Universal NCT

Router que conecta **Nodos** (modelos, agentes, satélites) con **Conectores** (HTTP, SSE, WebSocket, archivos) bajo un contrato común validado por `red/enchufe_gate.py`.

## 📦 Contenido

```
router-universal/
├── red/
│   ├── enchufe_gate.py    # validación de contratos
│   ├── router.py           # core routing
│   └── connectors.py       # HTTP/SSE/WS/file transports
├── src/                    # 🌐 Interface web (vanilla HTML+CSS+JS)
│   ├── index.html
│   ├── css/styles.css
│   └── js/{router,inspector,app}.js
├── docs/
│   ├── contratos.md
│   └── ejemplos.md
├── examples/
│   └── ejemplo_basico.py
└── README.md
```

## 🧠 Backend (Python)

```python
from red.router import send, broadcast
r = send("openclaw", {"text": "hola"})
```

**Contrato** de cada artifact:
- `artifact_id` ^art_[a-z0-9]{8,32}$
- `estado` pending|approved|rejected|completed
- `kind` text|code|file|image|consensus|manifest
- `transport` http|sse|ws|file|ipc
- `sandbox` pyodide|wasm|native|none|docker
- `timeout_ms` 100..600000
- `hash` SHA256 del payload
- `signature` HMAC-SHA256 opcional

## 🌐 Interface web

`src/index.html` — vanilla HTML, sin build step, deployable directo a Cloudflare Pages.

**Features**:
- Sidebar con 7 satélites preconfigurados (openclaw, claude-code, mimo-code, nct, ocr, obsidian, graphiti)
- Health check auto cada 30s
- Composer con kind/transport/sandbox/timeout selector
- Modo broadcast (envía a todos en paralelo)
- Inspector con tabs (Inspector / Topología / Contrato)
- Visualización de topología en SVG (router central + satélites)
- Settings: URL base, HMAC secret, colores personalizables
- Log de respuestas con payload completo
- Tema dark/light
- Mobile responsive
- LocalStorage para satélites + log + config

**Uso**:
```bash
cd src && python3 -m http.server 8080
# abrir http://localhost:8080/
```

**Deploy a Cloudflare Pages**:
```bash
npx wrangler pages deploy src --project-name=router-ui
```

## 🚀 Despliegue completo

1. Backend Python: `pip install requests pyyaml && python3 red/router.py`
2. Frontend: `python3 -m http.server 8080` en `src/`
3. Conectar via URL en Settings de la UI

## 🧪 Tests

Abrir la consola del navegador en `src/index.html` y verificar:
- 7 satélites en sidebar
- Health check ejecuta `fetch(/health)` cada 30s
- Click en satélite → muestra inspector
- Envío crea artifact con UUID + hash SHA256 + validado por regex
