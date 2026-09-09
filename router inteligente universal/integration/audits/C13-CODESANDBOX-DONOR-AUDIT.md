# C13 CodeSandbox dual — donor audit

Contrato: `tel.workflow/v3`  
Modo: `FAIL_CLOSED_LOOP`  
Nodo: `RIU-0029 / P02_WIRE_PRUNE_FILL`

## INPUT/GOAL literal aplicable
C13 debe respetar `REUSE > PATCH > ADAPT > GENERATE`, no crear un segundo core y conectar únicamente mediante Enchufe Universal. La arquitectura/Handoff define C13 como `CodeSandbox dual`, `MISSING`, `GENERATE/ADAPT; Docker + subprocess con paridad`.

## Donor local verificado
- Ruta: `router inteligente universal/Componente open soure router inteligente universal/docker-py/`
- Manifest: `pyproject.toml`
- Nombre de paquete: `docker`
- Descripción: Python library for Docker Engine API.
- Licencia declarada: `Apache-2.0`
- Upstream/Source: `https://github.com/docker/docker-py`
- El manifest usa versión dinámica (`hatch-vcs`); esta auditoría no inventa una versión.

## Capacidad demostrada vs contrato Router
`docker-py` demuestra capacidad de hablar con Docker Engine y es donor válido para el backend Docker. Esto NO define por sí mismo el contrato de seguridad/ejecución de C13 ni la paridad con subprocess.

No se recuperó evidencia Router-owned suficiente para definir exactamente:
1. allowlist de comandos/lenguajes/entrypoints;
2. imágenes Docker permitidas, digest/pinning y política de pull;
3. límites CPU/memoria/PIDs/disco y concurrencia;
4. política de red, DNS, puertos y egress;
5. filesystem read-only/tmpfs, mounts y workspace;
6. timeout, cancelación y kill/escalation semantics;
7. límites y formato stdout/stderr/artefactos;
8. variables de entorno, secretos y redacción de logs;
9. contrato de paridad Docker ↔ subprocess y condiciones de fallback;
10. schema de resultado/errores y boundary exacto con Enchufe Universal.

## Decisión
`ADAPT_CANDIDATE / AUDIT_ONLY`.

Se abre `GAP-C13-SANDBOX-CONTRACT-001`. Bajo `FAIL_CLOSED_LOOP` no se genera/adapta código productivo C13 hasta recuperar el contrato anterior. No se invoca el skill de descarga/extracción porque el donor requerido ya existe localmente y no se añadió ningún componente externo.

## Council12 / refutaciones / cross-check / CODA
Council12: PASS para auditoría fail-closed.  
Refutación 1: `docker-py` presente ≠ sandbox integrado.  
Refutación 2: Docker Engine API ≠ política de aislamiento/recursos del Router.  
Refutación 3: implementar un fallback subprocess sin contrato de paridad introduciría comportamiento no autorizado.  
Cross-check: Handoff + README arquitectura + STATE/CHECKPOINT/PLAN/RECOVERY coherentes con `AUDIT_ONLY`.  
CODA: `PASS_SAFE_AUDIT_DELTA`.  
`verify_final=PASS_C13_AUDIT_ONLY_CONTRACT_GAP_RECORDED`.
