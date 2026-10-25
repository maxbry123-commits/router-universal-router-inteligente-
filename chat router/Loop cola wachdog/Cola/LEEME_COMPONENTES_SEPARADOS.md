# Componentes independientes del NCT

Este archivo es un índice corto. La integración con el Router existente y los límites precisos están en el README principal de la entrega completa.

**Cola CIT-50:** `nct_addons/cola50/core.py` + `api.py`, con worker y base de datos propios. Requiere callback al modelo por `_chat_ficha` de tu proyecto para tareas `model`.

**Watchdog 48 horas:** `nct_addons/watchdog48/core.py` + `api.py`, con worker y base de datos propios. No ejecuta tareas, solo observa `heartbeat` o el estado de una cola si se configura callback.

**LOOP ECC — solo delta:** `nct_addons/loop_delta/real_actions.py` + `local_executor.py`. Es un adaptador con pruebas TDD RED/GREEN reales y recibos, no otro scheduler.

**Ricardo — solo delta:** `nct_addons/ricardo_delta/validation.py` + `adapter.py`. Reutiliza el `motor_cli.Motor` ya entregado sin copiarlo.

**Para montar todos en la API del Router**, usa el ZIP completo con `INSTALAR_EN_ROUTER.py`, `integracion/fastapi_app.py`, ENV y los tests. **No instalar junto al backend NCT anterior si sus rutas/contratos se solapan; comparar primero.**
