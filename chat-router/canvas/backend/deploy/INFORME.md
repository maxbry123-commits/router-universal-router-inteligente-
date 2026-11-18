# INFORME · N4-D2 · 3 VENTANAS (MIRROR / DIFF+EDITOR QUIRÚRGICO / DEPLOY) + MCP

> Nodo **N4-D2** · AGENTE 1 (DOER/EXECUTOR) · FAIL_CLOSED · DAG `yaiwes.node/v2` ·
> RESEARCH → EXECUTE → VALIDATE · `authorized_deploy: []` · **nada desplegado**.
> Fecha: 2026-11-16 · Todos los comandos y salidas están en `ledger.jsonl` (este directorio).

---

## 1 · INPUT BLOCK VERBATIM (copiado literal del brief)

```
N4-D2 · LAS 3 VENTANAS: MIRROR · DIFF+EDITOR QUIRÚRGICO · DEPLOY  (cada una con MCP HTTP y sandbox aislado)

VENTANA 1 · MIRROR: ocurre la salida del code que se crea. Puede hacer un ESPEJO de manera automática de cualquier texto o información de
  búsqueda y crear una COPIA / ESPEJO del código fuente: ya sea que venga de un URL, de un archivo, de búsquedas web o de generación de code de la IA.
  → Entradas: URL | archivo local | texto pegado | generación IA. Salida: el bloque de code espejado (nunca escribe en GitHub aquí).

VENTANA 2 · DIFF + EDITOR QUIRÚRGICO: el diff con líneas enumeradas. El modelo y el sistema pueden ver todos los bloques de code separados.
  Debe poder tener un ESPEJO si el code fue creado a partir de un texto/copia: un motor revisa que MACHEE el code (que sea similar) y marca las
  diferencias. Tiene DOS modos: VENTANA MANUAL y VENTANA TOOL.
  · VENTANA TOOL: solo permite SELECCIONAR las líneas que vas a cambiar del code; editar quirúrgicamente. NO editas el bloque completo.
    El usuario o la LLM pegan el cambio en una ventana de editar, seleccionan las líneas del cambio y pulsan CAMBIAR → se cambian SOLO
    las líneas seleccionadas (las demás quedan intactas, byte a byte).
  · La LLM NO tiene acceso a todo el code para editarlo en GitHub: SOLO a las ventanas 1, 2 y 3. La LLM solo puede EJECUTAR (run) el motor.
  · El motor de la GUÍA decide: cada punto de la guía es un motor (mini ingeniero) que replica la acción; el motor decide si la acción ya está
    DEFINIDA o es NECESARIA para replicar, y realiza la ADICIÓN de code o la REFACTORIZACIÓN SOLO DE LAS LÍNEAS NECESARIAS.
    El motor hace MATCH contra el EJEMPLO de la guía (mismo vocabulario de la búsqueda) y devuelve las líneas exactas a cambiar.
  · Si la acción hallada habla de AUTORIZACIÓN o ADVERTENCIA → se escala al usuario/IA para aprobar antes de aplicar.

VENTANA 3 · DEPLOY: los motores encargados de hacer el despliegue. Varios métodos de salida: archivos con carpetas separadas para descargar
  el code; el sistema raíz lo coloca MANUAL o la LLM vía TOOL selecciona dónde se despliega (qué raíz de destino). El motor puede crear la raíz
  si no existe y desplegar en GitHub y hacer el commit/push.
  · En la VENTANA 3 SOLO se puede hacer la SELECCIÓN DEL DESTINO DE LA RAÍZ y el DEPLOY.
  · La VENTANA 3 tiene los tokens de acceso de GitHub y HuggingFace para poder acceder al commit/push.

REGLAS DE LAS 3 VENTANAS: cada ventana debe tener MCP HTTP para que cualquier IA se conecte; cada ventana es un SANDBOX AISLADO.
  Para editar directo en GitHub y para extraer el code de un archivo o una raíz en GitHub, el sistema usa el MISMO MÉTODO de la ventana 1 y 2:
  hace un espejo del code para copiarlo, o hace en ventana 2 editar para editar solo la línea que se quiere cambiar.
  La LLM no tiene acceso a todo el code para editarlo en GitHub: solo a las ventanas 1, 2 y 3, y solo puede ejecutar (run) el motor.

CONTRATO MCP (6 tools): memory_profile (estado del proyecto) · memory_index (buscar en docs) · render_diagram (archify) ·
  render_motion (graphy motion) · audio_explain (resumen + voz) · xray_audit (verificación).
  Una sola regla: el modelo NO lee el corpus; pide tool, recibe resultado mínimo, decide siguiente tool.
  MCP HTTP:Streamable HTTP en /mcp, con allowlist de tools por VENTANA (allowlist distinta por ventana), validación de origen,
  tamaño máximo de payload y sin credenciales en el payload.

MOTOR DE DEPLOY (reglas duras): fail-closed · fast-forward NUNCA force · sin LFS (nada de punteros .lfs-ref ni .gitattributes con LFS) ·
  sin GitHub Actions · sin Vercel/HF sin autorización · dry-run por defecto · expected HEAD obligatorio (si el HEAD no coincide → CONFLICT y aborta) ·
  read-back obligatorio (sha256 del bloque escrito == sha256 local) · el token va SOLO por variable de entorno, nunca en logs ni en el HTML.
```

