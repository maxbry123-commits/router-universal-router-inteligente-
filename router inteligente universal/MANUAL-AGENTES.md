# MANUAL PARA AGENTES — Router Inteligente Universal (fuente de la verdad)

Actualizado: 2026-10-03 noche (Opus, por orden del Director Hy). Este manual reemplaza a todas las guías anteriores del Router.
Si algo de cualquier otro archivo contradice este manual, **vale este manual**. Guías viejas que NO debes seguir: `CONECTAR-ROUTER.md`, `CONECTAR-SDK-NUEVO.md`, `HANDOFF-CABLEADO.md`, `HANDOFF-PROVISIONAL-ROUTER.md` y las `ADENDA-*` / `ARQUITECTURA-*` / `GUIA-MAESTRA-*` de `Readme arquitectura router inteligente universal/`.

**Inicio rápido (5 líneas):** 1) pide tu token al Director y ponlo en `RIU_TOKEN`; 2) `GET <puerta>/tokens/yo` para ver tus permisos; 3) chat: cliente OpenAI con `base_url=<puerta>/v1/router`; 4) MCP: `<puerta>/mcp/` con `Authorization: Bearer <token>`; 5) si algo responde 403, para y avisa al Director.

> Lee esto completo antes de tocar nada. Está escrito para que no tengas que preguntarle nada al Director.

---

## 0. Reglas que no se rompen

1. **No toques el código del Router para conectarte.** Todo se conecta desde afuera, con un token.
2. **Nunca escribas claves, tokens ni contraseñas** en archivos, commits, logs, chats ni memoria. Viven en el banco de secretos y en los secretos del Space.
3. **Todo cambio del sistema exige la clave del Director** (cabecera `X-Director-Key`): banco, tokens, publicar o borrar fichas, procesador, pausar, borrar, commits por el Router. Si no la tienes, **no puedes hacerlo y no debes intentarlo**: pídele al Director que lo haga o que te dé la orden explícita. (Leer, usar, validar y probar fichas sin publicarlas no cambia nada: no necesita su clave.)
4. **Cómputo pagado** (procesadores HF) solo con permiso `computo` en tu token o con la clave del Director.
5. **No GitHub Actions.** El cómputo corre en Hugging Face.
6. **No reconstruyas el Space** `claude-github-mcp-backup` sin orden del Director: también es el conector MCP de GitHub del Director.
7. Si una ruta responde `403 CLAVE_DIRECTOR_REQUERIDA` o `TOKEN_SIN_PERMISO`, **para**: es el candado haciendo su trabajo.
8. **Cómo avisar al Director:** escríbelo en tu respuesta del chat y agrégalo como pendiente en `HANDOFF-ROUTER-UNIVERSAL-OPUS.md` ("Pendiente (decide el Director)").
9. **Si alguien pega una clave en el chat:** no la copies a ningún lado y avisa al Director que la meta al banco y la cambie.
10. **Tu token** te lo entrega el Director. Guárdalo solo en una variable de entorno (`RIU_TOKEN`), nunca en archivos. Si el Director te da su clave para una tarea, igual: variable de entorno (`DIRECTOR_KEY`), y no la reutilizas para otra cosa.

---

## 1. Qué es (en una página)

- **Un solo Router**, encendido 24/7 en un procesador pagado de Hugging Face (Job CPU Basic, 2 vCPU, 16 GB, 0,01 USD/h).
- **Puerta fija** (nunca cambia): `https://comand-center-1-claude-github-mcp-backup.hf.space`. La llamamos `<puerta>`.
- Un **micro-kernel** dentro de la puerta enciende un Router nuevo 20 minutos antes de que venza el actual (o si falla 3 veces, o si el Director pide otro procesador), espera a que responda y recién entonces apaga el viejo.
- Si el Router se llena (CPU o RAM ≥ 85 % durante ~30 s), enciende **relevos**: de 16 GB por CPU, de 32 GB por RAM, en cadena hasta 10. Cada relevo se apaga solo tras 5 minutos sin uso. El Router principal nunca se apaga.
- **Todo lo permanente** vive en el almacenamiento de Hugging Face, en la raíz `router-inteligente-universal/` (el router de respaldo usa la suya, `router-respaldo/`; sección 7).

