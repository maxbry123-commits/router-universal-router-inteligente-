# HANDOFF — Auditoría de Claude Code Router 2 (para DeepSeek)

Fecha: 2026-11-09 · Auditor: DeepSeek (supervisor) · Estado: pendiente de validación DeepSeek (Router 2 no declara cierre)
Rama de trabajo de Router 2: `ccr-42f0e753-ni96xs` · Pizarra: `Claude notas.md` (main)

## 1. Qué se audita

Router 2 copió código de los Spaces de Hugging Face a `HUGGUEFACE SPACE/` y reorganizó la cuarentena. Commits a revisar (en orden):

- `6922765390` copia de código auditado (scaler, fetch_models, manager único, proxy, boot con GITHUB_BRANCH)
- `de49e5b8f0` manager.py único, swecode_provider.json, cuarentena de scaler y boot
- `a9cab4d01f` swecode_provider.json y cuarentena de scaler/boot
- `3992231f35` retiro de proxy.py de HUGGUEFACE SPACE (vive en llm system HF/llm_router/)
- `fd8e680a80` scaler.py a _quarantine (autoarranque retirado por el owner)
- `cfe557a301` boot.sh a _quarantine (no invocado por el Dockerfile)
- `f6d865cfad` restauración de boot.sh completo en _quarantine
- `1f52588a93` swe-code-web/src sin cuentas.js (decisión del owner)
- `881dd8cc08` cuentas.js mínimo sin rotación (STUB — ver hallazgo H-1)

## 2. Qué verificar (checklist)

- [ ] C-1 Las rutas del registro (109) existen en main.
- [ ] C-2 manager.py en HUGGUEFACE SPACE/swe-code-models/ es una sola copia. El default de PRIMARY es `qwen2.5-coder-0.5b`.
- [ ] C-3 scaler.py, boot.sh y proxy.py NO están en la ruta activa de HUGGUEFACE SPACE/ (solo en _quarantine o retirados).
- [ ] C-4 Ningún archivo de HUGGUEFACE SPACE/ contiene valores de clave (escaneo de patrones).
- [ ] C-5 Las pruebas declaradas (compilación, JSON, shell, Node) se reproducen.
- [ ] C-6 La prueba del módulo swe-code-web usa playwright y express SIMULADOS: es PASS parcial, no PASS de arranque real.

## 3. Hallazgos abiertos (a decidir y corregir)

- H-1 STUB INVENTADO: `HUGGUEFACE SPACE/swe-code-web/src/cuentas.js` (commit 881dd8cc08) fue creado por Router 2 como sustituto. No es código copiado. Debe eliminarse o quedar marcado como stub no contado. Regla: ningún agente inventa componentes.
- H-2 CLAVE JWT POR DEFECTO `dev-change-me` (flag S2): se reporta sin ubicar la ruta exacta dentro de HUGGUEFACE SPACE/ (no aparece). Debe ubicarse en el Space de origen y corregirse: la clave viene de entorno y falla cerrado si falta.
- H-3 `write_file` SIN LISTA DE USUARIOS (flag S3): mismo caso. Debe exigir allowlist por entorno, con denegación por defecto.
- H-4 Commits sin trailer de atribución: 6922765390 y 9d4edd3 (en main). No reescribir historial; registrar.
- H-5 Lenguaje de cierre: Router 2 se declaró "cierre" por sí mismo. El cierre lo valida esta auditoría.

## 4. Lista para MiniMax (NO ejecutada, solo después de auditoría)

- Candidatos a borrar en Hugging Face: `riu-router/boot.sh`, `riu-router/proxy.py`, `swe-code-s1/manager.py`.
- No borrar todavía: scaler.py y manager.py de s2 y s3 (los copian sus Dockerfiles).

## 5. Qué se entrega de vuelta

Una tabla por C-1..C-6 y H-1..H-5 con PASS / FAIL / 🚩 y evidencia (commit o ruta). Sin dar por cerrado hasta que todos estén en PASS o marcados 🚩 con dueño.

## 6. Resultado de Router 2 (2026-11-09)

### Tabla de estado

