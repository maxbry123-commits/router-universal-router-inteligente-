# TAREA 1 · FUENTE DE LA VERDAD · CANVAS VISUAL + 3 VENTANAS DIFF/DEPLOY

> **Este fichero es la fuente de la verdad de la TAREA 1.** Todo lo que se ejecute en esta
> tarea se contrasta contra este documento. El `INPUT BLOCK VERBATIM` está congelado con
> SHA‑256 abajo; el DAG es `yaiwes.node/v2`; los gates son secuenciales y FAIL_CLOSED.
>
> **Regla de raíz:** la estructura `canvas/` del enunciado se materializa **dentro** de la raíz
> única `chat-router/` → `chat-router/canvas/`. No se crea raíz nueva en el repo.
> **Rama de trabajo:** `ccr-f01c3de9-bmry0s` (serie MINIMAX). `main` no se toca en esta tarea.

---

## 1 · INPUT BLOCK VERBATIM (congelado)

| ID | Origen | Bytes | SHA‑256 |
|---|---|---|---|
| IB‑01 | `🏗️1 -PROMPT_BACKEND_ECC_RICARDO_INVESTIGACION.md` | 16.277 | `f21fcc5e1ea093ae…` (ver manifest) |
| IB‑02 | `🏗️ 02_PROMPT_ADICIONAL_CHAT1_BACKEND_MOTORES.md` | 8.263 | `9c780eef1e1bf487…` |
| IB‑03 | `🏗️ 03_AUDITORIA_Y_UBICACIONES.md` | 7.097 | `f77f61e3e70bc954…` |
| IB‑04 | `📌PROMPT_CHAT1_BACKEND_GAPS_FRONTEND_V03_YAIWES.md` | 15.380 | `2eccdd5fece20505…` |
| IB‑05 | `03-PROMPT_FRONTEND_MECANICO_LOOP_V07.md` | 11.801 | `e2d7a71a828e484d…` |
| IN‑06 | `YAIWES-PANELES-PALETAS-V2.html` | 26.181 | `9371f690b2e9…` |
| IN‑07 | `panel-media.html` (versión A) | 7.478 | `ef833fece97a…` |
| IN‑08 | `panel-agentes.html` (versión A) | 5.237 | `b2359d2f3020…` |
| IN‑09 | `panel-media.html` (versión B) | 9.170 | `585bef9accc1…` |
| IN‑10 | `panel-agentes.html` (versión B) | 5.949 | `5dfe51174437…` |
| IN‑11 | `panel-configuracion.html` | 14.642 | `332184e478a2…` |

Manifiesto completo con SHA‑256 de 64 caracteres: `audit/recepcion_20261116/MANIFEST_INPUT_BLOCKS.json`.
Copias byte‑exactas: `audit/recepcion_20261116/IB-0*_VERBATIM.md` · `IN-*_VERBATIM.html`.
Registro de recepción 1:1: `audit/recepcion_20261116/RECEPCION_1a1.md`.

**Enunciado del owner (Tarea Canvas Visual · Micro resumen + Flujos + 3 ventanas DIFF/deploy)**
queda también congelado en el mensaje de entrada de esta sesión; su desglose operativo es
este DAG.

---

## 2 · OBJETIVO

Construir **en el sandbox** (sin publicar nada salvo este fichero) un sistema de 2 capas:

**Capa A · CANVAS VISUAL** — 5 sistemas independientes (Mapa Mental · Archify · Graphy Motion ·
Audio · Auditoría X‑Ray), 4 ventanas (V1 Canvas · V2 Progress · V3 Architecture · V4 Audit),
backend Python primero (6 adapters aislados + engine + API REST/WS) y **motor de audio
explicativo sin LLM en la conversión** (resumen ≤150 palabras → traducción opcional →
edge‑tts → `.mp3`).

**Capa B · 3 VENTANAS DIFF/DEPLOY** —
- **V1 Mirror**: crear/copiar un bloque de código desde URL, archivo, búsqueda web o generación de IA.
- **V2 Diff + editor quirúrgico**: la LLM lee y decide; **solo se escriben las líneas seleccionadas**;
  dos modos (manual y tool); el motor de la guía decide si la acción está definida y **qué líneas** tocar;
  un motor de *match* compara el código contra el ejemplo de la guía; un motor gramatical
  (objeto/verbo/adjetivo) descompone la acción; un motor de descubrimiento busca la acción en guías,
  skills,社区 y RAG; la acción se convierte en **trigger** ejecutable por fases.
- **V3 Deploy**: selección de raíz de destino, motor con tokens GitHub/HF, commit + push.
  Las 3 ventanas exponen **MCP HTTP** y son **sandboxes aislados**.

**Una sola regla de todo el sistema:** el modelo **no lee el corpus**; pide *tool* y recibe el
resultado mínimo. `PASS` solo lo emite el validador determinista, nunca el LLM.

---