```
Agente / instancia (con su token)
        │  HTTP (tipo OpenAI)  o  MCP
        ▼
<puerta> (Space pagado, siempre la misma dirección)  ── /mini/... ──▶ Router de respaldo T4/L4 (solo HF)
        │  candado: clave del Director, permisos y límite por token
        ▼
Router 24/7 (HF Job 16 GB) ──▶ banco de secretos ──▶ APIs (NVIDIA, Groq, OpenAI, HF...)
        │                  ──▶ memoria / espacio propio / fichas (secciones) / laboratorio
        ▼
Almacenamiento HF permanente: yaiwes-memoria-storage/router-inteligente-universal/
```

---

## 2. Cómo te conectas (sin cablear nada)

Necesitas **un token** `riu_...`. Lo crea el Director (sección 5). Con ese mismo token tienes todo:

| Quieres | Cómo |
|---|---|
| Chat con cualquier modelo | Cliente OpenAI con `base_url = <puerta>/v1/router`, `api_key = <tu token>`, `model = "auto"` (o un grupo, o `proveedor:modelo`) |
| MCP (Claude, harness, agentes MCP) | URL `<puerta>/mcp/`, cabecera `Authorization: Bearer <tu token>`, transporte streamable HTTP |
| Python sin dependencias | `router inteligente universal/sdk/riu_conectar.py` → `Router("riu_...")` |
| Node 18+ | `router inteligente universal/sdk/riu-conectar.mjs` → `new Router("riu_...")` |
| Saber quién soy y qué permisos tengo | `GET <puerta>/tokens/yo` |

**Ejemplo Python (copiar y pegar):**
```python
from riu_conectar import Router
r = Router("riu_TU_TOKEN")            # o variable de entorno RIU_TOKEN
print(r.yo())                         # quién soy
print(r.chat("Hola, resume esto: ..."))
r.memoria_guardar("proyecto-x", "decision-1", {"texto": "usar Postgres"})
r.espacio_guardar("informes/hoy.md", "# Informe\n...")
print(r.seccion("mi-ficha", "entrada para la ficha"))
```

**Ejemplo cliente OpenAI:**
```python
from openai import OpenAI
c = OpenAI(base_url="https://comand-center-1-claude-github-mcp-backup.hf.space/v1/router", api_key="riu_TU_TOKEN")
c.chat.completions.create(model="auto", messages=[{"role": "user", "content": "hola"}])
```

**Ejemplo MCP (config de cliente):**
```json
{"mcpServers": {"router": {"type": "http", "url": "https://comand-center-1-claude-github-mcp-backup.hf.space/mcp/",
  "headers": {"Authorization": "Bearer riu_TU_TOKEN"}}}}
```

**Harness DeepSeek** (usa el Router como proveedor, sin DeepSeek API):
```bash
MAXBRY_ROUTER_URL=<puerta>/v1/router MAXBRY_ROUTER_API_KEY=<token> RIU_ROUTER_URL=<puerta> RIU_API_KEY=<token> DSH_TELEMETRY_MODE=DISABLED \
dsh headless --patch 'chat router/harness plugins/deepseek-harness-chat/plugins/router-provider.cordis.yml' \
             --patch 'chat router/harness plugins/memoria/harness-memoria.cordis.yml' "tarea"
```

**SSH:** no existe en HF Jobs. Usa la **terminal remota** (`/terminal/run`, permiso `terminal`): ejecuta comandos en un procesador HF y devuelve los registros.

---

## 3. Lo que te da tu token (las 3 cosas)

### 3.1 APIs y SDK (sin ver nunca una clave)
- El Router usa las claves del banco **por ti**. Tú solo pides `model`.
- `model = "auto"` usa la cadena por defecto (NVIDIA primero; si falla, Groq...). Grupos: `assistants`, `code`, `minor`, `g2`, etc. (lista: `GET /v1/router/models`).
- Directo a un proveedor: `proveedor:modelo`, p. ej. `nvidia:moonshotai/kimi-k3`, `groq:qwen/qwen3.8-27b`.
- Catálogo vivo de lo que hay ahora: `GET /fichas/catalog` (o herramienta MCP `router_catalog`).

