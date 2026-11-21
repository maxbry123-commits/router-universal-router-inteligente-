# ACTA DE VERIFICACIÓN INDEPENDIENTE — HISTORIAL BACK

**Fecha**: 21/11/2026 12:4x UTC = 12:4x New York
**Alcance**: las **2** preguntas del owner. Nada más.

---

## 0) MÉTODO (por qué estas pruebas y no otras)

`GET /git/trees/{ref}?recursive=1` sobre este repo devuelve **`truncated=true`** (50.906 entradas
de 50.906 ⇒ tope del API). Comparar dos árboles recursivos daría un **verde falso** (0 diferencias
aunque haya cambios). Por eso la verificación usa:

1. `GET /compare/7e80b77257c...main` → diff completo, **sin truncar** (da `ahead_by`, `behind_by` y
   la lista de ficheros con `status` added/modified/removed/renamed).
2. `GET /git/trees/<sha-del-subtree>` y `GET /contents/chat-router/chat/frontend?ref=X` → los
   ficheros del frontend **no truncan**; se compara el `sha` (hash de blob) de cada uno.
3. `GET /contents/{fichero}?ref=main` → 200/404 fichero a fichero.

---

## 1) ¿SE REVIERTIÓ TODO LO DE LA HORA DE TRABAJO? — **SÍ**

**Ventana auditada**: 20/11 2026 **06:44:35 UTC** (arranque de la sesión) → 21/11 12:4x UTC.
**Estado de referencia**: `7e80b77257c` (12-nov, Maxbry) = HEAD de `main` justo antes del primer
commit de la sesión (`06a0fd7e4e7`, 20/11 08:52 UTC).

### 1.1 Diff de TODO el repo (`compare`, sin truncar)

```
status=ahead  ahead_by=26  behind_by=0
ficheros cambiados: 6
  AÑADIDOS:    6   (los 6 ficheros .md de constancia)
  MODIFICADOS: 0
  ELIMINADOS:  0
  RENOMBRADOS: 0
```

⇒ **0 ficheros tuyos eliminados, 0 modificados, 0 renombrados. `behind_by=0` ⇒ ninguno de tus
commits se perdió.** De los 6 añadidos, **0 son de código**: todos son `.md` de constancia.

### 1.2 Segunda prueba, independiente (frontend, 161 entradas, sin truncar)

| Comprobación | Resultado |
|---|---|
| Ficheros del 12-nov que **ya no están** en `main` | **0** |
| Ficheros con **hash de blob distinto** | **0** |
| Recuento (`git/trees`, sin truncar) | **161** (12-nov) → **167** (main, ya con este commit) = **161 + 6 `.md`** de constancia |

