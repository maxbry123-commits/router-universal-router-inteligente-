# WATCHDOG CHECKLIST RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-05 03:10 EST
Commit router: ac4e20bc63a9f85b85f1ef423e1316ecd7080aaf (previo a0eb06c2)
Rama: reorganizacion

## Estado Ixx
- I01 Checkpoint/reinicio MVP: BLOQUEADO (HF space stage=PAUSED; health unreachable, 503/Preparing Space)
- I02 5 agentes cableados + harness DeepSeek: GAPS (sin cambios; no re-testable por space paused)
- I03 SWE CODE free / SWEN CODE autónomo: BLOQUEADO (space paused; modelos no re-testables)
- I04 Modelos selectores: BLOQUEADO (no re-testable; space paused)
- I05 System prompt MVP: VALIDACION (sin re-test)
- I06 Acceso HF + GitHub: BLOQUEADO (HF health/MCP fail por pause; github_leer no re-testable)
- I07 Frontend selectores: CERRADO (UI Vercel 200 OK https://riu-jev-bridge.vercel.app)
- I08 Yaiwes + OpenClaw UI: PENDIENTE (UI responde 200 pero backend paused)
- I09 HTTP + MCP: BLOQUEADO (space paused, /health /mcp /chat/send unreachable)
- I10 Tarea 1: PENDIENTE
- I11 Tarea 2: PENDIENTE
- I12 Watchdog: CERRADO (ciclo ejecutado; checklist actualizada; gap reportado)

## Tests ciclo
1. Health: FAIL (space paused, Preparing Space / stage PAUSED)
2. MCP initialize + tools/list: FAIL (space paused)
3. /chat/send (cualquier modelo): FAIL (space paused)
4. MCP github_leer: FAIL (space paused)
5. UI Vercel: 200 OK

Siguiente: Reiniciar space HF COMAND-CENTER-1/riu-router (maintainer, runtime stage PAUSED) luego re-ciclo health+MCP+3 tests. Prioridad I01/I09 desbloqueo.