### 3.2 Almacenamiento propio (nadie más lo ve)
- **Memoria** (cada token tiene la suya; nadie más la ve):
  - Guardar: `POST /memoria/save` con cuerpo JSON `{"scope": "proyecto-x", "key": "decision-1", "data": {...cualquier JSON...}}`.
  - Leer: `GET /memoria/load?scope=proyecto-x&key=decision-1` → `{"records": [{"id", "scope", "key", "data"}]}`.
  - Buscar: `GET /memoria/search?scope=proyecto-x&query=texto&k=10`.
  - SDK Python: `memoria_guardar(scope, key, data)`, `memoria_leer(scope, key)`, `memoria_buscar(scope, query)`. MCP: `memoria_save`, `memoria_load`, `memoria_search`.
- **Archivos**: `PUT /espacio/<ruta>` (cuerpo = el archivo tal cual, hasta 20 MB; la ruta la eliges tú, p. ej. `informes/hoy.md`), `GET /espacio/<ruta>`, `GET /espacio` (lista), `DELETE /espacio/<ruta>`. Vive en `router-inteligente-universal/espacios/<tu-token>/` en HF. SDK: `espacio_guardar`, `espacio_leer`, `espacio_lista`. MCP: `espacio_guardar`, `espacio_leer`.
- El SDK no se instala: copia el archivo `sdk/riu_conectar.py` (o `sdk/riu-conectar.mjs`) junto a tu código.
- Todo se copia solo al almacenamiento permanente de HF (memoria cada 60 s; archivos al instante).

### 3.3 Cómputo
- Permiso `computo`: `POST /hf/compute/run` (`{"command": [...], "flavor": "cpu-basic", "image": "python:3.12", "timeout": "30m"}`).
- Permiso `terminal`: `POST /terminal/run` (`{"comando": "ls -la", "flavor": "cpu-basic"}`, el comando es un texto) → responde `{"job_id": "...", "ver": "/terminal/<job_id>?logs=60"}`; luego `GET /terminal/<job_id>?logs=60`. El procesador tarda 1–3 min en encender y se cobra a la cuenta HF del Director.
- GPU (`t4-small`, `l4x1`) también por esas rutas, si el Director dio el permiso. Para modelos rápidos por llamada usa el **router de respaldo** (sección 9).
- Además el Router enciende relevos solo si se llena (no tienes que hacer nada).

---

## 4. Permisos y límites

| Permiso | Qué abre | Por defecto |
|---|---|---|
| `chat` | `/v1/router/chat/completions`, `/chat/send`, `/chat/route` | sí |
| `memoria` | `/memoria/*` | sí |
| `almacenamiento` | `/espacio*` | sí |
| `fichas` | `/secciones/<nombre>/run`, `/secciones/probar`, `/fichas/<id>/run` | sí |
| `computo` | `/hf/compute/run` (CPU y GPU), router de respaldo `/mini/*` (GPU de pago) | **no** (lo da el Director) |
| `terminal` | `/terminal/*` | **no** (lo da el Director) |

- Rutas abiertas a cualquier token válido (no cambian el sistema): `/tokens/yo`, `/secciones`, `/secciones/<n>`, `/secciones/_plantilla`, `/secciones/validar`, `/secciones/recargar`, `/fichas/catalog`, `/v1/router/models`, `/ventana`, `/control/hf/status`, `/vault/status`, `/lab/run`, `/lab/last`.
- Si al crear un token no se dan `permisos`, recibe los 4 de por defecto (`chat`, `memoria`, `almacenamiento`, `fichas`).
- Cada token tiene **límite por minuto** propio (por defecto 600). Si te pasas: `429 LIMITE_POR_MINUTO_DEL_TOKEN`. Los demás agentes no se ven afectados.
- Un token **apagado** deja de entrar al instante (≤ 60 s en todas las copias).

