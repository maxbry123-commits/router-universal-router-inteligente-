# EQUIPO-8 · I-FUNCIONES-FALTANTES — funciones visibles ausentes de plan y backend

Comparación contra `T-06-INVENTARIO.md`, `chat router/Workflow Loop code Yaiwes/13-CHAT-UI-SUITE/gateway.py` y `chat router/ui/*`. Se listan solo funciones visibles sin control/endpoint equivalente.

| Función faltante | Dónde se ve | Motivo |
|---|---|---|
| Workspace completo de revisión de PR | UI-EXTRA-014..016; UI-REF-038..048 | Overview/Changes/Description/Discussion/Commits/Checks/Bugs, merge y diff avanzado no existen en T-06 ni en gateway/UI backend. |
| Monitor automático de comentarios, CI y conflictos de PR | UI-EXTRA-014 | No hay contrato T-06 ni endpoint backend para vigilancia de comentarios/CI/conflictos o para desactivarla. |
| Estado de despliegue Vercel dentro del PR | UI-EXTRA-014 | No hay panel/endpoint de deployments en T-06 ni backend actual. |
| Smart diffs, detección de código movido y bugs con AI | UI-EXTRA-016; UI-REF-042 | No hay función equivalente en T-06 ni backend. |
| Uso de suscripción ChatGPT desde selector de modelo | UI-EXTRA-017 | T-06 selecciona proveedor/modelo, pero no controla plan/suscripción ni backend expone ese toggle. |
| Entrada de voz/micrófono en composer | UI-EXTRA-017; UI-REF-022/054/063 | T-06/chat backend procesa texto; no hay STT/voz en el contrato actual. |
| Intervención humana estructurada durante una tarea | UI-REF-007 | No existe control/endpoint de NEEDS_INTERVENTION con formulario de opciones. |
| Telemetría detallada de tarea y rating | UI-REF-008 | No hay métricas de páginas/comandos/API/archivos/créditos/tiempo ni rating en T-06/backend. |
| Acciones de ciclo de vida de tarea | UI-REF-009 | Añadir a proyecto, renombrar, programar, fijar, favorito, archivar y eliminar no están en T-06/backend. |
| Toolbox multimodal/generativo | UI-REF-010..011 | Crear/editar imagen, audio, video, juegos, diapositivas, sitios, apps y hojas no existe en T-06/backend. |
| Wide Research, Playbook y conectar computador remoto | UI-REF-011 | No hay controles ni endpoints equivalentes. |
| Catálogo/selector de Skills | UI-REF-012 | No hay picker de skills en T-06 ni backend UI actual. |
| Historial/buscador de tareas recientes | UI-REF-013 | No hay endpoint/control de recent tasks. |
| Vista jerárquica de subtareas | UI-REF-016 | Seguimiento T-06 consulta ledger, pero no ofrece árbol/vista de subtareas. |
| Centro de cuenta ampliado | UI-REF-017..018 | Créditos, share, Knowledge, Mail, data controls, cloud browser, versión, cache y logout no están en T-06/backend. |
| Configuración de bot/orquestador | UI-REF-020..021 | Auto-review, timezone, bot computer, haptics y preferencias de bot no existen en el contrato/backend. |
| Comandos slash del chat | UI-REF-025 | No hay command palette ni registro de slash commands en T-06/backend. |
| Gestión de entornos/builds/snapshots/blueprints/outputs | UI-REF-024; UI-REF-028..030 | No hay endpoints ni controles para entornos, snapshots diferenciales, schedules, blueprints u outputs. |
| Política de apertura de enlaces PR | UI-REF-031 | No existe selección in-session/Devin Review/Git Provider. |
| Terminal/log de ejecución en vivo | UI-REF-041 | T-06 consulta ledger por ID, pero no expone terminal/live command stream. |
| Defaults de sesión, custom commands y usage limits | UI-REF-049..050 | No existen estas configuraciones en T-06 ni en gateway/UI actual. |
| Automatización de comportamiento de PR y perfiles de seguridad | UI-REF-051..052 | No hay reglas de @mention, auto-reviewer, bots permitidos o security profiles en T-06/backend. |
| Scheduler de automatizaciones con trigger e instrucciones | UI-REF-055 | No hay creador de automatizaciones programadas en T-06/backend. |
| Notificaciones push/email por automatización | UI-REF-056 | No hay canales push/email configurables en T-06/backend. |
| Crear/probar rama alternativa desde resultado | UI-REF-057 | T-06 contempla rama no editable, no un flujo de branching experimental. |
| Dashboard de hosts/push/content | UI-REF-060 | No existe módulo de hosts, push messages o content feed en T-06/backend. |
| Dashboard de facturación/Quick Payment | UI-REF-062 | Referencia visual sin función equivalente en plan/backend. |
