# T03-A — Runtime / instalación OmniRoute v3.8.50

OBJETIVO: resolver SOLO runtime e instalación contra evidencia upstream exacta.

NO TOCAR supervisor_omniroute.py ni mantenimiento_db.py salvo que T03-B falle.

EVIDENCIA YA VERIFICADA:
- tag v3.8.50 existe y package.json declara:
  engines.node = ">=22.22.2 <23 || >=24.0.0 <27"
- Node 24 NO es el único runtime permitido en v3.8.50.
- issue #9576 mantiene abierta compatibilidad nightly Node 24/26.
- issue #9613 documenta better-sqlite3 ausente con npm >=11; solución upstream:
  npm 10 o approve-scripts explícito antes de instalar.
- release v3.8.50 es la release publicada actual.

TRABAJO:
1. Verificar package.json + package-lock DEL TAG v3.8.50.
2. Elegir runtime seguro para Job Linux 16 GB:
   - Node 22.22.2+<23, o
   - Node 24.x
   justificando la decisión con upstream.
3. Verificar versión exacta de better-sqlite3 del lockfile.
4. Corregir start_omniroute.sh para que la instalación de better-sqlite3 sea
   reproducible y no dependa de un rebuild que pudo haber sido bloqueado.
5. Confirmar comando server-only real, health endpoint y variables runtime.
6. bash -n start_omniroute.sh.

SALIDA:
- Cambios mínimos en start_omniroute.sh si son necesarios.
- Evidencia en DIAGNOSTICO.md.
- No declarar PASS global; T03-C decide el cierre.
