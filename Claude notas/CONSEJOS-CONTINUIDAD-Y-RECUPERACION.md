# CONSEJOS Y ESTRATEGIAS — CONTEXTO ACTIVO, RECUPERACIÓN Y CONTINUIDAD

Repo: `maxbry123-commits/router-universal-router-inteligente-` · rama `main`
Escrito 2026-09-18 por el Claude que retomó el trabajo (cuenta 2 del equipo).
Regla de este archivo: se actualiza AÑADIENDO, nunca borrando ni resumiendo. Cada consejo nació de algo que el repo ya exige (CLAUDE.md, GUIA-MAESTRA) o de un fallo real que se vio al recuperar contexto.

---

## 0. Idea central
El chat se olvida; el repo no. Todo lo que otra cuenta necesite para seguir tiene que estar en GitHub `main` ANTES de que se acabe el plan.
Un dato importante vive en UN solo archivo autoritativo; los demás lo referencian, no lo copian. Copiar estado en cinco archivos produce deriva (ver sección 6).

## 1. Modelo mental: capas de memoria
1. Contrato y reglas — `CLAUDE.md`, `GUIA-MAESTRA-EJECUCION-LOOP-...md`. Casi no cambian.
2. Estado operativo — `STATE.json`, `CHECKPOINT.json`, `PLAN-TAREAS.md`, `RECOVERY-PATCH.md`. Cambian con cada nodo.
3. Ledger histórico — `BITACORA-CRAZY-WALL.md`, `forensics/*`. Solo se añade.
4. Memoria de Claude — `Claude notas/`. Lo aprendido, decisiones del Director, correcciones y traspasos.
5. Handoff — `Handoff router inteligente universal.md`. Resumen para quien llega en frío.
Regla: si algo no está en una de estas capas, no existe para la siguiente cuenta.

## 2. Antes de que se acabe el plan (traspaso en caliente)
1. Aviso temprano: cuando quede ~15-20% del plan, dejar de abrir frentes nuevos y solo cerrar el delta en curso.
2. Cerrar el delta actual hasta un estado claro: `VERIFIED_CLOSED`, `GAP` con evidencia, o `NOT_APPLIED` (no dejar cosas a medias sin marcar).
3. Anotar en la bitácora el nodo actual, qué se hizo, qué falta y cuál es el siguiente delta seguro.
4. Actualizar `STATE.json` / `CHECKPOINT.json` solo si cambió el estado operativo (regla de CLAUDE.md).
5. Verificar con read-back que lo escrito quedó en `main` (no confiar en que el commit "pasó").
6. Dejar en `Claude notas/` un mensaje de traspaso corto (plantilla en sección 12) con: HEAD SHA, nodo, próximo paso literal, preguntas abiertas para el Director.
7. Si hay una instrucción del Director aún sin ejecutar, copiarla literal (input block 1 a 1) al traspaso; no parafrasear.
8. Decirle al Director, en el chat, "estoy por quedarme sin plan, todo lo importante está en X commit" para que cambie de cuenta sin perder nada.

## 3. Arranque de una cuenta nueva (boot)
Orden exacto (respeta GUIA-MAESTRA §3 y añade lo aprendido):
1. `Claude notas/00-LEEME-PRIMERO.md` (índice, correcciones y estado consolidado).
2. `CLAUDE.md` (contrato, permisos, fail-closed).
3. `STATE.json` → `CHECKPOINT.json` → `PLAN-TAREAS.md` → `RECOVERY-PATCH.md`.
4. `BITACORA-CRAZY-WALL.md`: leer las últimas 3 entradas RIU primero, luego hacia atrás solo lo necesario.
5. `Handoff router inteligente universal.md`.
6. `Claude notas/memoria.md` y el resto de `Claude notas/`.
7. HEAD real: últimos ~10 commits (`GET /repos/.../commits`). Comparar el último RIU de la bitácora con los mensajes de commit.
8. Regla de oro: si dos documentos se contradicen, gana el que tenga (a) fecha/nodo más nuevo Y (b) evidencia verificable (SHA, log, código leído). En duda, leer el código o el commit, no el resumen.
9. Al terminar el boot, responder al Director con: nodo actual, último `VERIFIED_CLOSED`, contradicciones encontradas y siguiente delta seguro. No empezar a escribir sin ese resumen.

