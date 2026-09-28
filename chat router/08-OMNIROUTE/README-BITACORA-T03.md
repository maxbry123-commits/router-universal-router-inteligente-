# T03 — OmniRoute · Bitácora forense, arquitectura, pruebas y recuperación

**Última auditoría:** 2026-09-28 · Rama: `main` · **Estado: PASS RUNTIME / BLOCKED_UPSTREAM para proveedores gratuitos anónimos probados**.

> **Regla de lectura:** compilación, servicio y respuesta de un proveedor externo son **tres gates distintos**. Nunca declarar «la API gratuita funciona» basándose únicamente en tests o `/health`. No borrar ni duplicar pruebas anteriores, no cambiar una instalación ya validada por una hipótesis, no afirmar cierre de la parte gratuita sin contenido generado.

## 0. Cómo retomar el trabajo sin repetirlo

**Fuente de verdad en este repo:**

- [Handoff general de espejos](../06-ESPEJOS/HANDOFF-ESPEJOS.md) — tablero/estado T03 y tareas conexas.
- [Informe contractual T03](../06-ESPEJOS/informes/T03.md) — acceptance, commits y logs relevantes.
- [README operativo](README.md) — arranque actual, variables, tests y endpoints.
- [Diagnóstico técnico](DIAGNOSTICO.md) — tabla de síntomas/causas y gates.
- [Diagnóstico de runtime/Node](DIAGNOSTICO-RUNTIME.md) — investigación histórica del camino `npm ci`/build; **no usar sus pasos antiguos de compilación como procedimiento vigente**.
- [Lanzador operativo](start_omniroute.sh), [wrapper x10 compatible](start_omniroute_x10.sh), [supervisor](supervisor_omniroute.py), [mantenimiento SQLite](mantenimiento_db.py).

