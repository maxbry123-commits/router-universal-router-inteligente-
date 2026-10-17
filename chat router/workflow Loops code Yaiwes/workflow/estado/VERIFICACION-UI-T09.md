# T-09 — comparación con la especificación visual

Fecha de verificación estática: 2026-10-01T03:37:20Z. Fuente: `chat router/Workflow Loop code Yaiwes/01-PLAN/ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md` (copia idéntica en `chat router/Workflow Loop code Yaiwes/01-PLAN/SKILLS-MAXBRY-UI/diseno/`). Evidencia implementada: `chat router/ui/`, `integration/chat_mvp/{app,router,org_api,fables_adapter}.py` y pruebas `tests/test_org_api.py`. VERIFIED indica lectura de código/prueba automatizada; no implica verificación visual en navegador.

| Sección | Estado | Evidencia, motivo del GAP y siguiente paso |
| --- | --- | --- |
| §0 guía de lectura | VERIFIED | Se compararon las secciones del documento, sin cambiarlo. |
| §1 paleta y geometría | GAP | Seis grises y azul especificados están en `shell.css` y tienen prueba; faltan colores semánticos, radios 18/16/22px y verificación visual. Ajustar estilos y capturar pantalla con autorización. |
| §2 arquitectura resumida | GAP | Solo están las vistas del Router; faltan familias de editor visual, habilidades y automatizaciones. Añadir cuando existan fuentes reales. |
| §3 conectores Claude | GAP | Lista Fables de lectura disponible; no hay detalle, reconexión ni estado OAuth. Crear contratos y fuente de salud antes de controles. |
| §4 FROMTED | GAP | Sin editor de tema, biblioteca de iconos ni simulador móvil. Reutilizar recursos existentes mediante el flujo de componentes autorizado. |
| §5 perfil visual | GAP | Navegación lateral básica presente; faltan apariencias y equivalencia móvil. Comprobar en navegador. |
| §6 patrones de referencia | GAP | Cards genéricas en CSS; faltan variantes de dashboard y kit de controles. Comparar capturas después de implementarlas. |
| §7 tareas, habilidades y automatización | GAP | Cola de solo lectura vacía sin worker; no hay habilidades ni formulario de automatizaciones. Conectar fuentes reales antes de habilitar acciones. |
| §8 modos y bots | GAP | Tres modos presentes como límites de tokens; faltan bots/ajustes y profundidad de razonamiento real. Exponer contrato del Router. |
| §9 composer Devin | GAP | Hay selector de agente y rama deshabilitada; faltan adjuntar desde composer, comandos slash completos y selector de rama operativo. Cablear contratos autorizados. |
| §10 Router, plantillas, conectores e ingeniería | GAP | Vistas Fables/plantillas/ingeniería de lectura presentes. No existe selección y ejecución de plantilla, Sentinel de runtime ni fuente de toggles; Fables sigue INACTIVE. Implementar activación aprobada y ejecución inmutable. |
| §11 evidencia | GAP | Seguimiento lee bitácora y ledger persistido; no muestra CREATED→TESTED→VERIFIED→READY→MERGED→BLOCKED ni revisión por etapa. Añadir proyección con evidencia real. |
| §12 componentes universales | GAP | Shell propio sin cuatro componentes RUI (grid-reveal, fluid-orb, matrix-orb, step-player). Solo adquirirlos por el workflow RDC previsto. |
| §13 contrato universal | GAP | Fichas de panel registradas INACTIVE en Fables; shell importa módulos directamente y no renderiza contrato universal. Definir gate de activación antes de montaje dinámico. |
| §14 appState | GAP | `shell.js` mantiene la vista activa; no hay modelo completo para chain/engineering/conectores. Consumir proyecciones reales, sin valores simulados. |
| §15 HTML | GAP | Shell y paneles semánticos disponibles y servidos en pruebas; falta cotejo visual del layout de referencia. Probar en navegador con permiso. |
| §16 CSS | GAP | Paleta base presente; estilos condensados no implementan la geometría ni toda la responsividad de referencia. Ajustar y cotejar capturas. |
| §17 JavaScript | GAP | Router de vistas y API única probados sintácticamente; interacción real y consola no comprobadas. Probar interfaz con permiso. |
| §18 selector de plantillas | GAP | Listado LOCKED de solo lectura; falta selección/ejecución autorizada. Incorporar un endpoint de ejecución con validación Sentinel. |
| §19 automatizaciones | GAP | No hay fuente ni formulario. Conectar servicio real y validar permisos. |
| §20 máquina de estados | GAP | Existen estados de backend y badges básicos; UI no aplica todas las transiciones ni muestra needs_intervention completo. Derivar transiciones de backend. |
| §21 modelo de datos | GAP | Graph, files y connectors provienen del backend; plantillas y toggles no siguen el modelo unificado. Publicar proyecciones respaldadas por datos. |
| §22 mapa funcional | GAP | Chat/archivos/seguimiento/canvas parciales; faltan voz, tareas reales, cadena, evidence graph y controles de ingeniería. Resolver los GAPs §7-21. |
| §23 capturas de referencia | GAP | Archivos reubicados sin cambio de contenido; no se han cotejado píxel a píxel ni generado captura de la nueva UI. Validación visual pendiente. |
| §24 instrucciones para otra IA | GAP | El handoff documenta fuentes y primer nodo no PASS; faltan módulos para reconstruir el alcance completo. Retomar desde T-05. |
| §25 resumen final | GAP | Cobertura parcial de navegación y paleta; continuar por los GAPs anteriores. |

Otros GAPs del plan: T-06 pide ninguna clave en navegador, pero la UI utiliza `X-API-Key` conservada solo en memoria JS; requiere sesión de servidor HttpOnly. T-07 exige `.github/workflows/research-download-chain-router-components-20260903.yml`, ausente tanto en esta rama como en `origin/main`; no se hizo descarga ni se fabricó evidencia. CI de GitHub Actions no inició por bloqueo de facturación, según anotación del job; esto no valida código.

## T-05 — decisión B del Director (auditoría ≠ mutación)

La contradicción anterior quedó resuelta por decisión expresa del Director: cada GET de `/chat/org/*` añade un evento `RESOURCE_READ` append-only en `BITACORA.jsonl` como telemetría, y está prohibido que un GET cambie `status`, `payload`, `workflow_state`, `business_state` o cualquier dato del recurso leído.

Implementación y evidencia en `tests/test_org_api.py`:

- `ui_bridge._emit_state_audit_event` escribe solo en la bitácora, con read-back del contenido persistido, y no regenera `STATE.json` ni `CRAZY_WALL.json`.
- `_state_projection` ignora los eventos `RESOURCE_READ`, así que la proyección funcional es idéntica antes y después de las lecturas.
- `POST /state/events` rechaza `RESOURCE_READ` con `STATE_AUDIT_ONLY_FROM_GET`; ese tipo solo lo produce la capa de lectura.
- Las respuestas de error deterministas (`DAG_ID_INVALID`, `DAG_NOT_FOUND`, `LIMIT_INVALID`) también se auditan con su código HTTP.
- Si la auditoría no se puede persistir, la vista falla cerrado con `{"status":"error","detail":"STATE_AUDIT_UNAVAILABLE"}` y HTTP 503, sin devolver datos.
- La prueba verifica secuencias crecientes, ausencia de escrituras en SQLite y archivos canónicos intactos.

GAP restante de T-05: sin credencial de GitHub la escritura de auditoría no es posible, por lo que las ocho vistas responden 503 en un entorno sin `RIU_GITHUB_PAT_FULL_ACCESO`; no se ha verificado el recorrido HTTP real contra el repositorio.