## 4. Qué anotar y dónde
| Evento | Archivo | Cómo |
|---|---|---|
| Delta terminado (código, test, decisión) | `BITACORA-CRAZY-WALL.md` | Nueva entrada `RIU-XXXX` al final |
| Cambió el estado operativo (gates, closed/pending) | `STATE.json` + `CHECKPOINT.json` | Migrar sin borrar provenance: lo viejo pasa a `SUPERSEDED_PROVENANCE_ONLY` |
| Cambió el plan | `PLAN-TAREAS.md` | Nodo activo + GAPs autoritativos |
| Para quien llega en frío | `Handoff ...md` | Bloque "Estado que debe heredar el próximo chat" |
| Instrucción o decisión del Director | `Claude notas/` | Literal (verbatim), con fecha |
| Aprendizaje / corrección de un error propio | `Claude notas/` | Archivo o adenda nueva; no reescribir historia |
| Evidencia dura (informe forense) | `forensics/RIU-XXXX-...md` | Un archivo por hallazgo |
| Cambió la arquitectura | README arquitectura | Solo si cambia de verdad |

## 5. Plantilla de entrada RIU (para la bitácora)
```
## RIU-XXXX — TÍTULO CORTO — FECHA
Contrato: tel.workflow/v3 · FAIL_CLOSED_LOOP. Autorización: (referencia a la del Director)
### Input literal del Director
(pegado tal cual)
### Trabajo realizado
- qué archivo, qué commit SHA, qué se leyó, qué se escribió
### Evidencia
- ruta + SHA de commit/blob + read-back + log/run id (o "NO EJECUTADO")
### GAPs nuevos / actualizados
- GAP-...: estado, causa, quién debe actuar
### Estado del nodo
CODIGO_ESCRITO | TEST_ESCRITO | TEST_EJECUTADO | VERIFIED_CLOSED  (usar el más bajo que sea cierto)
### Próximo delta seguro
```

## 6. Anti-deriva (lección real de esta recuperación)
Al recuperar contexto aparecieron estas contradicciones REALES:
- `memoria.md` §8.2/§10.5 decía que `hf_scheduler.py` "falta implementar"; el código existe y está probado (RIU-0074, Job 5/5).
- `Handoff` y `CHECKPOINT` decían `GAP_ADAPTER_REGISTRY_SCHEMA` abierto/`false`; el código ya lo repara (RIU-0098) y la bitácora lo registra.
- `STATE.json` sigue en RIU-0086, `PLAN` en RIU-0089, `CHECKPOINT` en RIU-0097, `Handoff` en RIU-0093, bitácora en RIU-0100.
- CLAUDE.md dice `tel.workflow/v3`; la GUIA-MAESTRA dice `tel.workflow/v4`.
Estrategias:
1. Un hecho, una fuente. Los demás archivos apuntan a esa fuente ("ver RIU-0074") en vez de repetir el dato.
2. Antes de escribir "falta X" o "no existe X": comprobar en el repo (buscar el archivo, leer el commit). Escribir "falta" sin mirar es la causa n.º 1 de deriva.
3. Sellar cada afirmación de estado con fecha o nodo (`al 2026-09-18, HEAD 3e6fc22`). Un estado sin sello envejece en silencio.
4. Cuando se descubra una contradicción: no borrar la vieja; añadir una CORRECCIÓN con fecha que diga cuál manda y por qué (evidencia).
5. Reconciliar en bloque, no a trozos: STATE, PLAN, CHECKPOINT, Handoff y bitácora se sincronizan juntos (`STATE_RECONCILIATION → CRAZY_WALL_SYNC → PLAN_SYNC → CHECKPOINT_SYNC → HANDOFF_SYNC`). Dejarlo a medias fue lo que creó el desfase actual.
6. "100 %" siempre con alcance: `core_status=VERIFIED_CLOSED` es SOLO el alcance histórico P01/P02/P03 (hot-path GitHub público). No es cierre del backend C01-C23 ni del proyecto (`global_closed=false`).
7. No mezclar catálogos: el "20/20 accounted" histórico y el REMOTE20 V2 son inventarios distintos (RIU-0091). Nombrar siempre cuál.