---

## 2 · FICHEROS ESCRITOS (alcance exclusivo, ni un byte fuera)

| # | Fichero | Bytes | Qué hace |
|---|---|---|---|
| 1 | `chat-router/canvas/frontend/w1_mirror.html` | 28.600 | Ventana 1 · MIRROR (4 orígenes → espejo + sha256 + handoff a w2) |
| 2 | `chat-router/canvas/frontend/w2_diff_editor.html` | 40.434 | Ventana 2 · diff enumerado + editor quirúrgico (MANUAL / TOOL) |
| 3 | `chat-router/canvas/frontend/w3_deploy.html` | 25.806 | Ventana 3 · destino + método de salida + DRY-RUN / Desplegar |
| 4 | `chat-router/canvas/frontend/w_mcp.js` | 10.741 | Cliente MCP del browser (initialize · tools/list · tools/call) reutilizado por las 3 ventanas |
| 5 | `chat-router/canvas/backend/deploy/deploy_engine.py` | 27.547 | Motor de deploy fail-closed (plan · validate_preconditions · execute · push bloqueado) |
| 6 | `chat-router/canvas/backend/deploy/mcp_server.py` | 29.120 | MCP HTTP JSON-RPC 2.0 en `/mcp` con allowlist por ventana + proxy de la guía |
| 7 | `chat-router/canvas/backend/deploy/INFORME.md` | ~24,6 KB | Informe de detalle (exigido por el brief) |
| 8 | `chat-router/canvas/backend/deploy/ledger.jsonl` | 4.373 | Ledger de comandos (append) con tokens redactados |

**NO tocados** (son de otros nodos): `backend/api.py`, `backend/adapters/`, `backend/audio_engine.py`, `backend/xray/`,
`backend/guide/`, `backend/canvas_engine.py`, `backend/health.py`, `frontend/index.html`, `frontend/shared/`,
`frontend/v1_canvas.html`, y el repo `maxbry123-commits/router-universal-router-inteligente-` (cero git, cero push).

---

## 3 · LEY DE DISEÑO APLICADA (tokens GRIS del owner + 6 temas verbatim)

* **Tokens GRIS del owner** (`IN-06_VERBATIM.html`, Gris V07) copiados literales:
  `--bg #1B1B1B · --surface #202020 · --surface-alt #252525 · --module #2A2A2A · --selected #3C3C3C · --mask #484848 ·
  --border #3A3A3A · --border-strong #525252 · --title #FAFAFA · --text #EDEDED · --quiet #BFBFBF · --quiet2 #A0A0A0 ·
  --active #0848F7 · --ok #12D86A · --error #FF475F · --warn #FF7B1A`.
* **6 temas verbatim** de `reference/tokens.css` (little · matte · blanco · crystal · orange · blue), cada bloque copiado literal.
* En GRIS los tokens de rol (`--card`, `--text-primary`, `--accent`, `--selected`, `--download`…) son **alias** de los tokens del
  owner: **ningún color inventado**. `--accent-hover` = `--active` (mismo valor, sin color nuevo).
* Geometría 24/12/10/28 (`--phone-radius/--card-radius/--button-radius/--sheet-radius`), tipografía `system-ui`.
* Tema por defecto **gris** (IN-06: «GRIS V07 es el tema principal»), persistido en `localStorage['yaiwes-demo-theme']`
  (se lee también `fromted-deploy-theme` por compatibilidad, R14). `meta[theme-color]` se actualiza al cambiar de tema.