## 3 · DAG (yaiwes.node/v2)

```yaml
schema: yaiwes.node/v2
mode: FAIL_CLOSED
function: ExecuteNode(NodeInput) -> NodeOutput
repo: maxbry123-commits/router-universal-router-inteligente-
branch: ccr-f01c3de9-bmry0s
objective: >-
  Construir en sandbox el Canvas Visual (5 sistemas / 4 ventanas / backend Python con
  6 adapters + audio explicativo + auditor X-Ray + gaps) y las 3 ventanas
  Mirror / Diff-Editor-Quirurgico / Deploy con MCP HTTP y sandbox aislado,
  mas la guia viva de acciones con motores (gramatica, discovery, trigger, match).
authorized_deploy: []          # NINGUN deploy autorizado en esta fase
input:
  acceptance_criteria:
    - "AC1 Backend canvas: 6 adapters con ping() fail-closed (OK|OMITIDO), canvas_engine, api.py REST+WS /health, /render/diagram, /render/motion, /convert"
    - "AC2 Audio: audio_engine.py con resumen <=150 palabras, traduccion opcional, edge-tts con fallback pyttsx3, cache por hash, /audio/explain y /audio/{id}"
    - "AC3 X-Ray: xray_audit.py fases 0-9 deterministas -> STATE/INVENTORY/WIRING/CONTRACTS/GAPS/NEXT_ACTIONS/XRAY_REPORT/FINGERPRINT + validador PASS y gaps API con evidencia ruta:linea"
    - "AC4 Frontend canvas: shell + V1..V4 + shared/api.js + shared/ws.js, cada ventana una URL propia, FROMTED (6 temas + gris), 0 mock (llama al backend real)"
    - "AC5 3 ventanas: V1 Mirror (crear/copiar bloque), V2 Diff + editor quirurgico (solo lineas seleccionadas, modos manual/tool), V3 Deploy (destino + commit/push)"
    - "AC6 Motores de la guia: gramatica (objeto/verbo/adjetivo), discovery con RAG (10 dominios de investigation_sources.json), conversion accion->trigger, match contra el ejemplo de la guia"
    - "AC7 MCP HTTP por ventana + sandbox aislado (allowlist de tools, postMessage con validacion de origen)"
    - "AC8 Archivos ANTES y DESPUES de todo lo que quedaria en el deploy, para revision"
    - "AC9 Propuestas HTML por ventana con mejoras de 0 friccion"
    - "AC10 Nada publicado salvo este fichero de fuente de verdad; NO LFS, NO GitHub Actions, NO otro sistema que no sean los motores de descarga/extraccion"
  tasks:
    - { id: T0, goal: "Congelar input blocks, verificar rutas reales del repo, escribir este fichero y publicarlo", ac_ids: [AC10], depends_on: [] }
    - { id: T1, goal: "Backend canvas: 6 adapters + canvas_engine + api + health + audio_engine + requirements", ac_ids: [AC1, AC2], depends_on: [T0] }
    - { id: T2, goal: "Auditor X-Ray (fases 0-9) + gaps store/API con validacion de evidencia", ac_ids: [AC3], depends_on: [T0] }
    - { id: T3, goal: "Guia viva: motores de gramatica, discovery/RAG, accion->trigger, match contra ejemplo", ac_ids: [AC6], depends_on: [T0] }
    - { id: T4, goal: "Frontend canvas: shell + V1..V4 + shared (api/ws/theme) con 0 friccion", ac_ids: [AC4, AC9], depends_on: [T1, T2] }
    - { id: T5, goal: "3 ventanas Mirror/Diff/Deploy + MCP HTTP + sandbox + motor de deploy", ac_ids: [AC5, AC7], depends_on: [T3] }
    - { id: T6, goal: "Validacion real: arranque del backend, smoke de endpoints, Playwright de las 7 ventanas, capturas", ac_ids: [AC1, AC2, AC3, AC4, AC5], depends_on: [T1, T2, T3, T4, T5] }
    - { id: T7, goal: "Empaquetado de auditoria: ANTES/DESPUES + 4 grupos de entrega + zip + informe", ac_ids: [AC8, AC9, AC10], depends_on: [T6] }
steps: { count: EXACTLY_3, order: [RESEARCH, EXECUTE, VALIDATE] }
parallel: { enabled: true, max_agents: 4, exclusive_files_per_agent: true }
gates: [NO_AUTHORIZATION: FLAG, NO_REAL_TEST: NO_PASS, NO_EVIDENCE: NO_PASS, OBJECTIVE_DRIFT: FAIL]
flag: { symbol: "🚩", allowed_only_if: "objective not solvable via existing code, documents, research or alternative routes", effect: "never stops, never escalates, never asks" }
```

### Nodos de ejecución (agentes en paralelo, ficheros exclusivos)