**Rutas externas de evidencia:** [commits main](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commits/main), [Jobs HF](https://huggingface.co/jobs/COMAND-CENTER-1), [upstream OmniRoute](https://github.com/diegosouzapw/OmniRoute), [paquete npm](https://www.npmjs.com/package/omniroute).

**No reintentar sin motivo:** los antiguos builds con Turbopack, los builds limitados a heap V8 de 4096 MB, `npm install` de todas las dependencias, ni arrancar 10 instancias para probar las mismas claves.

## 1. Estado real verificado, por capa

| Capa | Evidencia | Resultado |
|---|---|---|
| Contrato local T03 | `9 passed` + `ACCEPTANCE=PASS` en Job `6aba04746b030d633f69bc1c` | **PASS** |
| Instalación | CLI oficial npm `omniroute@3.8.50`, sin compilar Next en HF; `better-sqlite3` comprobado con DB `:memory:` | **PASS** |
| Runtime | Job `6aba04746b030d633f69bc1c`: `PORT_20128=PASS`, `HEALTH_HTTP=200`, supervisor estable | **PASS** |
| Multiplicidad | 1 instancia activa; wrapper anterior x10 exporta `OMNIROUTE_INSTANCIAS=1` | **9 pausadas deliberadamente** |
| Enrutamiento | `auto/best-free` produjo pool de 13 candidatos e intentó 3 | **ROUTING alcanzado** |
| Generación gratis desde HF | `CHAT_HTTP=502`, OpenCode 403, Felo 400/429; directos DDG 418, UncloseAI 502, AI Horde 406 | **BLOCKED_UPSTREAM / NO PASS** |
| Router central | Job `6aba08fb6b030d633f69bc6c` visto `RUNNING`; su log contenía `GET /health 200` | **health del Router observado**; esto *no* acredita una respuesta LLM |
| T10 `auto/best-free` | Commit `03c7333223e9...` contiene trabajo aparte de selección gratuita | **No modificar T10 dentro de T03 sin auditar contrato propio** |

**Veredicto:** T03 está **cerrado para arranque/runtime** y **no cerrado para respuesta de API no-auth desde la salida de red de HF**. El último resultado no invalida los primeros.

## 2. Bitácora cronológica de acciones, en el orden en que ocurrieron

| Etapa | Commit / Job | Qué se hizo y qué se aprendió |
|---|---|---|
| Contrato y sentinela | Workflow run `36372627916`; commit `f6c37a1e4eef...` | Se registraron 7/7 archivos, aceptación exit 0 y 9 tests PASS. Esto **no** era una prueba de inferencia live. |
| Despliegue x10 | `aa96f9fef869...` → `61a0c9210cbf...` → `843035cf2d4a...` | Una compilación y diez puertos/instancias; se cableó Router ↔ OmniRoute. |
| Fallback npm inicial | `194e05082870...` | Al fallar `npm ci`, pasar a `npm install` disparaba más postinstalls y consumo. |
| Test remoto inicial | `ab4ea2d95650...`; run `36373298337` | Se diseñó prueba HTTP estado/modelos/chat; retornó error del endpoint HF, no resultado fiable del servicio en sí. |
| OOM x10 | HF `6ab9dc4052d0dbd7f1d9f760` | **ERROR: exit 137 OOMKilled**; el Router llegó a responder health antes de la muerte del Job. |
| OOM x1 | HF `6ab9f74152d0dbd7f1d9fe15` | **ERROR: exit 137 OOMKilled** con una sola instancia; por tanto la multiplicidad NO era causa suficiente. |
| Instrumentación fuente | HF `6ab9faad6b030d633f69ba97` | Fases observadas: instalación `npm`, `better-sqlite3` PASS, build Turbopack cercano a 16 GB; prueba **CANCELED**, no confundir con PASS. |
| Parche de reducción de memoria | `32b3ae829c05...`, `20d11f56e21e...`, `f59b1962a461...` | `--ignore-scripts`, arreglar lockfile, `build:backend`, Webpack/menos workers. Redujo uso del cgroup, pero no produjo servidor funcionando. |
| Prueba de ese fix | HF `6aba013252d0dbd7f1da005c` | **CANCELED** después de quedar cerca de 12/16 GB, sin `PORT_20128`; no asumir que compilar estaba finalizado. |
| Diagnóstico delimitado a 9 min | handoff `4002aa6988eb...`; HF `6aba03926b030d633f69bc01` | `npm ci` completó (2448 paquetes), `better-sqlite3=PASS`, empezó `Next.js 16.3.1 (webpack)`. El error verdadero fue `FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory` alrededor de 4057 MB de heap V8; cgroup ~12 GB/16 GB. Job terminó ERROR exit 2 por timeout del diagnóstico. |
| Solución que **sustituyó** el build | `ed38cff9a638...` | No insistir con `4096→6144` y recompilar en cada Job: usar el **paquete npm oficial precompilado `omniroute@3.8.50`**. La hipótesis de heap aumentado quedó **superada, no aplicada como solución final**. |
| Supervisor CLI y x9 pausadas | `726d1d5ed148...`, `da5af9b5c321...` | Supervisor inicia `omniroute serve`, mide RSS del árbol, aplica lock/health/backoff; wrapper deja una sola instancia. |
| Prueba real satisfactoria | HF `6aba04746b030d633f69bc1c` | **COMPLETED**: 9/9 tests PASS, puerto 20128 PASS, health 200, supervisor estable, `better-sqlite3` OK. En chat gratuito `502` externo. |
| Proveedores no-auth directos | HF `6aba06f36b030d633f69bc4c` | `HEALTH=PASS`, pero 6 modelos de DDG, UncloseAI y AI Horde retornaron 418, 502 o 406; **NO_WINNER**. Job ERROR exit 1 porque no hubo modelo que contestara. |
| Handoff/Router cableado | `ab89ed4c17c3...`, `b7ba32a8cbf0...`, `45cab4a5c13a...`, `a186d3d41922...` | Router central quedó configurado con launcher estable; workflow de prueba separa `OMNIROUTE_RUNTIME_VEREDICTO` de `OMNIROUTE_FREE_PROVIDER_VEREDICTO`; docs registran resultado separado. |
| Despliegue posterior | `c9f72cb8f254...`, `865debb01dde...`, `a2272da39001...` | Se ordenó relanzar Router central con OmniRoute estable; Job `6aba08fb6b030d633f69bc6c` observado RUNNING y health del Router central 200; no inferir chat OK. |

Los SHA cortos facilitan la lectura; para verificar se usan los enlaces de commits o las rutas de archivos de `main`. No inventar SHA o tests faltantes.

## 3. Diagnóstico causal: qué falló y qué NO

### A. x10 vs x1

Se pensó que diez procesos saturaban 16 GB. **El experimento x1 también murió con exit 137**, así que bajar a uno **no resolvía por sí solo** el build. Mantener uno reduce carga del runtime pero no es la corrección primaria del arranque.

### B. Lockfile y `npm install` vs `npm ci`

La rama fuente v3.8.50 tenía una incidencia de lockfile/workspace: el `npm ci` inicial fallaba; pasar indiscriminadamente a `npm install` introducía postinstalls/descargas de Playwright, ONNX y otros paquetes innecesarios para el gateway. Se probó una estrategia `--ignore-scripts`, y quedó validado que `better-sqlite3` podía reconstruirse **selectivamente**, pero instalar y compilar la fuente seguía costando memoria.

### C. Turbopack/Next/SWC

La instrumentación desde fuente observó la memoria cercana al límite del Job. Cambiar a Webpack + `build:backend` eliminó parte de la presión, pero hizo visible otro cuello: el **heap V8 de 4096 MB**. El log confirmó `Allocation failed - JavaScript heap out of memory`, incluso con cgroup por debajo de 16 GB. Un stack de `@next/swc` por sí solo NO demuestra una incompatibilidad de SWC: la primera línea fatal demuestra **límite de heap**. No aplicar `OMNIROUTE_BETTER_SQLITE3_STUB=1` a artefactos productivos: el propio upstream advierte que puede dejar la DB inutilizable.

### D. Solución validada: separar construcción y arranque

El paquete publicado en npm **ya incluye servidor compilado**. Se instala con:

```bash
OMNIROUTE_SKIP_POSTINSTALL=1 npm install -g omniroute@3.8.50 \
  --omit=optional --ignore-scripts --no-audit --no-fund
```

El launcher instala `better-sqlite3@^13.0.2` separadamente en `~/.omniroute/runtime/`, abre una DB `:memory:` como prueba y aborta si no es válido. Para runtime se fija Node 24, `127.0.0.1:20128`, `REQUIRE_API_KEY=false` **solo porque escucha localmente**, `DATA_DIR` configurable y clave de cifrado **persistente/no publicada en git**. `supervisor_omniroute.py` gestiona espera de puerto, lock, backoff, health y límite RSS de 6 GB. `mantenimiento_db.py` hace retención y mantenimiento.

### E. Fallo de free-tier upstream (no es un error de arranque)

El Job exitoso dio `CHAT_HTTP=502`, pero los headers probaron enrutamiento real: `x-omniroute-combo-pool-size: 13`, `x-omniroute-combo-attempted: 3`. El proveedor OpenCode respondió `403` por restricción del cliente admitido, Felo `400/429`; pruebas directas desde la red de HF: DuckDuckGo `418 ERR_BN_LIMIT`, UncloseAI `502`, AI Horde `406 model_not_supported`. **No son API keys ni logs de Docker faltantes; son respuestas de los servicios/modelos externos probados**.

En la comunidad el mantenedor distingue el OpenCode-Free `403` como una restricción del contrato de cliente y hay arreglos de routing en `release/v3.8.51`; eso **no** acredita que el paquete publicado 3.8.50 lo incluya ni autoriza suplantar/evadir la protección. Para respuestas estables, conectar proveedores permitidos con acceso oficial (incluidas cuotas gratuitas con credenciales legítimas cuando existan), comprobar catálogo y probar un modelo explícito. No relanzar bucles de tráfico contra servicios que rechazan solicitudes.

## 4. Evidencias mínimas reproducibles

### Gate local, sin consumo remoto

```bash
python -m pytest 'chat router/08-OMNIROUTE' -q
bash -n 'chat router/08-OMNIROUTE/start_omniroute.sh'
bash -n 'chat router/08-OMNIROUTE/start_omniroute_x10.sh'
```

### Runtime (dentro del mismo Job que ejecuta OmniRoute, NO en tu móvil)

```bash
curl -isS --max-time 10 http://127.0.0.1:20128/api/monitoring/health
curl -isS --max-time 15 http://127.0.0.1:20128/v1/models
```

### Inferencia real: gate independiente de disponibilidad externa

```bash
curl -isS --max-time 90 http://127.0.0.1:20128/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"auto/best-free","messages":[{"role":"user","content":"Responde exactamente OMNI_OK"}],"max_tokens":32}'
```

**PASS chat** exige HTTP 200 **y contenido del asistente no vacío**; HTTP 200 vacío, HTTP 502, encabezado de pool o `/models 200` NO lo cumplen. Probar con proveedores habilitados oficialmente y sin saturar su cuota.

### Revisión segura

```bash
tail -n 120 /tmp/omniroute.log
ps -eo pid,ppid,rss,args | grep -E '[o]mniroute|[s]upervisor_omniroute'
```

**Seguridad:** nunca pegar keys, `STORAGE_ENCRYPTION_KEY`, cookies, headers de autorización ni `DATA_DIR` privado completos en el README o los logs compartidos. Evitar trabajos nuevos cuando ya existe evidencia concluyente. No usar sistemas de evasión de límites del proveedor.

## 5. Fuentes consultadas y decisiones derivadas

**Código/documentación upstream**
- [Tag v3.8.50 y fuentes](https://github.com/diegosouzapw/OmniRoute/tree/v3.8.50).
- [Dockerfile y gestión de Next](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/Dockerfile).
- [Guía Docker de la rama próxima](https://github.com/diegosouzapw/OmniRoute/blob/release/v3.8.51/docs/guides/DOCKER_GUIDE.md).
- [Config sobre stub SQLite — no usar en runtime](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/scripts/build/better-sqlite3-stub-flag.mjs).
- [Catálogo de cuotas free y contratos](https://github.com/diegosouzapw/OmniRoute/blob/release/v3.8.51/docs/reference/FREE_TIERS.md).
- [Troubleshooting de providers gratuitos](https://github.com/diegosouzapw/OmniRoute/blob/release/v3.8.51/docs/guides/TROUBLESHOOTING.md).

**Reportes concretos de la comunidad**
- [Issue OpenCode 403 en OmniRoute 3.8.50 #13935](https://github.com/diegosouzapw/OmniRoute/issues/13935).
- [Discusión OpenCode restrictivo #13986](https://github.com/diegosouzapw/OmniRoute/discussions/13986).
- [Discusión problemas de proveedores auto / DDG 418 / UncloseAI #14327](https://github.com/diegosouzapw/OmniRoute/discussions/14327).
- [Issue free-tier y cuota OpenCode #8655](https://github.com/diegosouzapw/OmniRoute/issues/8655).
- [Issue de app/contrato OpenCode #13121](https://github.com/diegosouzapw/OmniRoute/issues/13121).
- [Issue subsets OpenCode Free #14405](https://github.com/diegosouzapw/OmniRoute/issues/14405).
- [Comunidad Next/Turbopack memoria #95744](https://github.com/vercel/next.js/issues/95744).
- [Problemas de lockfile npm CI #8726](https://github.com/npm/cli/issues/8726).
- [Issue lockfile/workspaces OmniRoute #11747](https://github.com/diegosouzapw/OmniRoute/issues/11747).

**Precisión:** estas fuentes explican fallos reproducidos en la comunidad. En nuestro entorno las *causas confirmadas* se asignan únicamente cuando un Job propio enseñó el síntoma exacto. Las ramas futuras upstream no sustituyen una versión validada por sí solas.

## 5 bis. Investigación posterior al PASS: estado específico de T10 y otros free-tier

**Hallazgo reproducible de repositorio (2026-09-28):** existe el [contrato T10](../06-ESPEJOS/tareas/T10.md) en `chat router/06-ESPEJOS/tareas/T10.md`, commit `03c7333223e9...`, pero al auditar `main` **no existe** el directorio esperado `chat router/08-OMNIROUTE/autofree/` ni sus ficheros prometidos `aplicar_parche_autofree.sh`, `parche_virtualFactory.py`, `prueba_autofree.py` o `tests/test_parche.py`. Por tanto, **T10 NO puede declararse implementada ni probarse con el gate de ese contrato**.

**Conflicto de arquitectura:** T10 fue diseñada como parche TypeScript del fichero de fuente `open-sse/services/autoCombo/virtualFactory.ts` **entre `npm ci` y `npm run build`**. El arranque estable de T03 usa `npm install -g omniroute@3.8.50` precompilado y evita por completo esa fase; no basta con crear el archivo T10 para que altere el comportamiento del servidor precompilado. **No volver al build roto para integrar T10 sin rediseñar, investigar el bundle y probar su aceptación de forma aislada.**

**Más evidencia upstream (NO verificada en el egress HF en esta investigación):**

- [OmniRoute #13935](https://github.com/diegosouzapw/OmniRoute/issues/13935) y [discusión #13986](https://github.com/diegosouzapw/OmniRoute/discussions/13986): OpenCode Free devuelve 403 cuando el cliente no cumple su contrato; la rama de desarrollo menciona cambios, pero el paquete 3.8.50 no queda reparado por eso.
- [OmniRoute #14327](https://github.com/diegosouzapw/OmniRoute/discussions/14327): comunidad también reporta bloqueo DDG 418 y catálogos UncloseAI caducos. No insistir con una IP rechazada ni intentar eludir sus controles.
- [OmniRoute #4265](https://github.com/diegosouzapw/OmniRoute/issues/4265): Pollinations requiere claves para modelos premium, aunque algunos modelos básicos fueron catalogados como keyless; [#9827](https://github.com/diegosouzapw/OmniRoute/issues/9827) documenta que incluso conexiones anónimas pueden dar 401. Por ello **Pollinations no se marcará compatible con HF hasta obtener HTTP 200 y texto real**.
- [Guía de free tiers](https://github.com/diegosouzapw/OmniRoute/blob/release/v3.8.51/docs/getting-started/FREE-TIERS-GUIDE.md): `noAuth` / `hasFree` son **metadatos** de descubrimiento y no implican acceso garantizado. Un proveedor con cuotas gratuitas puede requerir autenticación legítima.

**Regla para siguiente cambio:** T03 no necesita tocar código de instalación. Si se decide ejecutar T10, primero crear un plan distinto compatible con el paquete precompilado o con build en una fase externa claramente separada del runtime; validar autorización y disponibilidad de cada proveedor antes de incluirlo en auto-ruteo, sin suplantar clientes ni evadir cuotas.

## 6. Contrato de continuación: bucle en microtareas con gates

`LEER HANDOFF + README → IDENTIFICAR ÚNICO FALLO PENDIENTE → INVESTIGAR fuente/log upstream → ANOTAR HIPÓTESIS Y PRUEBA → CAMBIO QUIRÚRGICO SOLO SI HACE FALTA → GATE LOCAL → GATE RUNTIME → GATE CHAT → READ-BACK + INFORME → SIGUIENTE MICROTAREA`

1. **No ejecutar otro build de fuente de T03**. El runtime ya tiene evidencia PASS, salvo si un nuevo SHA cambia directamente el lanzador/supervisor.
2. **Próximo objetivo separado:** una **respuesta real** de un proveedor legítimamente disponible. Primero revisar si hay alguna conexión gratuita *oficialmente autorizada* y activa en el Router actual (sin copiar claves al chat), su modelo vigente y su cuota. El proveedor que devolvió 403/418/429 no se vuelve a sondear compulsivamente.
3. Si no hay proveedores activos: `FREE_PROVIDER=BLOCKED_EXTERNAL`; no transformar esto en `T03_RUNTIME_FAIL`. Informar dependencia (cuenta/clave legítima o disponibilidad del upstream), no inventar workaround.
4. Si hay uno disponible: probar **un modelo explícito** con timeout y presupuesto; después `auto/best-free` y fallback. Grabar HTTP, modelo, contenido/no contenido, fecha, Job y SHA, **sin secretos**.
5. Si falla: buscar **primera línea causal**, analizar cambios y repetir **solo la microtarea**, nunca la cadena completa. Límite histórico pedido por el Director: **un bloque de cómputo como máximo 10 min**, luego informe; no dejar Jobs de diagnóstico activos sin una causa operativa justificada.
6. Sentinel: no marcar `PROVEEDORES=PASS` sin contenido real. En la tabla T03 mantener `RUNTIME=PASS`, `FREE_NOAUTH_HF=BLOCKED_UPSTREAM` hasta prueba que demuestre lo contrario.

## 7. Ficha de recuperación para otro agente

```text
PROYECTO          = Router Universal, tarea T03
RAM JOB           = HF cpu-basic 16 GB (histórico)
MAIN              = maxbry123-commits/router-universal-router-inteligente-
SOURCE            = chat router/08-OMNIROUTE/start_omniroute.sh
WRAPPER           = chat router/08-OMNIROUTE/start_omniroute_x10.sh
SUPERVISOR        = chat router/08-OMNIROUTE/supervisor_omniroute.py
DB                = chat router/08-OMNIROUTE/mantenimiento_db.py
HANDOFF           = chat router/06-ESPEJOS/HANDOFF-ESPEJOS.md
INFORME           = chat router/06-ESPEJOS/informes/T03.md
JOB_BUILD_HEAP    = 6aba03926b030d633f69bc01 (falló)
JOB_RUNTIME_PASS  = 6aba04746b030d633f69bc1c
JOB_NOAUTH_FAIL   = 6aba06f36b030d633f69bc4c
JOB_ROUTER_CENTRAL= 6aba08fb6b030d633f69bc6c (RUNNING al auditar)
VEREDICTO_RUNTIME = PASS
VEREDICTO_CHAT_NOAUTH_HF = BLOCKED_UPSTREAM
NO REPETIR        = npm install completo; build Next en Job; x10 simultáneo
GATE RESTANTE     = proveedor autorizado capaz de contestar HTTP 200 + contenido
```