---

## 5. Tokens (solo el Director los crea)

Todas estas rutas exigen tu token **y** `X-Director-Key`.

| Acción | Llamada |
|---|---|
| Crear 1 | `POST /tokens` `{"instancia": "equipo-a", "nombre": "agente-1", "permisos": ["chat","memoria","almacenamiento","fichas"]}` |
| Crear 10.000 | `POST /tokens` `{"instancia": "equipo-a", "prefijo": "agente", "cantidad": 10000}` → `equipo-a/agente-00001` … |
| Con cómputo | agrega `"computo"` y/o `"terminal"` a `permisos` (ojo: `computo` también abre GPU de pago) |
| Límite propio | `"limite_rpm": 600` (llamadas por minuto de ese token) |
| Amarrar a una ficha | `"ficha": "mi-ficha"` al crear, o `POST /tokens/ficha/<nombre>` `{"ficha": "mi-ficha"}` |
| Apagar / encender | `POST /tokens/apagar/<nombre>` · `POST /tokens/encender/<nombre>` |
| Listar | `GET /tokens` (`?instancia=equipo-a`) |

- El token se muestra **una sola vez** al crearlo. El banco guarda solo su huella (`banco/tokens.json`), nunca el token.
- Los tokens nuevos funcionan en ≤ 60 s en todas las copias del Router, sin reiniciar.

---

## 6. Fichas = secciones vivas (plantilla, no composición)

- Una ficha es **un archivo JSON** en `router-inteligente-universal/fichas/<nombre>.json`.
- El Router revisa esa carpeta cada 60 s: **cada ficha nueva aparece sola como sección nueva** con su ruta `POST /secciones/<nombre>/run`. Sin reiniciar y sin tocar el Router.
- `_plantilla.json` (en la misma carpeta y en `GET /secciones/_plantilla`) es la plantilla vacía. Los archivos que empiezan con `_` no se montan.
- **Paso a paso detallado para crear y operar fichas: `router inteligente universal/HANDOFF-FICHA.md`.**

Resumen de la plantilla:
```json
{
  "nombre": "mi-ficha",
  "descripcion": "Que hace",
  "modo": "cadena",
  "anclaje_system_prompt": "Reglas para todos los pasos",
  "pasos": [{"nombre": "paso-1", "modelo": "auto", "system_prompt": "", "instruccion": "{input}", "max_tokens": 1024}],
  "juez": null,
  "conectividad": {"tokens_permitidos": ["*"], "vias": ["http", "mcp"]}
}
```
- `modo`: `cadena` (cada paso recibe la salida del anterior), `paralelo`, `consejo` (todos + `juez`), `unico`.
- `conectividad.tokens_permitidos`: qué tokens pueden usar la sección (patrones como `equipo-a/*`).
- **Token amarrado a ficha:** todo lo que ese token mande a `/v1/router/chat/completions` pasa por la ficha automáticamente.
- **Sin clave del Director** puedes: revisar una ficha (`POST /secciones/validar`) y correrla de prueba sin publicarla (`POST /secciones/probar`, permiso `fichas`).
- Publicar/cambiar/quitar fichas exige la clave del Director (`POST /secciones`, `DELETE /secciones/<nombre>`).

---

## 7. Almacenamiento permanente (HF) — dos raíces

Bucket privado `COMAND-CENTER-1/yaiwes-memoria-storage`:

```
router-inteligente-universal/
  memoria/        base del Router (riu_chat.sqlite3) + documentos; copia cada 60 s, se recupera al arrancar
  banco/          vault.db.gz.b64 (cifrado) + providers.json + tokens.json (huellas) + copias .bak + archivo-bancos-viejos/
  laboratorio/    latest.json + reports/<run_id>.json
  control/        router-current.json (Router vigente), router-desired.json (procesador pedido), kernel-log.jsonl
  codigo/         router-bundle.tar.gz + router-bundle.json (código que arrancan los Jobs)
  fichas/         <nombre>.json (secciones) + _plantilla.json
  espacios/       <token>/... (archivos propios de cada token)
  Ventana status router inteligente universal/   estado vivo (se escribe solo, ver sección 8)
router-respaldo/  state.json + LEEME-HANDOFF.md (mini router T4/L4)
```
No hay nada fuera de esas dos raíces. No crees carpetas nuevas en la raíz del bucket.

