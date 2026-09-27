# T03-B — Supervisor + SQLite

ESTADO: PROTEGIDO / NO REGENERAR.

Archivos:
- supervisor_omniroute.py
- mantenimiento_db.py
- tests/test_supervisor.py

EVIDENCIA ACTUAL:
- 9 tests pasan.
- wait_port_free NO relanza si el puerto sigue ocupado.
- health acepta solo HTTP 2xx.
- backoff 5/15/45...
- lock impide doble instancia.
- timestamp epoch segundos reciente se conserva.
- mmap_size=128 MiB se aplica/verifica por conexión.
- retención + VACUUM probados en DB temporal.

REGLA:
Solo modificar este bloque si un test real de T03-B falla o evidencia upstream
demuestra incompatibilidad concreta. No regenerar por estética.
