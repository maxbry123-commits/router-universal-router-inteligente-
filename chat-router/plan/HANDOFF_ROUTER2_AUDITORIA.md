# HANDOFF — Auditoría de Claude Code Router 2 (para DeepSeek)

Fecha: 2026-11-09 · Auditor: DeepSeek (supervisor) · Estado: pendiente de auditoría
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
