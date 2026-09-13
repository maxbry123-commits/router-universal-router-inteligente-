# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0062 — BASE CERRADA
P01/P02/P03=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión core `RIU FAST-CLOSE` PASS.

## RIU-0063/0064 — CONNECTIVITY FABRIC
- raíz canónica `conectividad con Router inteligente universal/`.
- 19/19 repos con `PUENTE-RIU-<repo>.yaml` v2.
- frontend v2 integra GitHub + HF `COMAND-CENTER-1` + Jobs CPU/GPU + Space `yaiwes-ui-factory` + Claude GitHub MCP + memoria.
- runtime base y fabric probados.

## RIU-0065 — SUITE COMPLETA
Regresión final amplia: **75 passed, 2 warnings**. Connectivity runtime fresco: **7 passed**. Fail-closed sin secrets validado.

## RIU-0066 — PROBES + RUNNER CODESPACES
Runtime implementa probes GitHub identity/permisos, HF whoami/role y GitHub MCP initialize sin exponer secretos. Runner `integration/verify_runtime_connectivity.py` preparado para ejecución en entorno autorizado.

## RIU-0067 — HF OIDC / TRUSTED PUBLISHER
- Space `COMAND-CENTER-1/yaiwes-ui-factory` confirmado `static`.
- frontend OIDC publica correctamente al Hub.
- runs `34675165228` attempt 2 y `34677293995`: upload PASS.
- commits HF `57b5a04d371bad59bab6fa7e9db791fb982daec4` y `307549f879b6a3d40493b3bb82d285cb93f76047`.
- Hub read-back HTTP 200 PASS.
- URL directa `hf.space` 404 permanece como serving GAP separado, no fallo de autorización.

## RIU-0068 — BOOTSTRAP GLOBAL AUTH — NODO VIVO
Auditoría cruzada del 2026-09-13 confirma:
- Core del Router = **100% VERIFIED_CLOSED**.
- Integraciones/fabric/runtime existen; no se requiere refactor ni arquitectura nueva.
- `.github/workflows/riu-auth-presence-probe.yml` comprueba presencia, identidad HF/rol y acceso GitHub a 8 repos sin imprimir valores.
- `.github/workflows/riu-propagate-auth-secrets.yml` es fail-closed y no continúa sin `RIU_GITHUB_PAT`.
- evidencia previa del probe run `34677207175`: credenciales globales de Actions ausentes en ese momento.

### GAP REAL RESTANTE
No es código base: es **bootstrap y validación runtime de credenciales externas**.
1. `RIU_GITHUB_PAT` en Router Actions Secrets, con acceso a los 8 repos y capacidad para escribir Actions secrets.
2. `RIU_HF_TOKEN` role=`write` de `COMAND-CENTER-1`.
3. Dispatch `RIU Propagate Auth Secrets`.
4. Re-run `RIU Auth Capability Probe` y exigir identidad/permisos PASS.
5. Completar Codex account 1/2 device-auth persistence.
6. Completar Claude `setup-token` persistence.
7. Ejecutar E2E global GitHub + HF + MCP + memoria y cerrar solo con evidencia fresca.

## ESTADO
- Core/arquitectura/runtime: `VERIFIED_CLOSED` 100%.
- Capa externa de acceso global: `ACTIVE_BOOTSTRAP_GLOBAL_AUTH`.
- Nodo: `RIU-0068_BOOTSTRAP_GLOBAL_AUTH`.
- Regla: sin secreto runtime verificable y read-back real => PENDING, nunca PASS inventado.