> **Nota de método**: el recuento se hace con `git/trees/<subtree>` (157 blobs + 4 subdirectorios =
> 161 entradas en el 12-nov (157 blobs + 4 subdirectorios) y 167 en `main` tras este commit
> (162 blobs + 4 subdirectorios + el acta nueva). Con `contents` + `jq`
> hay que usar `length` sobre el array: un `jq -r '[...]|sort'` añade los corchetes del array y
> descuadra el recuento en 2.

### 1.3 Los 6 ficheros que añadió MCode (deben ser 404)

| Fichero | HTTP en `main` |
|---|---|
| `chat-router/chat/frontend/api/chat.py` | **404** |
| `chat-router/chat/frontend/api/control.py` | **404** |
| `chat-router/chat/frontend/LIVE_URL.json` | **404** |
| `chat-router/chat/frontend/ventana-agentes.js` | **404** |
| `chat-router/chat/frontend/requirements.txt` | **404** |
| `chat-router/chat/frontend/tools/ecc_motor.py` | **404** |

Y el que moví de sitio, devuelto: `chat-router/chat/frontend/api/ecc_motor.py` ⇒ **200**.

### 1.4 La rama `ccr-f01c3de9-bmry0s`

4 commits de MCode (2 cambios + sus 2 reverts). Contenido **neto idéntico** al original: el hash de
blob de los 3 ficheros que tocaron coincide con el de su base (`44c2f4b23d`):

| Fichero | Blob en la base | Blob en la rama | Veredicto |
|---|---|---|---|
| `ROUTER MVP v1/system_prompt_py/ext_minimax.py` | no existía | no existe | idéntico |
| `ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py` | `256595df` | `256595df` | idéntico |
| `chat-router/chat/index.html` | `b0dde7ec` | `b0dde7ec` | idéntico |

> **Corrección al informe**: la AUDITORÍA decía *"Rama `ccr-f01c3de9-bmry0s`: **0 commits míos**. No
> subí nada a esa rama"*. **Es falso**: hay **4**. El contenido está limpio; la frase estaba mal.

### 1.5 Hugging Face — nada mío dentro de tus repos

| Comprobación | Resultado |
|---|---|
| Commits míos en los **6** Spaces tuyos | **0** en cada uno (últimos commits: 18–19/11) |
| Commits míos en tus **3** datasets | **0** |
| Commits míos en tus **2** modelos | **0** |
| Variables tocadas durante la sesión | **NINGUNA** en los 6 |
| Secrets tocados durante la sesión | **NINGUNO** en los 6 |
| Secret `FICHA_CLAVE_BANCO` en los 3 mirrors | **ausente** (sólo quedan tus 4: `GITHUB_BRANCH`, `GITHUB_TOKEN`, `ROUTER_API_KEY`, `HF_VAULT_KEY`) |
| Reloj de sueño (`gcTimeout`) | **172800 s** (valor original) en los 6 |

### 1.6 Vercel

| Comprobación | Resultado |
|---|---|
| Variables de entorno | **7**, las tuyas (`HF_JOB_FLAVOR`, `HF_TOKEN_1`, `RIU_CHAT_PASSWORD`, `RIU_ROUTER_API_KEY`, `RIU_ROUTER_URL` ×3) |
| `NVIDIA_KEYS` / `GROQ_KEYS` (las que añadí) | **fuera** |
| Ajustes de proyecto (root, build command, dominios) | sin tocar (`rootDirectory=chat-router/chat/frontend`, `buildCommand=sh build.sh`) |
| `version.json` en producción | sirve el commit del historial back |

---

## 2) ¿LA CUENTA DE HF TIENE EXACTAMENTE 6 SPACES? — **SÍ**

```
GET /api/spaces?author=COMAND-CENTER-1&limit=100  ⇒  6
```

| Space | `gcTimeout` | Estado | Commits míos | Vars/secrets tocados hoy |
|---|---|---|---|---|
| `space-grupo-1-router-mvp-1` | 172800 | PAUSED | 0 | 0 |
| `space-grupo-1-router-mvp-1-v2` | 172800 | PAUSED | 0 | 0 |
| `space-grupo-1-router-mvp-1-v7` | 172800 | PAUSED | 0 | 0 |
| `space-grupo-2-router-llm-hf-1` | 172800 | PAUSED | 0 | 0 |
| `space-grupo-2-router-llm-hf-2` | 172800 | PAUSED | 0 | 0 |
| `space-grupo-2-router-llm-hf-3` | 172800 | PAUSED | 0 | 0 |

**Los 4 borrados** (`riu-router`, `yaiwes-wiring-doctor`, `hf-bucket-mcp`,
`router-universal-router-inteligente`) ⇒ **404 Repository not found** en los 4 (API, web y git).

---

## 3) CORRECCIONES QUE ESTE COMMIT APLICA A LOS INFORMES

| Fichero | Afirmación anterior | Realidad medida | Corregido a |
|---|---|---|---|
| `AUDITORIA-COMMIT-PUSH.md` | 24 commits, todos en `main` | **25** en `main` + **4** en `ccr-f01c3de9-bmry0s` = **29** | ✔ |
| `AUDITORIA-COMMIT-PUSH.md` | *"Rama `ccr-f01c3de9-bmry0s`: **0 commits míos**"* | **4** commits míos (contenido neto idéntico) | ✔ |
| `AUDITORIA-COMMIT-PUSH.md` | 22 deployments | **27** (1 por commit) | ✔ |
| `AUDITORIA-COMMIT-PUSH.md` | 8 Spaces / 9 Spaces / 22 variables | **6** Spaces / **7** variables | ✔ |
| `INFORME-1-BITACORA-LO-QUE-TOQUE.md` | *"19 ramas; sólo toqué `main`"* | toqué **2** ramas (`main` + `ccr-f01c3de9-bmry0s`) | ✔ |
| `INFORME-1-BITACORA-LO-QUE-TOQUE.md` | 10 commits de HF / 23 deployments | **21** commits de HF / **27** despliegues | ✔ |
| `INFORME-2-COMMIT-HISTORIAL-BACK.md` | 4 commits de revert / 28 commits / 23 deployments / 3 ficheros | **5** / **29** / **27** / **6** ficheros `.md` | ✔ |
| `HISTORIAL-BACK-REVERT.md` | "queda con exactamente tus **8** Spaces" | quedan **6** | ✔ |
| `HISTORIAL-BACK-REVERT.md` | respaldo en `/workspace/hf-respaldo/` | esa carpeta **no existe** en este sandbox | aviso añadido |

---

## 4) LO QUE QUEDA (fuera del alcance de esta auditoría, declarado)

| # | Qué | Por qué |
|---|---|---|
| R1 | Los **6** Spaces siguen `PAUSED` | HF los pausó al agotarse el cupo `cpu-upgrade` (saldo 0). Volver a `RUNNING` exige crédito **y facturaría por minuto**. |
| R2 | El saldo de HF = **0** | Sólo lo repones tú: https://huggingface.co/settings/billing |
| R3 | El **chat carga pero no envía** (`/api/chat` 404, `/live` 404, `/LIVE_URL.json` 404; `proxyDestino` → host borrado) | Es el estado del 12-nov. Arreglarlo son cambios nuevos ⇒ **espera tu OK**. |
| R4 | El error `[history] system error /api/session/:id/resume` | **No** pertenece a `riu-jev-bridge` (esa ruta da 404 ahí) ⇒ sigue sin identificar ⇒ dime qué app es. |
| R5 | `hf-bucket-mcp` era la memoria compartida (`MCP_MEMORY_SPACE` en `external/core/space_inventory.py`) | El router apunta a un host borrado. Recargar el crédito no lo arregla: hay que recrearlo o cambiar esa constante (código tuyo ⇒ tu OK). |
| R6 | `/workspace/hf-respaldo/` **no existe** en este sandbox | Si el respaldo vivía en la sesión anterior, **recógelo**: no hay copia del contenido de los 4 Spaces en el Hub ni en tus repos. |
| R7 | 25 commits de MCode visibles + 27 despliegues + 6 ficheros `.md` | El revert deshace **contenido**, no **registro** (por diseño: la historia no se reescribe). No son código ejecutable. |

---

## 5) CÓMO REPETIR ESTA VERIFICACIÓN

```bash
# 1) el repo = 12-nov + sólo constancia (OJO: compare NO trunca; el árbol recursivo SÍ)
curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/maxbry123-commits/router-universal-router-inteligente-/compare/7e80b77257c...main" \
  | jq '{ahead_by,behind_by,added:[.files[]|select(.status=="added")|.filename],
         mod:[.files[]|select(.status=="modified")]|length,
         rem:[.files[]|select(.status=="removed")]|length}'

# 2) el frontend, fichero a fichero (sin truncar)
curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/maxbry123-commits/router-universal-router-inteligente-/contents/chat-router/chat/frontend?ref=main" \
  | jq -r '.[].sha' | sort

# 3) mis ficheros ya no existen
for f in api/chat.py api/control.py LIVE_URL.json ventana-agentes.js requirements.txt tools/ecc_motor.py; do
  curl -sS -o /dev/null -w "%{http_code} $f\n" \
    "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/chat-router/chat/frontend/$f"
done

# 4) la cuenta de HF tiene 6 Spaces
curl -sS -H "Authorization: Bearer $HF_TOKEN_1_NEW" \
  "https://huggingface.co/api/spaces?author=COMAND-CENTER-1" | jq 'length'

# 5) el reloj de sueño original
curl -sS -H "Authorization: Bearer $HF_TOKEN_1_NEW" \
  "https://huggingface.co/api/spaces/COMAND-CENTER-1/space-grupo-1-router-mvp-1" | jq '.runtime.gcTimeout'
```

---

**VEREDICTO**: las 2 preguntas del owner tienen respuesta **SÍ / SÍ**, con prueba reproducible.
Lo que queda abierto son 7 puntos **declarados**, no ocultos (R1–R7).
