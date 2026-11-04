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
| D-16 | `j7_mirror` acepta `BASELINE=1` (baseline read-only, sin subir al Space) | El DAG en `S4_approval.if_missing` exige "j7 on main as read-only baseline, mirror skipped" y el script no tenía ese modo | Calcula ficheros/tamaño y estado del Space sin desplegar; el mirror real queda para `j9_remirror` (aprobación `deploy`) |