## 7. Coordinación entre cuentas
1. Una sola cuenta escribe a la vez en el mismo archivo. Antes de editar `STATE.json`, `CHECKPOINT.json`, `PLAN` o la bitácora: leer el HEAD y el `sha` del archivo; escribir con `current_sha`. Si falla por conflicto, releer y fusionar (no sobrescribir).
2. Reclamar el nodo: al empezar, dejar una línea en la bitácora ("RIU-XXXX en curso por cuenta N"). Al terminar, cerrarla.
3. Reparto por carpeta para evitar choques: cada cuenta tiene un frente (p. ej. cuenta A = HF/registry, cuenta B = docs/sync). Lo que cruce frentes se anota antes.
4. Regla P3 vigente: esta cuenta escribe SOLO en `router-universal-router-inteligente-`. Otros repos (`agentes`, `frontend`, `nct-core`...) se leen, no se escriben. El PAT técnicamente alcanza más repos: la restricción es de método, respétala.
5. Identificar la sesión en cada commit (`Co-Authored-By` / `Claude-Session`) como ya se hizo en RIU-0098; permite saber quién hizo qué al reconstruir.
6. Mensajes de commit con prefijo de nodo (`RIU-0101: ...`, `fix(hf): ...`). Facilita comparar bitácora vs commits.
7. Las instrucciones del Director llegan como input block 1 a 1: un input = un nodo literal. No fusionar ni reinterpretar dos instrucciones en una.
8. Cambio de cuenta sin perder acceso: reusar el mismo conector MCP (`GitHub_Backup_HF`) en la cuenta nueva (Settings → Connectors → Add custom connector → misma URL) y verificar con `GET /user` (debe devolver `maxbry123-commits`). Ver RIU-0100.

## 8. Escritura segura en GitHub
1. Leer antes de escribir; usar `current_sha`; hacer read-back después (comparar tamaño y buscar un marcador único de lo escrito).
2. Solo añadir: la API no permite "append"; reescribir un archivo grande es un riesgo de corrupción. Preferir archivos pequeños nuevos + un índice a reescribir un archivo de 30-45 KB.
3. Cuidar codificación: algunos archivos empiezan con BOM (`BITACORA-CRAZY-WALL.md`, `memoria.md`); nombres con emoji y acentos deben copiarse exactos.
4. Nunca `force` sobre `main`. Nunca borrar evidencia (lección: RIU-0072 preserva LiteLLM/litellm hasta comparar provenance).
5. Un commit = un delta con mensaje que diga qué y por qué. Evitar commits gigantes que mezclen frentes.
6. Nunca escribir valores de secretos (PAT, HF token, OAuth) en Git, logs, Handoff, bitácora ni chat. Solo nombres de referencia (`RIU_HF_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`).
7. El árbol recursivo de GitHub viene truncado (`truncated=true`, ~35.9 k entradas). Listar por sub-árbol (`git/trees/<sha>?recursive=1` de cada carpeta) y nunca declarar inventario total desde un árbol truncado.

## 9. Higiene del contexto dentro del chat
1. Leer en escalera: índice → estado → detalle solo de lo que toca. No abrir los ~62 donors (`Componente open soure...`): son librerías vendor, no proyecto; su presencia no es integración.
2. Un delta por vez, cada cierto tiempo un mini-resumen de checkpoint en el chat (nodo, hecho, siguiente). Sirve de ancla si el chat se compacta.
3. Si una respuesta de herramienta es enorme, guardarla en archivo y filtrar con grep/python en vez de pegarla entera al contexto.
4. Pedir al Director una sola pregunta a la vez; anotar la respuesta en `Claude notas/` en cuanto llegue, antes de seguir.
5. Tras una compactación (`/compact`) o cambio de cuenta, RE-LEER STATE/CHECKPOINT/bitácora en vez de fiarse del resumen automático.
6. Anti-stall (GUIA §6): tras 1-3 lecturas útiles debe haber un delta físico o un `BLOCKED` justificado; cinco lecturas seguidas sin cambio = `STALL_DETECTED` → ejecutar el delta mínimo seguro.
7. No repetir análisis ya cerrado: consultar la bitácora antes de investigar de nuevo (p. ej. REMOTE20 ya está en RIU-0091/0094).

## 10. Evidencia y honestidad
1. Distinguir siempre: código escrito ≠ test escrito ≠ test ejecutado ≠ verificado. Etiquetar con el estado más bajo que sea cierto (`CODE_COMMITTED_TEST_WRITTEN_EXECUTION_PENDING`).
2. `archivo presente ≠ integrado`; `test mock ≠ test real`; `catálogo ≠ inferencia autenticada`; `provider live ≠ READY`.
3. PASS exige ruta + commit/blob SHA + diff + log/run id + URL + read-back + test. Sin esa evidencia: `GAP`, con causa y quién debe actuar.
4. Separar bug de código de límite externo: el 403 de REMOTE20 es límite de credencial/cuenta (`GAP-EXTERNAL-CREDENTIAL-SCOPE-001`), no de código. No prometer arreglarlo con un commit.
5. Corregir los errores propios a la vista y con fecha (como esta adenda); no maquillar el historial.
6. No inventar `model_id`, versiones, hashes ni cifras. Si no se leyó, decir "no leído".

