# T03A — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute contrato A: runtime e instalación reproducible
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- start_omniroute.sh
- DIAGNOSTICO-RUNTIME.md

ACEPTACIÓN: bash -n 'chat router/08-OMNIROUTE/start_omniroute.sh' && grep -q 'NODE_VERSION_DECISION' 'chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md' && grep -q 'BETTER_SQLITE3_INSTALL' 'chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md') -ge 2

EVIDENCIA ACTUAL:
- causa: ARCHIVOS_INCOMPLETOS
- faltan: ['DIAGNOSTICO-RUNTIME.md']
- pytest/acceptance exit: 2
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q 'v3.8.50' 'chat router/08-OMNIROUTE/start_omniroute.sh'
- grep -q 'better-sqlite3' 'chat router/08-OMNIROUTE/start_omniroute.sh'

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: diegosouzapw/OmniRoute https://github.com/diegosouzapw/OmniRoute
- Repositorio oficial/upstream: WiseLibs/better-sqlite3 https://github.com/WiseLibs/better-sqlite3
- StackOverflow: No such file or directory message https://stackoverflow.com/questions/57912862/no-such-file-or-directory-message
- StackOverflow: Slim php, No such file or directory https://stackoverflow.com/questions/76778050/slim-php-no-such-file-or-directory
- StackOverflow: Why am I getting &quot;ENOENT: no such file or directory, open&quot; when trying to save an image through multer&#39;s storage? https://stackoverflow.com/questions/63302086/why-am-i-getting-enoent-no-such-file-or-directory-open-when-trying-to-save-a
- StackOverflow: &quot;No such file or directory&quot; protoc https://stackoverflow.com/questions/74929244/no-such-file-or-directory-protoc
- StackOverflow: Errno 2 No such file or directory error while importing a python script from a sub-folder https://stackoverflow.com/questions/61756691/errno-2-no-such-file-or-directory-error-while-importing-a-python-script-from-a-s

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: El archivo `chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md` nunca fue creado en el intento 1; el verificador (grep/pytest) falla con ENOENT al buscarlo. Además la ruta contiene espacio ("chat router"), riesgo de word-splitting si el grep no está entrecomillado.

EVIDENCIA: `grep: chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md: No such file or directory`; pytest_exit=2 (error de colección/archivo faltante, no fallo de tests); faltan=['DIAGNOSTICO-RUNTIME.md'].

GAPS: (1) No existe diagnóstico documentado del runtime de OmniRoute (Node version, better-sqlite3 build nativo, variables de entorno, pasos de instalación reproducible). (2) Protocolo no valida existencia de entregables antes de invocar pytest. (3) Desconocido si better-sqlite3 requiere prebuilds o compilación (node-gyp) en el entorno destino.

NO_REGENERAR: No tocar código fuente de OmniRoute ni tests existentes que sí pasan; no modificar otros archivos del contrato A ya presentes; no renombrar la carpeta "chat router".

REPARAR: Crear `chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md` con: versiones fijadas (Node LTS, npm), `npm ci` con lockfile, nota de better-sqlite3 (prebuilds vs node-gyp, python3/make/g++ si compila), variables de entorno requeridas, comando de arranque, verificación de salud (endpoint/CLI), y tabla de errores comunes (ENOENT, ABI mismatch). Entrecomillar rutas en scripts: `grep ... "chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md"`.

ACEPTACION: `test -f "chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md"` exit 0; grep del verificador sin error; pytest_exit=0; documento contiene secciones runtime, instalación reproducible y troubleshooting.
