# 19. LANZADOR DE JOBS (R1, R5, R6)

Todo Job se lanza con `ops/launch.sh`. El lanzador:

- clona la rama que audita (`--branch $GH_BRANCH`) y hace `sparse-checkout` de `ops/ kernel/ connections/`;
- es idempotente: si ya está dentro de un clon con `ops/`, no vuelve a clonar (un clon por job);
- autentica con cabecera de entorno `GIT_CONFIG_*` + `extraheader`, nunca con token en la URL, en `argv` ni en los logs;
- ejecuta `python ops/<script>.py` (nunca `exec(open(...))`);
- propaga `RUN_ID` como clave de idempotencia: el mismo `RUN_ID` reescribe el mismo `result.json` en el Dataset.

Todo Job de Hugging Face debe llevar `--timeout`. El techo real observado de la plataforma es de 1800 s por Job: los Jobs que superan ese límite mueren con `Job timeout` y pierden su resultado. Por eso los Jobs pesados (historia, grafo) no clonan el historial completo, sino una ventana (`--shallow-since`) y sin blobs (`--filter=blob:none`).

# 20. FUENTES DE FALLO Y RUTAS DE RESOLUCIÓN

Orden de búsqueda cuando un nodo falla (FAIL_CLOSED, sin parar el bucle):

1. `existing_code` — leer el código que ya existe en el repo antes de escribir nada.
2. `repo_docs` — documentación del propio repo (`kernel/`, `connections/`, `AGENTS.md`).
3. `commit_history` — qué cambió y cuándo (`git log --name-status -M`).
4. `official_docs` — documentación oficial de la herramienta usada.
5. `closed_issues` — issues ya resueltos del upstream.
6. `stackoverflow` — soluciones ya resueltas por la comunidad.
7. `hf_forum` — foro de Hugging Face.
8. `smaller_scope` — reducir el alcance del nodo y volver a intentarlo.
9. `alt_library` — alternativa de librería.
10. `alt_architecture` — arquitectura alternativa.

Cuando se agotan las diez rutas: `FLAG_AND_CONTINUE_INDEPENDENT`. Se registra el flag `🚩` en `kernel/KERNEL.yaml → handoff.flags` y se continúa con los nodos independientes que no dependan del que falló. Nunca se declara PASS un nodo cuyo `result.json` no sea PASS, y nunca se afirma una conexión rota sin evidencia.

# 21. RECOMENDACIONES

- **U1 — catálogo único de patrones.** `ops/patterns.py` es el catálogo canónico de seis categorías (`http`, `mcp`, `endpoints`, `agents`, `engines`, `imports`). El catálogo de cinco de `connectivity_job.py` se mapea así: `network → http`, `environment → endpoints`. `ops/j11_patterns.py` aplica el catálogo y `ops/test_patterns.py` lo verifica. Los catálogos inline heredados (`ops/historical_wiring_audit.py`) se declaran como divergencia conocida y no se reescriben: son artefactos congelados de la guía anterior.
- **Registro antes que active.** Toda conexión nace en `pending_audit`. Solo pasa a `active` con `evidence` registrada en `connections/healthchecks.yaml` y comprobada por `wiring_check`.
- **Presupuesto antes que historial.** `j3_history` usa `--shallow-since` + `--filter=blob:none`. El análisis histórico completo del repo (7,9 GB, 374.174 rutas) no cabe en el techo de 1800 s por Job.
- **Preflight con dimensionamiento real.** `j0_preflight` mide el disco disponible (`disk_free_gb`) y aborta si no llega al mínimo; en el contenedor de Hugging Face se midieron 671,8 GB.
- **El registro es lo que se audita, no el README.** `connections/{registry,topology,endpoints,healthchecks}.yaml` es la fuente de verdad del cableado; `AGENTS.md` sólo define las reglas.

# 22. REGISTRO DE DESVIACIONES