| Nodo | Agente | Ficheros exclusivos (solo sandbox) |
|---|---|---|
| N4‑A | **A · Backend canvas + audio** | `chat-router/canvas/backend/{adapters/*.py, canvas_engine.py, api.py, health.py, audio_engine.py, requirements.txt}` |
| N4‑B | **B · X‑Ray + gaps** | `chat-router/canvas/backend/xray/{xray_audit.py, gaps_store.py, README.md}` |
| N4‑C | **C · Motores de la guía viva** | `chat-router/canvas/backend/guide/{grammar.py, discovery.py, trigger.py, match.py, guide_actions.json, README.md}` |
| N4‑D | **D · Frontend (7 ventanas + MCP)** | `chat-router/canvas/frontend/**` (shell, shared, v1..v4, w1..w3, mcp) + `chat-router/canvas/backend/deploy/{deploy_engine.py, mcp_server.py}` |

El orquestador (esta sesión) ejecuta **N4‑E · integración + validación** y **N4‑F · empaquetado de
auditoría**, y es el único que escribe en el repo (y solo este fichero).

---

## 4 · COMPONENTES AUTORIZADOS (solo estos, cero código fuera de la lista)

| Tipo | Componentes | Estado en el sandbox |
|---|---|---|
| Diagramas | Excalidraw · Mermaid · D2/Terrastruct | adapters con `ping()`; si el binario no está → `OMITIDO` (fail‑closed, no bloquea) |
| Motion | HyperFrames · Remotion · Rive | ídem |
| Archify | skill del repo `…/workflow-loop-yaiwes/archify/` | instalada en repo; `bin/archify.mjs` + `bin/preview.mjs` + `bin/visual-check.mjs` |
| Audio | edge‑tts (o fallback pyttsx3) · deep‑translator (opcional) | importación opcional, degradación explícita |

**Motores de descarga y extracción (únicos permitidos):**
`yaiwes.hf.download-extract.v1` — bundle por partes ≤12.582.912 B, `sha256` por parte, `no_lfs:true`,
reconstrucción verificada. Manifiesto real: `…/archify/DOWNLOAD_EXTRACT_MANIFEST.json`
(`source_repo: tt-a1i/archify`, `source_commit: d0c8c7e9f4e06f303389f804208d387f27019ef5`,
`bundle_sha256: 7216507b536ab0ce2f1a644262461a7cec6d3353a84c130217d3f2b25f97ebc4`,
`extracted_tree.sha256: 1b7fead3e626e20f9261738ceb526a497fff43af0d05402bf8b6611f3ce01e50`).
**Prohibido** `pip install`, `npm install`, `curl` de binarios, `git clone` de externos, LFS y
GitHub Actions. Si un componente no está, se reporta `OMITIDO` con su comando de ping.

---

## 5 · REGLAS DURAS (aplican a todos los nodos)

| Regla | Detalle |
|---|---|
| NO LFS | Ningún puntero LFS. Nada de `.lfs-ref`. Nada de `.gitattributes` con LFS. |
| NO GITHUB ACTIONS | Ni workflows, ni jobs, ni runners. |
| NO OTRO SISTEMA | Solo el motor `yaiwes.hf.download-extract.v1` y los motores ya existentes del repo (`Loop/nct_loop/*`). |
| NO DESPLEGAR SIN AUTORIZACIÓN | `authorized_deploy: []`. Nada de push de código, nada de restart de Space, nada de Vercel/HF. **Solo** este fichero de fuente de verdad. |
| FAIL_CLOSED | Si un adapter no responde → `OMITIDO` + causa exacta. Si una prueba no existe → no PASS. |
| EVIDENCIA > CONFIRMACIÓN | Cada entregable lleva comando, salida, exit code y timestamp. |
| 0 SECRETS | Nada de tokens en ficheros, logs, prompts ni capturas. Variables por entorno. |
| 1 FUNC = 1 FICHERO | Sin monolitos. `api.py` solo enruta; la lógica va en su módulo. |
| LEY DE FRONTEND | Tokens y geometría de `maxbry-ui-frontend` (6 temas) + variante `gris` del owner (`IN‑06`…`IN‑11`). Sin estilos inventados. |
| 0 MOCK | Las ventanas del frontend no pintan datos falsos: muestran `OMITIDO`/error real cuando el backend no responde. |

---

## 6 · FORMATO DE ENTREGA (obligatorio, en este orden)

```
1. ARCHIVOS DE BACKEND      → para auditar
2. FRONTEND HTML FUNCIONAL  → sin mock, para auditar
3. CÓDIGO FRONTEND VIEJO Y NUEVO → para revisar que nada se rompe
4. HTML DE PROPUESTAS POR VENTANA → mejoras 0 fricción
```

---

## 7 · ESTADO

| Campo | Valor |
|---|---|
| `state` | `PENDING` |
| `progress_pct` | 0 |
| `flags` | 0 |
| `authorized_deploy` | `[]` |
| `commit_deploy` | ninguno (este fichero es la única escritura) |