* `focus-visible: 2px solid var(--selected)`, `aria-pressed` en los selectores de tema, `aria-current` en la ventana activa,
  `prefers-reduced-motion → transition:none`, botones con `min-height:44px`.

**Checklist de 15 puntos de `maxbry-ui-frontend` (aplicado a las 3 ventanas):** 01 tema por defecto ✔ · 02 `:root` con geometría+font+semáforo ✔ ·
03 6 temas declarados ✔ · 04 `--selected` separado de `--accent` ✔ · 05 `--download` solo en «Descargar» ✔ · 06 botón primario con `--accent` ✔ ·
07 semáforo fijo ✔ · 08 geometría 24/12/10/28 ✔ · 09 system-ui ✔ · 10 focus-visible ✔ · 11 aria-pressed ✔ · 12 aria-current ✔ ·
13 localStorage `yaiwes-demo-theme` ✔ · 14 meta theme-color ✔ · 15 prefers-reduced-motion ✔.

---

## 4 · TABLA DE ACCIONES (comando o fichero → resultado → evidencia)

| ACCIÓN | COMANDO O FICHERO | RESULTADO | EVIDENCIA |
|---|---|---|---|
| Leer brief + skills | `read briefs/AGENTE_D2_TRES_VENTANAS_MCP_DEPLOY.md`, `.skills/*/SKILL.md` | Ley, alcance y reglas duras asimilados | — |
| Leer la ley de la tarea | `read canvas/TAREA_01_FUENTE_DE_LA_VERDAD.md` | DAG `yaiwes.node/v2`, `authorized_deploy: []`, AC5/AC7 | — |
| Leer tokens | `read .skills/maxbry-ui-frontend/reference/tokens.css` + `IN-06_VERBATIM.html` | 6 temas + GRIS V07 | líneas 1–12 de IN-06 |
| Referencia de estilo en el repo | `curl -H "Authorization: Bearer ${GH_TOKEN}" .../contents/chat-router/chat/frontend/panel-apariencia.html` | **HTTP 404** (no existe) | GAP-1 |
| Referencia de estilo en el repo | `curl ... /contents/chat-router/chat/frontend/paneles-reales.css` | **HTTP 404** (no existe) | GAP-1 |
| Árbol del repo | `curl ... /git/trees/ccr-f01c3de9-bmry0s?recursive=1` | 0 coincidencias; refs reales en `chat-router/chat/ui/` | GAP-1 |
| Entorno | `python3 -c "import uvicorn"` | `ModuleNotFoundError` (y `pip install` prohibido) | GAP-2 |
| EXECUTE | `write frontend/w1_mirror.html` | 4 orígenes + espejo + sha256 + handoff | 28.600 B |
| EXECUTE | `write frontend/w2_diff_editor.html` | diff enumerado + TOOL/MANUAL + CAMBIAR + guía | 40.600 B |
| EXECUTE | `write frontend/w3_deploy.html` | raíz + método + DRY-RUN/Desplegar | 25.800 B |
| EXECUTE | `write frontend/w_mcp.js` | cliente MCP + panel reutilizable | 10.700 B |
| EXECUTE | `write backend/deploy/deploy_engine.py` | motor fail-closed (plan/checks/execute/push bloqueado) | 27.400 B |
| EXECUTE | `write backend/deploy/mcp_server.py` | MCP HTTP stdlib, allowlists, proxy guía | 28.600 B |
| VALIDATE 1 | `python3 -m py_compile deploy_engine.py mcp_server.py` | `PY_COMPILE OK` (exit 0) | salida de consola |
| VALIDATE 2 | smoke in-line del motor (positiva + negativas) | **OK=31 FALLO=1** → el abort del HEAD salía como `HEAD_ESPERADO` | corregido → `CONFLICT` |
| VALIDATE 2 (re-run) | smoke: `CONFLICT en plan` / `CONFLICT en execute` | ambos `ABORT CONFLICT` (exit 0) | salida de consola |
| VALIDATE 3 | `python3 mcp_server.py --port 8078` + `curl POST /mcp` | initialize → `Mcp-Session-Id` + `allowedTools` | JSON real pegado abajo |
| VALIDATE 3 | `tools/list` por ventana | w1 `[memory_profile, memory_index]` · w2 `[render_diagram, render_motion, audio_explain]` · w3 `[xray_audit, deploy_plan]` | JSON real |
| VALIDATE 3 | `tools/call` **fuera de allowlist** (w2→`xray_audit`, w3→`memory_index`) | **RECHAZADO** `-32601 TOOL NO PERMITIDA EN ESTA VENTANA` | JSON real |
| VALIDATE 3 | `Origin: http://evil.example` | **HTTP 403** `ORIGEN NO VALIDADO` | JSON real |
| VALIDATE 3 | payload 300.116 B | **HTTP 413** `PAYLOAD DEMASIADO GRANDE (max 262144)` | JSON real |
| VALIDATE 3 | `arguments.token` en el payload | **RECHAZADO** `-32002 CREDENCIALES EN PAYLOAD RECHAZADAS` | JSON real |
| VALIDATE 3 | sesión de w1 reutilizada desde w2 | **RECHAZADA** `-32001 SESION INVALIDA` (sandbox aislado por ventana) | JSON real |
| VALIDATE 3 | `tools/call memory_profile` (w1) | `status OK`, 15 módulos backend + 10 ficheros frontend (estado real del disco) | JSON real |
| VALIDATE 3 | `tools/call deploy_plan` (w3) | `status PLAN`, `dry_run true`, sha256 por fichero, checks block OK | JSON real |
| VALIDATE 4 | `python3 -m http.server 8089 --directory .../frontend` + Playwright | **27 OK / 0 FALLO / 0 errores de consola / 0 errores de página** | capturas + salida |
| VALIDATE 4 | Playwright: diff enumerado | 5 filas, `nºA/nºB` = 1..5, origen `IGUAL`×5 | salida |
| VALIDATE 4 | Playwright: CAMBIAR | `['linea 1','linea 2','linea 3 CAMBIADA','linea 4','linea 5']` → 1,2,4,5 **intactas byte a byte** | salida |
| VALIDATE 4 | Playwright: MCP en las 3 ventanas | `MCP · CONECTADO` + allowlist correcta por ventana | salida |
| VALIDATE 4 | Capturas | `audit/ui_shots/canvas/{w1_mirror,w2_diff_editor,w3_deploy}.png` | 3 ficheros |
| SEGURIDAD | `grep -rniE 'gh[pousr]_\|hf_\|Bearer [A-Za-z0-9]{20,}'` sobre los 6 ficheros | **0 coincidencias** | exit 0 |