| # | Desviación | Motivo | Alcance |
|---|---|---|---|
| D-01 | `ops/kernel.py` completado hasta `validate/next/apply` | El bloque 3/3 venía truncado a mitad de `validate()` | La interfaz la fija `kernel_rules` (validate \| next \| apply) |
| D-02 | `ops/launch.sh` creado | R1, R5 y R6 lo exigían y no venía en la guía | Un clon por job, `--branch`, `--timeout` en el comando |
| D-03 | `entrypoints` y `domains` de `KERNEL.yaml` rellenados con rutas reales | La guía los deja como `FILL` | `chat-router/chat/frontend/shell.html`, `dsla/dsla.py` y 12 dominios reales |
| D-04 | `connections/registry.yaml` con el esquema de `wiring_check` (`from/to/via/provides/requires`) | El esquema de §5 (`name/source/target`) y el de `wiring_check` no coinciden | Precedencia del kernel: `kernel > registry > DSL DAG > cualquier nota`; `wiring_check` es la puerta |
| D-05 | `ops/j11_patterns.py` + `ops/test_patterns.py` | R10 exigía "own job + test" y la guía no traía el fichero | El catálogo heredado no se reescribe |
| D-06 | `ops/j7_mirror.py` excluye el código de terceros vendorizado (315.949 ficheros) | El Space no acepta el repo completo (374.205 ficheros / 10,42 GB) | El mirror es first-party (21.037 ficheros / 0,47 GB); el 84 % del repo permanece en el repo |
| D-07 | `kernel/DAG.yaml` con `progress_pct` medido sobre el DAG | La guía lo deja `FILL` | 15 nodos S0–S12, `parallel.max=3`, 10 rutas de fallo |
| D-08 | `j2_graph` evalúa sintaxis solo del código propio | Con el check literal, 61 errores de terceros tumban el job (39 vendorizados, 16 en `otros/descartados`, 1 truncado) | Los de terceros se(info) en `vendored_syntax_errors_reported`; no bloquean |
| D-09 | `_quarantine/**` dentro de `protected` | La cuarentena es parte del plan, no un hueco | `kernel/KERNEL.yaml → protected` |
| D-10 | `kernel/INPUT_BLOCK.yaml`: valor de `R9` entrecomillado | El texto literal de la guía produce YAML inválido (`{` sin comillas) → `ParserError` | Semántica idéntica; habilita el chequeo 1-a-1 programático |
| D-11 | `ops/launch.sh` instala también `pyyaml` y acepta `PYTHON` | 3 scripts importan `yaml` y la guía solo instalaba `huggingface_hub` | Sin esto `j2/j5/j6` mueren en el contenedor con `ModuleNotFoundError` |
| D-12 | Tokens solo por entorno heredado, nunca en argv | R2 e `improved_over_minimax` exigen "nunca en URL/argv/logs" | Lanzador con env heredada; 0 coincidencias de token en los logs |
| D-13 | `common.clone()` idempotente (reutiliza el repo si ya existe) | El job muere con rc=128 cuando el destino ya existe y no está vacío | Rutas §20: 1 `existing_code` + 8 `smaller_scope`; mantiene 1 clon por job (R5) |
| D-14 | `launch.sh` puede crear un clon sparse además del clon del job | La guía no define el reparto de clones | Solo cuando el script no está en el CWD; el clon sparse es mínimo (`ops/ kernel/ connections/`) |
| D-15 | `j4_plan` hace **un** barrido del repo con `git grep -f` en vez de hasta 3000 barridos completos | Medido: 74 s por barrido sobre 374.205 ficheros / 16 GB → 3000 barridos = 61 h (inviable) | Misma semántica de `no_text_ref` (referencias fuera del propio fichero); §20 rutas 8 `smaller_scope` + 1 `existing_code` |
| D-17 | `ops/hf_job.py` crea todo Job de HF con `flavor=cpu-upgrade` (32 GB RAM + 8 vCPU) | La API de HF no acepta `resources`/`hardware`: el campo es `flavor`; los jobs previos corrían en `cpu-basic` (16 GB) | `flavor` por defecto `cpu-upgrade`; override con `HF_FLAVOR` |
| D-18 | `wiring_check` evalua la sintaxis solo del codigo propio (misma regla que D-08) y usa `connections/baseline_unresolved.json` | Con el check literal, 61 errores de terceros hacian FAIL a `j7_mirror`; el baseline vivia solo en el Dataset | `no_syntax_errors` (propios) + `third_party_syntax_reported` (informativo); baseline commitado en `connections/` |
| D-19 | El baseline de `j7_mirror` usa `os.scandir` (stat cacheado) en vez de `os.walk`+`getsize` | Medido: 12+ min solo en recorrer 374.205 ficheros (un `stat` por fichero) | Mismo resultado, un solo recorrido del directorio |
| D-20 | El modo baseline de `j7_mirror` usa la env `MIRROR_BASELINE=1` (no `BASELINE`) | `wiring_check` usa `BASELINE` como env de la RUTA del baseline: mi flag de modo lo pisaba y `baseline_exists` fallaba | Evita la colision de nombres de env |
| D-21 | `ops/hf_job.py` usa la imagen `python:3.12` (con git y curl) en vez de `python:3.12-slim` | `python:3.12-slim` no trae git ni curl: los jobs no clonaban ni publicaban y el API los reportaba `COMPLETED` | Misma imagen que los jobs que si funcionaron (j0, j11) |
| D-22 | `ops/hf_job.py` envia el comando en el campo `command` (array) y no en `environment.CMD` | Con `CMD` el contenedor arranco sin ejecutar nada y la API reporto `COMPLETED`: 6 jobs "pasados" que no hicieron nada | Verificado contra el unico job que funciono (j0: `command`=["bash","-lc",...]) |
| D-16 | `j7_mirror` acepta `BASELINE=1` (baseline read-only, sin subir al Space) | El DAG en `S4_approval.if_missing` exige "j7 on main as read-only baseline, mirror skipped" y el script no tenía ese modo | Calcula ficheros/tamaño y estado del Space sin desplegar; el mirror real queda para `j9_remirror` (aprobación `deploy`) |
| D-23 | `ops/j9_remirror.py` y `ops/j10_final_audit.py` implementados por nosotros | La guía DECLARA los dos jobs en el mapa `jobs` y en `S12_final` pero NO incluye su código (X-Ray 2026-11-05) | Patrón idéntico a `j7_mirror`/`j8_audit` (mismos helpers y gates); gates implementados: `Space==new HEAD` y `audit PASS` |
| D-24 | `j5_apply` comprueba el gate `entrypoints_exist` declarado en `S5_j5` | El código de la guía para `j5_apply` no implementaba ese gate (X-Ray 2026-11-05) | El gate se evalúa contra el árbol de la rama; en la ejecución en curso se verificó a posteriori sobre la rama publicada |
| D-25 | `no_new_unresolved` (wiring_check) y `no_new_unresolved_vs_before` (j5_apply) se evaluan solo sobre el codigo PROPIO | El untrack de los 37 directorios `build/` del plan de j4 deja sin resolver referencias del codigo de TERCEROS vendorizado (plex/tailwind/transformers importaban esos artefactos) | Misma regla que D-18: los terceros se INFORMAN (`third_party_unresolved_reported`), solo el codigo propio bloquea |
| D-26 | `j5_apply` cachea el conjunto "before" de referencias indexado por el sha del commit (`/tmp/before_unresolved.json`) | El build del grafo tarda ~10 min y se ejecutaba dos veces por job (idempotencia por cache, sin alterar el resultado: es determinista) | Ahorra ~10 min por reejecucion; el hash del commit garantiza que la cache corresponde al mismo arbol |
| D-27 | `kernel.py apply` es idempotente (una entrada por job+run_id; el flag del job se recalcula) | La guia hacia `log.append` a ciegas: repetir apply duplicaba entradas y flags (X-Ray 2026-11-05) | Reaplicar el mismo resultado NO cambia el log ni el progreso |
| D-28 | `ops/hf_job.py legacy_command()` publica el log con `upload_file(path=...)` (argumento con nombre) | `huggingface_hub` >= 2.x exige `path=` como keyword: con el path posicional el job 6aebc8980e0338d1bb804a42 lanzo `TypeError` y no publico el artefacto (X-Ray 2026-11-05) | Los scripts heredados siguen byte-identicos; el fix esta en el lanzador |
| D-29 | El comando del job heredado termina en `cat /tmp/job.log` | La evidencia del job quedaba solo dentro del contenedor (log de HF vacio) | La evidencia queda visible en el stdout del job |
| D-30 | Un solo envoltorio `bash -lc` en el comando del job heredado | El comando venia doblemente envuelto (`bash -lc "bash -lc ..."`) | Sin cambio de comportamiento, comando legible |
| D-31 | `j0_preflight` valida el SHA-256 de `kernel/INPUT_BLOCK.yaml` contra `handoff.input_block_sha256` | El guia congela el bloque de entrada pero no lo verifica en el pipeline (X-Ray 2026-11-05) | El hash congelado queda registrado en el kernel; si el bloque se edita, el preflight FAIL |
| D-32 | `ops/hf_job.py create()` envia SIEMPRE el comando como `["bash","-lc",<string>]` | Con `command.split()` el contenedor ejecutaba el primer token como binario: `exec: "set": executable file not found in $PATH` -> el job moria al arrancar (6aebd2580e0338d1bb804d1f/d21) | Sin split: el shell recibe el comando completo |
| D-33 | `j5_apply` es REEJECUTABLE: tag reutilizado (`-f` + push --force), rama con `checkout -B`, `git mv` tolerante, commit con `--allow-empty` | La reejecucion moria en `git tag` (rc=128, "tag already exists") y en `checkout -b` (rama existente): el job solo podia ejecutarse una vez (X-Ray 2026-11-05) | Mismo resultado en la primera ejecucion; la segunda ya no falla por estado residual |
| D-34 | `j6_rewrite` publica el bundle con `upload_file(path=...)` y usa `git remote set-url` | `huggingface_hub` >= 2.x exige `path=` (con `path_or_fileobj=` -> TypeError, el bundle de rollback no se publica) y `git remote add` falla si origin ya existe (rc=128) | Mismo efecto, reejecutable |
| D-35 | `ops/launch.sh` anade el `bin` del interprete al PATH | `git filter-repo` (necesario en S10) vive en el venv: sin esto el job muere con "git: 'filter-repo' is not a git command" | Sin cambio de comportamiento |
| D-36 | `j5_apply` reintenta el `TEST_CMD` hasta 5 veces (30 s) y el check `before_cached` es INFORMATIVO | El Space RIU se redespliega cada ~60 s (autosync) y `/health` da 503 transitorio; ademas un "cache miss" del grafo se registraba como check fallido y hacia FAIL el job | El gate sigue exigiendo rc=0 real, con tolerancia a un redesplie; el cache solo informa |
| D-38 | Se registra el dominio `memoria` (`chat-router/memoria`) en `KERNEL.yaml -> domains` | El lote R2-L3 lleva un fichero a `chat-router/memoria/` y ese prefijo no era dominio: violaba la layout_rule "todo fichero pertenece a un dominio" | Dominio registrado; el fichero tiene dueño |
| D-39 | `wiring_check.run(root, graph=None)` acepta un grafo ya construido y `j5_apply` reutiliza el suyo | El job hacia 2 builds del grafo (~10 min cada uno) sobre 374.205 ficheros | Un solo build por job; mismo resultado |
| D-40 | `VENDORED` (en `ops/j2_graph.py` y `ops/wiring_check.py`) reconoce tambien la nueva ubicacion `agents/...` | Al mover `chat-router/agentes/` -> `agents/` los prefijos de terceros dejan de casar y 38.405 referencias vendorizadas pasan a "propias" y bloquean el gate | Ambas formas conviven durante la transicion |
| D-41 | `no_new_unresolved` compara contra el baseline por `(basename, destino)` | El baseline (65.908 entradas) esta indexado por ruta: cualquier renombrado del lote R2 lo invalidaba y hacia fallar el gate | El renombrado conserva el nombre de fichero, asi que la comparacion sigue detectando referencias nuevas sin penalizar los movimientos |
| D-45 | `ops/backend_smoke.py` (nuevo): arranca el backend REAL y hace el smoke del gate `TEST_CMD`, en un Job de HF | El Space `riu-router` esta en hardware de pago sin saldo (HF responde 402) y queda PAUSED: su /health da 503 y el gate "real backend start + smoke" no se puede cumplir a traves del Space | Misma semantica del gate (backend real arrancado + /health real), sin depender del saldo del Space; publica rc+log en el Dataset |
| D-46 | Los Jobs de HF se crean con `flavor=cpu-upgrade` (el hardware del owner, 32 GB + CPU) | El owner decide no bajar a hardware gratis y esperar su recarga | Sin cambio de hardware; el Space mantiene el suyo |
| D-48 | `j5_apply` pushea la tag SIEMPRE con `--force` | En la reejecucion la tag ya existe en remoto y el push se rechaza ("already exists") -> rc=1 y el job muere (X-Ray 15 min, 2026-11-05) | La tag es el punto de rollback del run; forzarla es idempotente |
| D-49 | `ops/backend_smoke.py` fija el PYTHONPATH completo (backend, router-mvp, chat-router, chat-router/chat) | El backend importa `mvp`, `router`, `agentes` y `plugins`, que viven en raices distintas: con solo el backend en el PYTHONPATH el arranque peta con "No module named 'router'" (X-Ray 15 min, 2026-11-05) | Arranque real del backend con sus imports reales |
| D-51 | La cadena registra un flag y CONTINUA cuando un nodo queda en rojo, en vez de abortar | Contrato del DAG: N8_gap_loop -> N9_flag -> seguir con los nodos independientes; el gate sigue FAIL_CLOSED (el nodo rojo no se da por bueno) | Cada nodo publica igualmente su resultado y el kernel guarda el flag |
| D-52 | La rama de trabajo se exporta antes del bloque de lotes R2 | Con `set -u` una variable no definida abortaba la cadena entera ("TARGET_BRANCH: unbound variable") | La rama ya existe (la publica j5_apply) |
| D-53 | `ops/job_status.py` (nuevo): el estado de cada job se lee del Dataset, no del fichero local de resultados | La cadena consultaba /tmp/out/<job>/result.json, volatil y borrado en cada reejecucion: tras reiniciar el sandbox volvia a ejecutar jobs ya en verde | El Dataset es la fuente durable de resultados |
| D-54 | `ops/make_healthchecks.py` (nuevo): genera un healthcheck real por conexion con canal real y lo EJECUTA | §5/§8: "sin healthcheck no hay activo"; el registro tenia los 38 campos pero 0 verificaciones | 14 conexiones con canal real documentado; 8 verificadas por import ejecutado, 6 con el modulo presente en el arbol git pero no materializado en el clon sparse local (se verifican en el clon completo), 0 rotas |
| D-55 | `ops/verify_pending_healthchecks.py` (nuevo): cierra en el clon completo las 6 verificaciones que el clon sparse local no podia materializar | 6 conexiones quedaron `pending_verificacion` (su modulo esta en el arbol git pero el clon sparse no lo trae) | 6/6 responden al import real en el clon completo -> 14/14 conexiones con canal real en `active` |
| D-56 | El push del mirror al Space pasa de `upload_folder` (endpoint de commits de HF) a `git push` por protocolo git al repo del Space, preservando antes los ficheros propios del Space (Dockerfile, boot.sh, proxy.py...) | El endpoint de commits de HF rechaza el push cuando el repo tendria >10.000 ficheros: "Your push was rejected because it contains too many files ... 20008 files" -> S7 FAIL | El push por git admite el tamano del mirror; el arbol del Space conserva sus 8 ficheros |
| D-57 | La cadena omite los lotes R2 si la rama de reorganizacion ya esta publicada | Tras reiniciar el sandbox la cadena re-aplicaba los movimientos ya aplicados (25 min y riesgo de colision) | `git ls-remote` comprueba la rama antes de aplicar |