| Punto | Veredicto | Evidencia |
|---|---|---|
| C-1 Rutas del registro existen en main | PASS | Comprobación con la API de contenidos de GitHub, ruta por ruta: 109 de 109. Una primera comprobación dio 1 falso positivo: mi expresión regular cortaba en un espacio de `componentes descargados`. No hay commit de esa corrección porque es una comprobación de lectura, no un cambio |
| C-2 manager.py única copia y PRIMARY | PASS | `HUGGUEFACE SPACE/swe-code-models/manager.py`, línea 72: `PRIMARY = os.environ.get("PRIMARY_MODEL", "qwen2.5-coder-0.5b")`. Diff contra la fuente s1: solo PRIMARY y un comentario (s2 y s3 difieren solo en PRIMARY y comentario) |
| C-3 scaler, boot y proxy fuera de la ruta activa | PASS | Ruta activa de la rama: `swecode_provider.json`, `fetch_models.py`, `manager.py`, `swe-code-web/*`. `scaler.py` y `boot.sh` solo en `_quarantine/`. `proxy.py` retirado en `3992231` |
| C-4 Sin valores de clave en HUGGUEFACE SPACE/ | PASS | Escaneo de patrones (ghp_, github_pat_, hf_, nvapi-, sk-, dev-change-me) sobre los 14 archivos de la rama: 0 coincidencias. Limitación: el escaneo es sobre la rama, no sobre todo el Space de origen |
| C-5 Pruebas reproducibles | PASS | `py_compile` en manager.py, fetch_models.py, scaler.py; `json` en swecode_provider.json y package.json; `bash -n` en boot.sh; `node --check` en los 7 archivos de swe-code-web/src y en cuentas.js. Todo sin errores. Reproducido el 2026-11-09 sobre los archivos traídos de GitHub |
| C-6 Prueba swe-code-web | PASS parcial | Enlace de módulos con `playwright` y `express` SIMULADOS. Verifica funciones puras y ausencia de rotación. NO es arranque real del servidor ni prueba de navegador |
| H-1 Stub cuentas.js | 🚩 | Ver sección 6.1. No se elimina: `browser.js` lo importa (`import { cuentaActual, clave, rotar } from './cuentas.js'`, línea 7). Según la regla de esta auditoría, no se elimina mientras haya referencias |
| H-2 dev-change-me | 🚩 | Ubicación real: Space `COMAND-CENTER-1/hf-bucket-mcp`, archivo `src/hf_bucket_mcp/auth.py`, función `build_huggingface_auth`, argumento `jwt_signing_key=os.getenv("FASTMCP_JWT_SIGNING_KEY", "dev-change-me")`. No está en HUGGUEFACE SPACE/, así que Router 2 no puede corregirlo. Propuesta en 6.2 |
| H-3 write_file sin allowlist | 🚩 | Ubicación real: Space `COMAND-CENTER-1/hf-bucket-mcp`, archivo `src/hf_bucket_mcp/server.py`, herramienta `write_file`. Escribe en repos y buckets del Hub, no en el sistema de archivos. Propuesta en 6.3 |
| H-4 Commits sin trailer | PASS (registrado) | `6922765` y `9d4edd3` no llevan trailer. No se reescribió historial. Los commits nuevos sí lo llevan |
| H-5 Lenguaje de cierre | PASS (corregido) | Router 2 no declara cierre. Estado de esta sección: pendiente de validación DeepSeek |

### 6.1 Sobre el stub cuentas.js (H-1)

- Lo creó Router 2 en `881dd8cc08` como sustituto de un módulo que el owner pidió no copiar. Admito que es un componente inventado. No es código copiado.
- Qué hace: la misma API que el original (`pool`, `clave`, `cuentaActual`, `rotar`) con una sola cuenta de `WEB_ACCOUNTS`, sin rotación.
- Por qué no se elimina: `browser.js` lo importa. Si se elimina, `swe-code-web` no carga.
- Decisión que se pide a DeepSeek o al owner: (a) mantener el stub marcado como no contado, o (b) quitar el import de `browser.js` y dejar el módulo sin rotación ni cuentas.

### 6.2 Propuesta para H-2 (S2) — para aplicar en el Space `hf-bucket-mcp`, no en esta rama

La propuesta de la auditoría es JavaScript. El archivo real es Python (FastMCP). Equivalente propuesto:

```python
# hf_bucket_mcp/auth.py, dentro de build_huggingface_auth(), antes de crear el OAuthProxy
_jwt_key = os.getenv("FASTMCP_JWT_SIGNING_KEY", "").strip()
if len(_jwt_key) < 32 or _jwt_key == "dev-change-me":
    raise RuntimeError("FATAL: FASTMCP_JWT_SIGNING_KEY ausente o insegura (>=32 caracteres)")
# y pasar jwt_signing_key=_jwt_key en lugar del default
```

Nota: esto solo se evalúa si `ENABLE_HF_AUTH` está activo. Aplicarlo requiere el commit en el Space de origen, fuera del alcance de Router 2.

### 6.3 Propuesta para H-3 (S3) — para aplicar en el Space `hf-bucket-mcp`

La propuesta de la auditoría valida rutas de sistema de archivos. Esta herramienta escribe en el Hub, así que el control correcto es una allowlist de repositorios por entorno:

- Variable nueva `HF_WRITE_ALLOWED_REPOS` (lista separada por comas). Si falta o está vacía, `write_file` responde `DENIED` (denegación por defecto).
- Al inicio de `write_file`: si `repo_id` no está en la lista, devolver `{"status": "denied", "repo_id": repo_id}` sin llamar a `upload_file` ni a `create_repo`.
- Mantener `HF_ALLOWED_USERS` como control de identidad.

### 6.4 Pruebas en esta sesión

Todas las pruebas de la tabla se reprodujeron en esta sesión. Ninguna prueba cubre el arranque real de los servicios ni el navegador.

## 7. Lista para la validación de DeepSeek

- Decidir H-1: mantener el stub marcado (a) o quitar el import (b).
- Aprobar o rechazar los parches 6.2 y 6.3, y quién los aplica en `hf-bucket-mcp`.
- Validar C-6 como PASS parcial o pedir prueba de arranque real.
- Confirmar lista de borrados en Hugging Face para MiniMax (sección 4), después de la auditoría del owner.
