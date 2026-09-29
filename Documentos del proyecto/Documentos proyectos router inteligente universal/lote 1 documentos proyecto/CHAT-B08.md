# CHAT-B08.md — TASK-08: CodeSandbox Dual (Docker + Subprocess)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-02 COMPLETED** (usa `SecretVault` para env_vars seguros). DAG_NODES: N18.

## 2. ⚠️ ESTA TASK LLEVA CONDICIÓN DEL ASK COUNCIL #7 (OBLIGATORIA, NO OPCIONAL)
Límites de recursos (`timeout_ms`, `max_memoria_mb`) deben respetarse en AMBOS backends (Docker y subprocess), con PARIDAD de contrato. No es aceptable que uno de los dos backends "confíe" en que el código se comporta bien.

## 3. OBJETIVO
Ejecutar código arbitrario (Python/Bash/YAML) inyectado desde la UI sin tocar el repo fuente en GitHub. Docker cuando esté disponible en el entorno de despliegue; fallback a subprocess con límites reales cuando no lo esté (el usuario confirmó: no hay VPS con Docker garantizado).

## 4. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-035 | `engine/sandbox/code_sandbox.py` | NEW | ~150 |
| R-036 | `engine/sandbox/docker_backend.py` | NEW | ~150 |
| R-037 | `engine/sandbox/subprocess_backend.py` | NEW | ~150 |

## 5. CONTRATOS
- `code_sandbox.py`: fachada única `CodeSandbox` que decide backend disponible al boot (detecta si Docker daemon responde) y expone SIEMPRE la misma interfaz:
  ```python
  async def spin_container(self, image_or_none, limits: SandboxLimits) -> SandboxHandle: ...
  async def inject_and_run(self, handle, script_content: str, env_vars: dict) -> ExecutionResult: ...
  async def teardown(self, handle) -> None: ...
  ```
- `docker_backend.py`: usa `docker` SDK. `limits` se traduce a `mem_limit`, `cpu_quota`, `network_disabled` según corresponda.
- `subprocess_backend.py`: usa `subprocess` + `resource` (RLIMIT_AS para memoria, `signal.alarm` o `asyncio.wait_for` para timeout). Sin Docker, el aislamiento de red/filesystem es más débil — debe documentarse explícitamente en docstring como limitación conocida, no ocultarla.
- `teardown()` DEBE ejecutarse en `finally` en ambos backends, incluso si `inject_and_run` lanza excepción.

## 6. CALIDAD Y SEGURIDAD
Igual que TASK-01 sección 7, más:
- Ningún script ejecutado puede acceder a variables de entorno del proceso padre salvo las explícitamente pasadas en `env_vars`.
- Timeout y memoria son OBLIGATORIOS en cada llamada — sin defaults infinitos.

## 7. TESTS OBLIGATORIOS
- `test_docker_backend_respeta_timeout`
- `test_docker_backend_respeta_memoria`
- `test_subprocess_backend_respeta_timeout`
- `test_subprocess_backend_respeta_memoria`
- `test_teardown_se_ejecuta_incluso_con_excepcion` (ambos backends)
- `test_fachada_selecciona_backend_disponible`

## 8. ACEPTACIÓN
3 archivos ≤500 LOC c/u. Los 6 tests en verde para AMBOS backends (paridad real, no solo en el que "funciona mejor").

## 9. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-08
  chat_b_id: CHAT-B08
  root_ids: [R-035, R-036, R-037]
  paridad_backends_verificada: true/false
  status: COMPLETED | BLOCKED
```

## 10. BLOCKER
Si no puedes verificar paridad real entre ambos backends (por ejemplo, entorno de test sin Docker disponible para probar ese backend), repórtalo explícitamente — no marques COMPLETED sin evidencia de los dos.

## 11. TRAZABILIDAD
DAG_NODES: N18 → TASK-08 → CHAT-B08 → R-035, R-036, R-037