---

## 8. Ventana status (handoff JSON vivo)

- Carpeta `router-inteligente-universal/Ventana status router inteligente universal/`, se actualiza sola cada 30 s (solo si algo cambió):
  - `conectados.json`: quién está conectado, por HTTP o MCP, cuántas llamadas, última ruta.
  - `banco.json`: qué hay en el banco (número N01…, proveedor, cuenta, huella; **nunca** la clave).
  - `laboratorio.json`: último estado de cada API.
  - `secciones.json`: fichas montadas y las que tienen error.
  - `tokens.json`: cuántos tokens por instancia, activos y apagados.
  - `handoff-vivo.json`: Router vigente, puerta, rutas, conteos y guías.
- En vivo: `GET /ventana` o herramienta MCP `ventana_estado`.

---

## 9. Router de respaldo (solo HF)

- `<puerta>/mini/...`, independiente de GitHub. GPU **T4** (0,40 USD/h, Qwen2.5-3B) y **L4** (0,80 USD/h, Qwen2.5-7B) con vLLM.
- Se enciende con la primera llamada (tarda ~7 min la primera vez) y se apaga solo a los 5 min sin uso.
- Tope 5 USD por GPU; al llegar se bloquea hasta que el Director apruebe.
- Chat: `POST /mini/v1/chat/completions` con `model: "t4"` o `"l4"` (503 STARTING/LOADING mientras enciende: reintenta cada 30–60 s).
- Usar: clave maestra o token con permiso `computo`. Cambiar costo/tiempo (`/mini/config`) y aprobar gasto (`/mini/approve`): solo con la clave del Director.
- Handoff propio: `router-respaldo/LEEME-HANDOFF.md` en el almacenamiento HF.

---

## 10. Banco de secretos

- Banco único: `router-inteligente-universal/banco/vault.db.gz.b64` (cifrado con la clave maestra del Director).
- El Router lo abre solo al arrancar y lo **relee cada 5 minutos**: claves nuevas entran sin reiniciar.
- Agregar o rotar claves: `POST /vault/credentials` o `/vault/rotate` con `X-Director-Key` (se guarda en HF con copia de respaldo).
- API nueva (otro proveedor tipo OpenAI): su `base_url` va en `banco/providers.json`; el Router la reconoce sola.
- Detalle completo: `router inteligente universal/Banco de claves/HANDOFF-BANCO.md`.

---

## 11. Laboratorio

- `POST /lab/run` (o MCP `lab_run`): prueba **todas** las claves del banco con 3 pruebas (modelos, respuesta, herramientas), numeradas N01…, sin mostrar claves. Guarda informe en `laboratorio/` y en la base.
- `GET /lab/last`: último informe. Resumen también en la Ventana status (`laboratorio.json`).

---

## 12. Mapa de rutas (todas por `<puerta>`)