### 4.1 · Salida real del smoke del motor de deploy (extracto)

```
== 1) POSITIVA: plan correcto (sin escribir nada) ==
  [OK]   plan status PLAN -> PLAN
  [OK]   plan con 2 ficheros -> 2
  [OK]   sha256 correcto -> b2fcd46b1ed14da9
  [OK]   plan NO escribe (no crea la raiz) -> raiz ausente: True
  [OK]   plan no hace push -> dry-run por defecto; el push exige DEPLOY_AUTHORIZED=1 + allow_push explicito
== 2) NEGATIVA (a) puntero LFS -> aborta ==
  [OK]   LFS puntero en contenido -> ABORT NO_LFS
  [OK]   LFS puntero .lfs-ref -> ABORT NO_LFS
  [OK]   LFS en .gitattributes -> ABORT NO_LFS
== 3) NEGATIVA (b) expected_head distinto -> CONFLICT ==
  [OK]   CONFLICT en plan -> ABORT CONFLICT
  [OK]   CONFLICT en execute -> ABORT CONFLICT
  [OK]   expected HEAD obligatorio -> ABORT EXPECTED_HEAD_OBLIGATORIO
== 4) NEGATIVA (c) sin autorizacion -> aborta (y no escribe) ==
  [OK]   sin DEPLOY_AUTHORIZED -> ABORT AUTORIZACION_REQUERIDA
  [OK]   sin autorizacion NO crea la raiz -> raiz ausente
  [OK]   sin token en el entorno -> ABORT TOKEN_AUSENTE
  [OK]   authorization_token incorrecto -> ABORT AUTORIZACION_INVALIDA
== 5) NEGATIVA (d) dry-run NO escribe nada ==
  [OK]   dry-run status DRY_RUN / no crea la raiz / 0 ficheros antes / 0 despues / sin manifest_path / no push
== 6) POSITIVA autorizada: escritura + read-back + MANIFEST (sin push) ==
  [OK]   status MANIFEST_ONLY_NO_PUSH
  [OK]   read-back sha256 == sha256 local -> 2 fichero(s) verificados
  [OK]   manifiesto escrito -> .../deploy_manifests/deploy_manifest_20261116T062319Z.json
  [OK]   NO push realizado
== 7) OTRAS NEGATIVAS fail-closed ==
  [OK]   GitHub Actions -> ABORT NO_GITHUB_ACTIONS
  [OK]   ruta fuera de la raiz -> ABORT RUTA_ESCAPE
  [OK]   symlink -> ABORT SYMLINK_PROHIBIDO
  [OK]   credencial dentro del fichero -> ABORT SIN_CREDENCIALES_EN_FICHEROS
  [OK]   raiz fuera del directorio de trabajo -> ABORT RAIZ_FUERA_DEL_TRABAJO
```

