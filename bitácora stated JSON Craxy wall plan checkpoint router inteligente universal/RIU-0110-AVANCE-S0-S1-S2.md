# RIU-0110 — AVANCE: S0 (escáner), S1 (Chat Mvp), S2.1-2.3 (núcleo del Secret Bank) — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Continúa `RIU-0108-PLAN-MAESTRO-CHAT-MVP.md` y `RIU-0109-DECISIONES-Y-ANALISIS-HF-JOBS.md`. Sin input nuevo del Director en este nodo (instrucción: "ve haciendo otras cosas" mientras corre la búsqueda).

## Hecho, con evidencia de runner real
| Salida | Qué | Commit | Evidencia |
|---|---|---|---|
| S0 | `.github/workflows/riu-secret-scan.yml`: falla si hay credenciales en texto plano; no imprime valores; autoprueba de patrones | `6e2466d6` | run `35495612128`, check-run `106037887477`: `scanned=383 findings=0`, autoprueba PASS. Límites: solo el árbol actual (no el historial de git), excluye el pool de donantes |
| S1 | `Chat Mvp/README.md`, `groups.yaml`, `accounts.yaml` | `6879fd97`, `44ef88c1`, `23bb1faa` | run `35495612111`, check-run `106037887491`: 20 modelos, 0 problemas; eliminados no presentes; ambas LFM2 presentes; sin credenciales; logins pendientes `abc123`, `planeta123` |
| S2.1 | `Chat Mvp/secret_bank/vault.py`: SQLite + AES-256-GCM por valor, scrypt, AAD por credencial, auditoría sin valores | `1ff7f303` | mismos tests |
| S2.2 | `session.py`: login una vez, TTL, logout | `4a41a136` | mismos tests |
| S2.3 | `broker.py`: `with_secret(...)` fail-closed (lista vacía deniega, `*` permite), auditoría de USE/DENIED | `fc7bd260` | mismos tests |
| Tests | `Chat Mvp/tests/test_secret_bank.py` | `086190e3` | 9 passed en local y en runner (check-run `106037887491`): contraseña incorrecta, el archivo no contiene el secreto ni la contraseña, cifrado distinto por valor, copia de seguridad restaurable, referencias inválidas, valor no movible entre credenciales, rotar/deshabilitar/caducar/borrar, permisos y auditoría, sesión y TTL |
| CI | `.github/workflows/riu-chat-mvp-core-verify.yml` | `6bc9be24` | dispara en cambios de `Chat Mvp/**` |

## Otros hechos de este tramo
- Motor de búsqueda del repo utilizable sin gastar tokens del LLM: `riu-websearch-run.yml` (9 corridas PASS en total; resultados en `router inteligente universal/websearch-results/`).
- Se dispara con `POST /repos/.../actions/workflows/riu-websearch-run.yml/dispatches` y campo `body` (con `params` da 422).

## Pendiente del Secret Bank (no hecho)
S2.4 API HTTP (`/bank/unlock|lock|credentials|rotate|disable|audit`), S2.5 integración con el gateway (`credential_ref` en lugar de `HF_TOKEN`), S2.6 página `/bank`, S2.7 copia cifrada al repo privado de HF, S2.8 passkey/WebAuthn. Hasta entonces el gateway sigue usando `HF_TOKEN` del entorno.
Límite conocido de diseño: la clave de descifrado vive solo en memoria de la sesión; al reiniciarse el Space hay que iniciar sesión de nuevo (una vez por arranque).

## GAPs
Abiertos: `GAP-SECRET-BANK-001` (S2.4-2.8), `GAP-GH-LOGINS-001`, `GAP-CONTRACT-JOB-SERVING-001`, `GAP-JOB-SERVING-SMOKE-001`, `GAP-OPENWEBUI-SPACE-001`, `GAP-EXPOSED-CREDENTIALS-001` (rotar las 4 pegadas en el chat), `GAP-SEARCH-KEYS-001`. Cerrado: S0 (escáner activo).

## Próximo delta seguro
S2.4 + S2.5 (API y gateway con el broker), luego S3 (Dockerfile del Space con Open WebUI).
