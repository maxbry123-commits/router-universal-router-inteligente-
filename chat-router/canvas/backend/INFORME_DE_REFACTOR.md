# INFORME DE REFACTOR · Backend del Canvas (cierre de fase)

Documento de la **Salida 1 + 2 + 3** de la auditoría forense del backend.
Cada refutación se contrasta con el código real antes de aplicar nada.

## 0 · Veredicto de la auditoría (qué se confirma y qué se corrige)

| # | Refutación propuesta | Veredicto | Qué se hizo |
|---|---|---|---|
| 1 | `mcp_server.py` no puede usar `http.server` en producción | **CONFIRMADA** | El MCP pasa a ser `backend/mcp_router.py` (APIRouter de FastAPI) montado en `backend/api.py`: un solo proceso, un CORS, un ciclo de vida. El `http.server` (puerto 8078) queda retirado. |
| 2 | `deploy_engine.py` hace un commit por fichero (`/contents/`) | **CONFIRMADA** | `push_fast_forward()` pasa a la **Git Data API**: blobs → tree → commit → ref, **un solo commit**, `force=false`, con read‑back de la ref y del árbol. |
| 3 | 19 ficheros HUÉRFANOS por falta de README | **PARCIAL** | Eran **18** (no 19) y el mecanismo es real (código sin claim documentado → `NEW` → `HUÉRFANO` P2). Se cierra con `backend/README.md` **y** con 5 correcciones al propio auditor. |
| 4 | El frontend no lo sirve `api.py` | **CONFIRMADA** | `StaticFiles` monta `frontend/` en `/ui` desde la misma app (antes: `http.server` aparte). |

## 1 · Por qué el código propuesto no se aplicó tal cual

La propuesta traía 4 defectos que habrían **empeorado** el backend:

| Defecto del código propuesto | Consecuencia | Corrección aplicada |
|---|---|---|
| `app.include_router(mcp_router, prefix="/mcp")` + ruta `@router.post("/mcp")` | La URL real sería **`/mcp/mcp`** (404 en todo) | El router se monta **sin prefijo**; sus rutas ya son `/mcp`, `/mcp/health`, `/guide/match`. |
| `tools/list` con `pass` | `tools/list` caía en “Method not found”: el cliente MCP no recibía catálogo | `tools/list` devuelve el catálogo real de la ventana. |
| `tools/call` devolvía `{"status": "OK", "message": "Tool ejecutada"}` | **MOCK**: habría mintido sobre el resultado real de cada herramienta | Las 7 tools ejecutan la lógica real (mismo motor, in‑process). |
| `MAX_FILE_BYTES` / `MAX_TOTAL_BYTES` declarados y **nunca aplicados** | Sin límite efectivo de tamaño | El motor ya lo aplicaba (check `TAMANO_MAXIMO`); la reescritura lo habría perdido. Conservado y verificado. |
| `raise Exception("Audio not found")` | 500 en vez de 404 | Se conserva el 404 real de la API. |
| `_check_credentials` comparaba el payload **en minúsculas** contra el token | **No detectaba** el token real (si tiene mayúsculas) | La detección real vive en `deploy_engine._scan_payload_keys` + comparación del valor literal. Verificada: `-32002`. |

## 2 · Qué se conservó del motor de deploy (no se tocó lo que funcionaba)

El motor **ya era** fail‑closed y probado. Se conservó **todo** y solo se cambió el
transporte del push:

- 10 checks: `ENTRADA_VALIDA` · `NO_LFS` · `NO_GITHUB_ACTIONS` · `RUTAS_DENTRO_DE_RAIZ` ·
  `SIN_SYMLINKS` · `TAMANO_MAXIMO` · `SIN_CREDENCIALES_EN_FICHEROS` · `HEAD_ESPERADO` ·
  `AUTORIZACION_DESPLIEGUE` · `TOKEN_POR_ENTORNO`
- `plan()` sin escritura · `execute()` con doble autorización · read‑back sha256 ·
  manifiesto con `tree_sha256` · ledger `ledger.jsonl` · `DEPLOY_AUTHORIZED=1` +
  `allow_push` explícito · **nunca** force.

## 3 · Los 5 fixes del auditor X‑Ray (la parte que la auditoría no vio)

El X‑Ray marcaba 18 HUÉRFANOS, pero el ruido venía del **propio auditor**:

| # | Fix | Por qué |
|---|---|---|
| 1 | Una línea de docs sin ruta **ni símbolo** no es una claim | Toda frase con la palabra “módulo” generaba un gap P3 sin evidencia (27 falsos). |
| 2 | Los ficheros que no son código (`.md`, `.json`, `.txt`) se verifican por su existencia | Una tabla de dependencias no declara funciones: darlas por “MODIFIED” era un falso positivo. |
| 3 | Si el símbolo declarado **es el propio fichero** (`api.py` → `backend/api.py`), la claim está verificada | Los docs citaban el nombre corto del fichero. |
| 4 | El extractor distingue **símbolo de código** de **palabra en prosa** | `funcionando (`, `auto (`, `OMITIDO` se tomaban como símbolos: gaps que nadie podía cerrar. |
| 5 | El parser de tablas markdown no parte celdas en los `\|` escapados | Las 25 filas de verificación se descartaban → el validador fallaba con 0 gaps. |

Resultado: **34 gaps → 0** · **18 HUÉRFANOS → 0** · `XRAY COMPLETE` · `PASS=true` (13/13).

## 4 · Verificaciones (todas reales, 0 mock)

| Prueba | Resultado |
|---|---|
| Arnés general (`verify_all.py`) | **60/60 OK** |
| Frontend servido por la propia app (`/ui`) | **8/8 páginas limpias** (0 errores JS, 0 404) |
| Push transaccional contra doble local de la Git Data API | **18/18 OK** (1 commit, sin `/contents/`, `force=false`, read‑back, CONFLICT, sin autorización → aborta) |
| Auditor X‑Ray sobre el código refactorizado | **0 gaps** · `PASS=true` 13/13 |
| MCP por ventana | `w1` → 2 tools · `w2` → 3 · `w3` → 2 · tool fuera de allowlist → `-32601` · sin ventana → `-32602` · credenciales → `-32002` |
| Tools reales | `render_diagram` → `OMITIDO` con el ping real de `mmdc` · `audio_explain` → MP3 real (MPEG 24 kHz, 25.920 B) · `memory_index` → hits reales · `guide/match` → veredicto `NECESARIA` con rangos de líneas |

## 5 · Desviaciones y límites (declarados, no escondidos)

1. **El MCP ya no es arrancable por separado** (`python3 mcp_server.py --port 8078`): es un
   shim que avisa y delega. Es correcto para producción (un proceso), pero cambia el
   modo de depuración.
2. **El frontend se sirve en `/ui`**, no en `/`: `/` sigue siendo el índice JSON de rutas.
3. **`/guide/match` antes daba 404** (la app no tenía esa ruta): ahora es real, pero es
   una ruta **nueva** en el contrato HTTP.
4. Las tools del MCP ahora llaman a los motores **en proceso**: no dependen de que la
   API esté levantada en otro puerto (antes era un HTTP contra sí misma con un payload
   que no cumplía el contrato → `HTTP 422` → nunca renderizó nada).
5. El push **no** se ha ejecutado contra GitHub: `authorized_deploy` sigue vacío y la
   prueba se hizo contra un doble local de la API de Git.