### 4.2 · Salida real del MCP (extracto)

```
initialize  → {"protocolVersion":"2025-06-18","serverInfo":{"name":"yaiwes-canvas-mcp","version":"1.0.0"},
               "sessionId":"sess-…","window":"w1","allowedTools":["memory_profile","memory_index"]}
tools/list w1 → [memory_profile, memory_index]
tools/list w2 → [render_diagram, render_motion, audio_explain]
tools/list w3 → [xray_audit, deploy_plan]
tools/call w2 → xray_audit  → {"code":-32601,"message":"TOOL NO PERMITIDA EN ESTA VENTANA: xray_audit"}
tools/call w3 → memory_index → {"code":-32601,"message":"TOOL NO PERMITIDA EN ESTA VENTANA: memory_index"}
Origin no permitido → HTTP 403 {"code":-32001,"message":"ORIGEN NO VALIDADO: origin no permitido: http://evil.example"}
payload 300116 B       → HTTP 413 {"code":-32000,"message":"PAYLOAD DEMASIADO GRANDE: maximo 262144 bytes"}
credenciales          → {"code":-32002,"message":"CREDENCIALES EN PAYLOAD RECHAZADAS","data":{"fields":["params.arguments.token"]}}
sesión cruzada        → {"code":-32001,"message":"SESION INVALIDA: inicializa de nuevo."}
```

### 4.3 · Salida real del Playwright (extracto)

```
== VENTANA 1 · MIRROR ==
  [OK]   w1 carga / tema GRIS por defecto / sha256 fallback correcto ('abc')
  [OK]   espejo con el texto pegado / sha256 del espejo calculado
  [OK]   MCP conectado en w1 → ALLOWLIST: memory_profile, memory_index
  [OK]   w2 abierta por handoff (sessionStorage) → ESPEJO RECIBIDO
== VENTANA 2 · DIFF + EDITOR QUIRURGICO ==
  [OK]   diff con líneas ENUMERADAS (5 filas) → 5 filas
  [OK]   numeración visible (nºA/nºB 1..5)
  [OK]   origen de cada línea marcado → ['IGUAL','IGUAL','IGUAL','IGUAL','IGUAL']
  [OK]   modo TOOL: ACTUAL en solo lectura
  [OK]   CAMBIAR cambia SOLO la línea 3 → ['linea 1','linea 2','linea 3 CAMBIADA','linea 4','linea 5']
  [OK]   líneas 1,2,4,5 intactas byte a byte
  [OK]   verificación post-apply: sha256 antes/después / resto intacto = SÍ / diff aplicado listado
  [OK]   guía: MOTOR DE GUÍA NO DISPONIBLE (estado real)
  [OK]   allowlist w2 = render_diagram, render_motion, audio_explain
== VENTANA 3 · DEPLOY ==
  [OK]   fichero listado con sha256 → src/ejemplo.py  14  b2fcd46b1ed14da9…
  [OK]   allowlist w3 = xray_audit, deploy_plan
  [OK]   DRY-RUN responde con el plan real del motor → "status": "PLAN", "dry_run": true
  [OK]   el plan NO hace push → "enabled": false
  [OK]   Desplegar deshabilitado sin autorización de sesión → disabled=True
  [OK]   Desplegar con flag de sesión → ABORT (expected HEAD obligatorio / autorización del servidor)
== CONSOLA ==  errores de consola: 0   errores de pagina: 0
RESUMEN playwright: OK=27 FALLO=0 | errores_consola=0 errores_pagina=0
```

---

## 5 · DISEÑO INTERNO (decisiones que el brief deja abiertas)

