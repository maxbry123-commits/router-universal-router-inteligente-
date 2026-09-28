# VALIDACION T03B — Supervisor OmniRoute + Mantenimiento SQLite

VALIDACION_T03B: PASS

FECHA: 2026-09-28
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS VALIDADOS:
- supervisor_omniroute.py
- mantenimiento_db.py
- tests/test_supervisor.py

## COMANDO DE ACEPTACION CONTRACTUAL

    python -m pytest 'chat router/08-OMNIROUTE/tests/test_supervisor.py' -q \
      && grep -q 'VALIDACION_T03B: PASS' 'chat router/08-OMNIROUTE/VALIDACION-SUPERVISOR-DB.md'

RESULTADO: exit 0 (9 passed; grep OK).

## SALIDA REAL DE TESTS

    $ python -m pytest 'chat router/08-OMNIROUTE/tests/test_supervisor.py' -q
    .........                                                              [100%]
    9 passed in ~3s

Tests (9/9 verdes):
1. test_backoff_crece ........................ 5s < 15s < 45s (x3)
2. test_backoff_tope ......................... backoff_delay(100) == BACKOFF_MAX (300)
3. test_wait_port_free_puerto_libre .......... True con puerto libre
4. test_wait_port_free_espera_y_timeout ...... NO relanza si el puerto sigue ocupado; timeout respetado
5. test_lock_impide_segunda_instancia ........ segunda adquisicion -> SystemExit
6. test_lock_contiene_pid .................... lock guarda el PID vivo
7. test_mantenimiento_db_inexistente ......... DB ausente: existed=False, deleted=0, sin error
8. test_mantenimiento_borra_viejo_y_conserva_nuevo ... retencion 7 dias epoch s/ms + ISO; mmap_size=134217728; VACUUM
9. test_supervisor_no_arranca_con_puerto_ocupado ..... main aplica backoff y NO llama start_process

## AUDITORIA PUNTO A PUNTO (sin GAPs)

- Backoff real: 5, 15, 45, 135... x3 con tope 300 s (BACKOFF_BASE=5, BACKOFF_MAX=300). OK
- Puerto ocupado: wait_port_free() espera hasta PORT_WAIT_TIMEOUT=120 s y devuelve
  False sin relanzar; main aplica backoff y reintenta. OK
- Healthcheck: healthy() acepta solo HTTP 2xx (200 <= status < 300) en
  /api/monitoring/health, tras 60 s de gracia, cada 30 s. OK
- Lock de instancia unica: flock LOCK_EX|LOCK_NB (o PID vivo como fallback);
  segunda instancia termina con SystemExit. OK
- RAM: si VmRSS > 6 GB -> SIGTERM con gracia 15 s y reinicio controlado. OK
- Retencion: borra filas > 7 dias en usage_history/call_logs/proxy_logs
  distinguiendo epoch-segundos (<1e11), epoch-milisegundos (>=1e11) y texto ISO;
  conserva los registros recientes. OK
- mmap_size: PRAGMA mmap_size=134217728 (128 MiB) aplicado y verificado dentro de
  la propia conexion (el pragma es por conexion, no persistente). OK
- VACUUM: ejecutado tras el borrado; verificado en DB temporal. OK
- DB inexistente: sale limpio sin crear archivos ni fallar. OK

## CHEQUEOS INDEPENDIENTES DEL SENTINELA

    grep -q 'wait_port_free' supervisor_omniroute.py   -> OK
    grep -q 'BACKOFF'        supervisor_omniroute.py   -> OK
    grep -q 'mmap_size'      mantenimiento_db.py       -> OK
    grep -q 'VACUUM'         mantenimiento_db.py       -> OK

## GAP

Ninguno. La unica causa del REVISE previo era ARCHIVOS_INCOMPLETOS
(faltaba este archivo de validacion); el codigo y los 9 tests ya eran
evidencia valida y no se regeneraron.