| Grupo | Rutas |
|---|---|
| Chat | `POST /v1/router/chat/completions`, `GET /v1/router/models` |
| MCP | `<puerta>/mcp/` (con la barra final; transporte "streamable HTTP", en la config `"type": "http"`). 19 herramientas: `router_chat`, `router_catalog`, `fichas_list`, `ficha_create` (Director), `ficha_run`, `lab_run`, `lab_last`, `memoria_save`, `memoria_load`, `memoria_search`, `almacenamiento_sync`, `hf_compute_run` (computo), `hf_job_status`, `quien_soy`, `secciones_listar`, `seccion_run`, `espacio_guardar`, `espacio_leer`, `ventana_estado` |
| Tokens | `GET /tokens/yo` · Director: `POST /tokens`, `GET /tokens`, `POST /tokens/apagar|encender|ficha/<nombre>` |
| Memoria | `POST /memoria/save`, `GET /memoria/load`, `GET /memoria/search`, `GET /memoria/health` |
| Espacio | `PUT|GET|DELETE /espacio/<ruta>`, `GET /espacio` |
| Secciones | `GET /secciones`, `GET /secciones/_plantilla`, `GET /secciones/<n>`, `POST /secciones/<n>/run`, `POST /secciones/recargar`, `POST /secciones/validar`, `POST /secciones/probar` · Director: `POST /secciones`, `DELETE /secciones/<n>` |
| Cómputo | `POST /hf/compute/run`, `GET /hf/compute/<id>?logs=40` · `POST /terminal/run`, `GET /terminal/<id>` |
| Puente HF | `GET /hf/status`, `GET /hf/models`, `GET /hf/datasets`, `GET /hf/datasets/file`, `GET /hf/skills` · Director: `POST /hf/hardware`, `POST /hf/local/serve` |
| Banco | `GET /vault/status` · Director: `POST /vault/credentials|rotate|import|lock` |
| Laboratorio | `POST /lab/run`, `GET /lab/last` |
| Estado | `GET /ventana`, `GET /control/hf/status` (autoscale), `GET /door/status` (kernel), `GET /health` |
| Enchufe Fables | `GET /chat/fichas` (módulos `yaiwes.router.*` y `yaiwes.seccion.*`) |
| Respaldo | `/mini/status`, `/mini/v1/chat/completions`, `/mini/v1/models`, `/mini/stop` · Director: `/mini/config`, `/mini/approve` |

---

## 13. Errores comunes

| Respuesta | Qué significa | Qué haces |
|---|---|---|
| `401 RIU_API_KEY_REQUIRED/INVALID` | falta el token o es malo | revisa `Authorization: Bearer riu_...` |
| `403 CLAVE_DIRECTOR_REQUERIDA` | la acción cambia el sistema | no la hagas; pide al Director |
| `403 TOKEN_SIN_PERMISO:<x>` | tu token no tiene ese permiso | pide al Director que lo agregue |
| `403 TOKEN_NO_PERMITIDO_EN_ESTA_SECCION` | la ficha no acepta tu token | revisa `conectividad.tokens_permitidos` |
| `429 LIMITE_POR_MINUTO_DEL_TOKEN` | te pasaste de tu límite | espera 1 minuto |
| `409 SECCION_CON_ERROR:<motivo>` | la ficha está mal escrita | corrige el JSON (ver `GET /secciones`) |
| `503` en `/mini/...` | la GPU está encendiendo | reintenta cada 30–60 s |
| `finish_reason: "length"` con poco texto | `max_tokens` muy bajo para un modelo que razona | sube `max_tokens` (≥ 400) |

---

## 14. Dónde está cada cosa (índice)

| Qué | Dónde |
|---|---|
| README y arquitectura | `router inteligente universal/README.md` |
| Este manual | `router inteligente universal/MANUAL-AGENTES.md` |
| Handoff corto (estado + pendientes) | `router inteligente universal/HANDOFF-ROUTER-UNIVERSAL-OPUS.md` |
| Fichas paso a paso | `router inteligente universal/HANDOFF-FICHA.md` |
| Banco paso a paso | `router inteligente universal/Banco de claves/HANDOFF-BANCO.md` |
| Plantilla de ficha | `router inteligente universal/fichas/_plantilla.json` |
| Laboratorio | rutas `POST /lab/run`, `GET /lab/last` (sección 11) |
| SDK | `router inteligente universal/sdk/` |
| Código del Router | `router inteligente universal/integration/chat_mvp/` (candado.py, tokens.py, secciones.py, ventana.py, rutas.py, control_plane.py, mcp_api.py, openai_route.py) |
| Pruebas | `router inteligente universal/tests/` (`test_conexion_universal.py` = candado, tokens, fichas) |
| Puerta, kernel y respaldo | HF Space `COMAND-CENTER-1/claude-github-mcp-backup`: `door.py`, `mini.py`, `README.md` |
| Estado vivo | HF `router-inteligente-universal/Ventana status router inteligente universal/` |