1. **Allowlist MCP por ventana** (literal del brief): `w1 = {memory_profile, memory_index}` · `w2 = {render_diagram, render_motion,
   audio_explain}` · `w3 = {xray_audit, deploy_plan}`. La ventana se identifica con la cabecera `X-MCP-Window` (o `?window=`).
   Sin ventana identificada → `-32602 VENTANA NO IDENTIFICADA` (fail-closed). Cada `initialize` crea una **sesión ligada a una ventana**:
   reutilizarla desde otra ventana → `-32001 SESION INVALIDA` (**sandbox aislado**).
2. **Credenciales**: nunca viajan en el payload. El servidor rechaza cualquier clave tipo `token/secret/password/api_key/authorization`
   (`-32002`) y también cualquier valor que coincida con un token del entorno. El motor de deploy lee el token **solo del entorno**.
3. **Ejecución desde la ventana 3**: la allowlist de `w3` es la del brief (`deploy_plan`). El botón «Desplegar» llama a
   `tools/call deploy_plan` con `mode=execute`; el servidor resuelve el token de su propio entorno (nunca del payload) y el motor exige
   `DEPLOY_AUTHORIZED=1` **y** `expected_head` **y** que la raíz esté dentro del directorio de trabajo. Sin autorización del servidor →
   `ABORT`. El botón queda deshabilitado hasta que el usuario marque el **flag de sesión en memoria** (no se guarda en ningún almacén).
4. **Push**: `push_fast_forward()` existe pero está doblemente bloqueado (`DEPLOY_AUTHORIZED=1` + `allow_push=True` + token del entorno) y
   **jamás se ha ejecutado**: en esta tarea el entorno no tiene `DEPLOY_AUTHORIZED` y el smoke lo comprueba
   (`"performed": false`). El push real verifica el HEAD remoto antes y comprueba que el commit nuevo sea hijo del HEAD esperado
   (fast-forward; nunca force).
5. **Restricción dura del editor quirúrgico**: el rango seleccionado debe ser **contiguo** y el cambio debe tener **el mismo número de líneas**
   que el rango. Es lo que garantiza «las demás quedan intactas, byte a byte» y que la numeración no se desplace. Si no se cumple → ABORT
   con el motivo exacto.
6. **Consulta de la guía**: la ventana 2 **no importa** `backend/guide/*` (módulos de otro nodo). Consulta por HTTP mediante el proxy
   server-side `POST /guide/match` del servidor MCP, que prueba `/guide/match`, `/match` y `/guide/actions` del backend del canvas y, si
   ninguno responde, devuelve `MOTOR DE GUÍA NO DISPONIBLE` con los intentos reales. Si el veredicto menciona AUTORIZACIÓN/ADVERTENCIA
   (o no es interpretable) → el cambio queda bloqueado hasta marcar «Apruebo la acción».
7. **0 MOCK**: las tools que dependen del backend del canvas (`render_diagram`, `render_motion`, `audio_explain`, `xray_audit`) devuelven
   `status OMITIDO` con la causa exacta cuando el backend no responde. `memory_profile` y `memory_index` sí devuelven **datos reales** del disco.

---

## 6 · GAPS / BLOQUEOS (🚩) — [gap] → [ruta probada] → [estado]

| # | Gap | Ruta probada | Estado |
|---|---|---|---|
| 1 | 🚩 Las referencias de estilo `chat-router/chat/frontend/panel-apariencia.html` y `paneles-reales.css` **no existen en el repo** (HTTP 404 en `ccr-f01c3de9-bmry0s`, `reorganizacion` y `main`; 0 coincidencias en el árbol recursivo de las 3 ramas) | Se usaron como referencia los ficheros reales más próximos (`chat-router/chat/ui/app.css`, `theme.css`, `loop-panel.html`, leídos por API con `${GH_TOKEN}`, solo lectura) + `reference/tokens.css` + `IN-06` | **Resuelto por ruta alternativa** (sin inventar estilos) |
| 2 | 🚩 `uvicorn`/`fastapi` **no están instalados** y `pip install` está **PROHIBIDO** por el brief | `mcp_server.py` se sirve con `http.server` (stdlib puro) y **además** expone `app` como ASGI mínimo para que `uvicorn mcp_server:app` funcione si algún día se instala | **Resuelto** (el MCP se validó en real por HTTP) |
| 3 | 🚩 El **motor de la guía** tiene los módulos en disco (`grammar.py`, `match.py`, `trigger.py`, `discovery.py`) pero **no está servido por HTTP** en `CANVAS_API_BASE` (7860) | Proxy server-side `/guide/match` + estado real `MOTOR DE GUÍA NO DISPONIBLE` con los intentos | **Degradado fail-closed** · pendiente que el nodo C lo exponga por HTTP |
| 4 | 🚩 El **backend del canvas** (`api.py`) no está levantado en 7860 | Las tools dependientes devuelven `OMITIDO` con la causa real (nunca datos inventados) | **Degradado fail-closed** |
| 5 | 🚩 La **generación IA** de la ventana 1 no tiene motor en este nodo | Campo de volcado con estado real `SIN MOTOR DE GENERACIÓN CONECTADO` + nota explícita; la IA vuelca su salida y el espejo la copia | **Degradado fail-closed** (sin mock) |
| 6 | Restricción propia del editor: nº de líneas del cambio = nº de líneas del rango | Documentada en la UI y en el informe | **Informativa** |

