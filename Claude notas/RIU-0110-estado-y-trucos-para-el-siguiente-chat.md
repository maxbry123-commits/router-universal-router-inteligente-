# RIU-0110 — ESTADO Y TRUCOS PRÁCTICOS PARA EL SIGUIENTE CHAT (2026-09-20)

Lee primero: `00-LEEME-PRIMERO.md` (estado viejo) y, más nuevo, `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0108-PLAN-MAESTRO-CHAT-MVP.md`, `RIU-0109-...` y `RIU-0110-AVANCE-S0-S1-S2.md`. Inputs textuales del Director: `INPUT-BLOCKS-01-04-VERBATIM.md`, `INPUT-BLOCK-05-...`, `INPUT-BLOCK-06-VERBATIM.md`, `INPUT-BLOCK-07-VERBATIM.md`.

## Dónde estamos
Prioridad única: el chat. Hecho y probado en runner: chat por el Router con Kimi K3 / DeepSeek V4 / MiniMax M3 (RIU-0105), escáner de credenciales (S0), `Chat Mvp/` con `groups.yaml` y `accounts.yaml` (S1), núcleo del Secret Bank con 9 tests (S2.1-2.3). Siguiente: S2.4-2.5 (API y gateway con el broker), luego S3 (Space Docker con Open WebUI).

## Reglas que el Director repite (no las rompas)
1. Nada de credenciales en texto plano en ningún sitio ni en el chat. Si pega alguna, no la uses, no la guardes, no la repitas y dile que la rote. Ya pegó 4 (1 de HF y 3 de GitHub) en el mensaje 06.
2. Cada instrucción del Director se anota textual, 1 a 1, y cada paso se marca en `Claude notas/`, `Readme arquitectura…/` y la carpeta de la bitácora.
3. Investigar con el motor de búsqueda del repo (no gastar tokens del LLM); descargar con los motores.
4. No pasar al Paso 2/3 hasta cerrar el chat. Escribimos solo en este repo (P3).

## Trucos que ahorran tiempo
- API de GitHub por el conector: `github_api` con `body` para POST/PUT (con `params` da 422); `params` es solo para GET.
- Lanzar una búsqueda: `POST /repos/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-websearch-run.yml/dispatches` con `{"ref":"main","inputs":{"query":"…","providers":"ddgs"}}`; el resultado aparece en `router inteligente universal/websearch-results/ws-<run>/summary.md` en menos de un minuto. Lista de carpetas con `git/trees/main:router%20inteligente%20universal%2Fwebsearch-results` (respuesta pequeña).
- Leer resultados de un workflow: anotaciones del check-run (`/actions/runs/<id>/jobs` → `id` del job → `/check-runs/<id>/annotations`); los logs devuelven vacío. Los workflows de este repo emiten `::notice`/`::warning` con el resultado.
- EVITA `/actions/workflows/<f>/runs` y `/search/code`: devuelven decenas de KB de JSON. Prefiere `per_page=1` y no repitas la consulta.
- El límite `params` de `/search/code` da resultados con ruido (`abc123` coincide con documentación de skills); no sirve para buscar cuentas.
- La API no permite añadir al final de un archivo: cada nodo va en un archivo nuevo. `BITACORA-CRAZY-WALL.md` (33 KB) y `memoria.md` (53 KB) no se reescriben; proponer al Director la partición por tramos.
- `HF_TOKEN_1` es full access sobre `COMAND-CENTER-1` (`repo.write`, `job.write`, endpoints), aunque su lista `global` solo muestre `discussion.write` y `post.write`: los permisos reales están en el bloque `scoped`.
- Mi herramienta `hf_fs` es de solo lectura (`ls cat attach stat find search`); para escribir en HF hay que usar workflows con `HF_TOKEN_1`.
- Numeración: RIU-0105 (chat MVP), 0106 (otro chat), 0107-0110 (estas notas). Comprueba la carpeta antes de tomar un número.

## Pendiente del Director
Rotar las 4 credenciales pegadas; login público de las cuentas `abc123` y `planeta 123`; aprobar la enmienda del contrato del registry (`HF_JOB_EPHEMERAL_SERVING`) y el gasto de céntimos de la prueba S7.3; lista del pool de agentes.