## 11. Recuperación cuando algo se corta
- Chat cortado a mitad de un delta: comparar el último commit de `main` con la última entrada de la bitácora.
  - Commit existe, nota no → anotar retroactivo con el SHA real.
  - Nota existe, commit no → marcar la entrada `NOT_APPLIED` y rehacer el delta.
- Herramienta o conector caído: `GitHub Backup HF` es respaldo opcional y NO bloquea (CLAUDE.md); GitHub directo (workflow `Claude Root Editor`) es la ruta canónica.
- `RECOVERY-PATCH.md`: refrescarlo cada varios nodos con "punto exacto de recuperación" (nodo, comando, resultado esperado). El actual está en RIU-0066 y quedó viejo.
- Regla del método del otro Claude (repo `agentes`): "Si esta conversación se corta, ESTE es el punto de partida" — mantener un parche de recuperación con quién soy, ecosistema, dónde está cada cosa y qué sigue.
- Si dos cuentas escribieron a la vez: no elegir a ciegas; leer ambos commits, fusionar a mano y anotar la fusión.

## 12. Plantilla de mensaje de traspaso (para dejar en `Claude notas/`)
```
TRASPASO — fecha — de cuenta N a cuenta N+1
HEAD al traspasar: <sha> (último commit: <mensaje>)
Nodo actual: RIU-XXXX — estado: <CODIGO_ESCRITO|TEST_EJECUTADO|VERIFIED_CLOSED|GAP>
Lo último que hice (con SHAs):
Lo que sigue (literal, un solo delta): 
Instrucción del Director aún pendiente (verbatim):
Preguntas abiertas para el Director:
Contradicciones detectadas y no resueltas:
```

## 13. Checklists cortos
Inicio de sesión: [ ] leí 00-LEEME [ ] leí STATE/CHECKPOINT/PLAN/bitácora [ ] comparé con HEAD [ ] listé contradicciones [ ] dije el nodo actual al Director.
Cada delta: [ ] destino exacto claro [ ] reuse revisado (REUSE > PATCH > ADAPT > GENERATE) [ ] escribí [ ] read-back [ ] anoté en bitácora [ ] ¿cambió el estado? → STATE/CHECKPOINT.
Fin de sesión (5 min): [ ] nada a medias sin marcar [ ] traspaso escrito [ ] HEAD anotado [ ] preguntas abiertas listadas.
Traspaso de cuenta: [ ] conector MCP reusado y verificado con GET /user [ ] la cuenta nueva leyó 00-LEEME antes de tocar nada.

## 14. Anti-patrones vistos (evitar)
- Escribir "falta X" sin comprobar en el repo (creó la contradicción de hf_scheduler.py).
- Actualizar un solo archivo de estado y olvidar los otros cuatro.
- Declarar "100 %" sin decir el alcance.
- Confiar en un resumen de chat compactado en lugar de releer el estado.
- Mezclar dos inventarios con el mismo nombre ("20 modelos").
- Reescribir un archivo grande a mano sin verificar tamaño ni read-back.
- Tratar un límite de permisos externos como si fuera un bug de código.

## 15. Propuestas de mejora estructural (NO ejecutadas — decide el Director)
1. Partir `BITACORA-CRAZY-WALL.md` (33 KB y creciendo) en tramos (`BITACORA-RIU-0001-0099.md`, `BITACORA-RIU-0100-....md`) con un índice; así cada nodo nuevo es un archivo pequeño y el append deja de ser una reescritura arriesgada.
2. Un archivo `NODE-INDEX.json` con una línea por RIU (id, título, estado, commit) que sirva de tabla de contenidos legible por máquina.
3. Un script/workflow "consistency check" que compare `current_node` de STATE, CHECKPOINT, PLAN, Handoff y última entrada de la bitácora y falle si difieren (detecta deriva automáticamente).
4. Decidir oficialmente `tel.workflow/v3` vs `v4` y dejarlo escrito en CLAUDE.md.
5. Correr `test_huggingface_openai_chat_registry.py` en un runner real (GAP-TEST-EXECUTION-001) para poder cerrar el fix con log.
6. Un registro de "quién es dueño de qué frente" por cuenta, para no pisarse al alternar cuentas.