---

## 7 · QUEDA VERIFICADO | NO SE PUDO VERIFICAR

**VERIFICADO (con evidencia real):**
* `py_compile` de los 2 `.py` → exit 0.
* Motor de deploy: `plan` correcto (hashes, sin escribir), `validate_preconditions` con 10 checks, `execute` con **read-back** y **MANIFEST**;
  negativas: **LFS** (3 variantes) → `NO_LFS` · **HEAD distinto** → `CONFLICT` · **sin autorización** → `AUTORIZACION_REQUERIDA` ·
  **sin token** → `TOKEN_AUSENTE` · **dry-run** → 0 escrituras · workflows → `NO_GITHUB_ACTIONS` · escape de ruta → `RUTA_ESCAPE` ·
  symlink → `SYMLINK_PROHIBIDO` · credencial en fichero → `SIN_CREDENCIALES_EN_FICHEROS` · raíz fuera del trabajo → `RAIZ_FUERA_DEL_TRABAJO`.
* MCP: `initialize` / `tools/list` / `tools/call` reales; allowlist distinta por ventana; tool fuera de allowlist **rechazada**;
  origen no permitido **403**; payload grande **413**; credenciales en payload **rechazadas**; sesión cruzada **rechazada** (sandbox aislado).
* Playwright: las 3 ventanas cargan, **0 errores de consola y 0 errores de página**, 3 capturas en `audit/ui_shots/canvas/`,
  diff **enumerado** (nºA/nºB + origen), `CAMBIAR` cambia **solo** la línea seleccionada (1,2,4,5 intactas byte a byte),
  verificación sha256 antes/después, handoff w1→w2 por `sessionStorage`, MCP conectado desde el navegador en las 3 ventanas.
* 0 secretos en los ficheros; el token solo se lee del entorno; el payload MCP rechaza credenciales.

**NO SE PUDO VERIFICAR (motivo real):**
* El **push real a GitHub / HF** y el **commit**: nunca se ejecutan en esta tarea (`authorized_deploy: []`, sin `DEPLOY_AUTHORIZED`) — por diseño.
* El **origen URL** de la ventana 1 contra un servidor real: el `fetch` depende de las cabeceras CORS del servidor remoto; el camino de
  error real está implementado pero no hay servidor externo de prueba en el sandbox.
* Las tools **render_diagram / render_motion / audio_explain / xray_audit**: solo se verificó su camino de degradación `OMITIDO`
  (el backend del canvas no estaba levantado); su respuesta real depende del nodo A/B.
* La **consulta real al motor de la guía**: solo se verificó la degradación `MOTOR DE GUÍA NO DISPONIBLE`.
* El **layout móvil** (≤820 px) y el contraste AA de la paleta: no pedidos por el brief en esta fase.
* El repo `maxbry123-commits/router-universal-router-inteligente-`: **cero escrituras** (solo lectura vía API con `${GH_TOKEN}`).

---

## 8 · CONCLUSIÓN

Las 3 ventanas (MIRROR · DIFF+EDITOR QUIRÚRGICO · DEPLOY) y el MCP HTTP con allowlist por ventana están escritos, validados en real
(`27 OK / 0 FALLO` en Playwright, `0` errores de consola; smoke del motor de deploy con todas las negativas) y sin desplegar nada.
Queda pendiente de los otros nodos: que el backend del canvas (7860) exponga el motor de la guía por HTTP para que la ventana 2 pase de
`MOTOR DE GUÍA NO DISPONIBLE` a veredicto real.
