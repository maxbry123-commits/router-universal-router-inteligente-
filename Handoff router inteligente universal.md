# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP` / FAST-CLOSE / 99%.

## RIU-0053
P01 quedó `CLOSED_EXECUTABLE_SET`: M20 PASS real; M09 COMPLETED con exact model y SHA pero `content=null`/reasoning-only -> FLAG; M17/M18 job fue CANCELED tras exceder timeout corto -> FLAGS, sin otra ventana larga. M04/large/provider/RW external boundaries preservados.

## Plan único
1. P01 CLOSED_EXECUTABLE_SET.
2. P02 ACTIVE — inspeccionar y cerrar sólo C01-C23 que bloqueen `FastAPI→Auth/APIKeyGuard→Enchufe→RedUniversal→adapter→destination→verifier`.
3. P03 PENDING — API Key Manager hasta 100 slots + E2E real.

Cierre global = P03 E2E real + PASS ejecutable + FLAGS externos explícitos.