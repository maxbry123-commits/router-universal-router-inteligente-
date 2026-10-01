# Índice canónico del plan

El trabajo existente se define en los DAG T-01..T-12 y sus contratos. `PLAN.json` es un marcador auxiliar creado por Devin a partir del ejemplo de 100 tareas/pasos del mensaje de modo recepción; no hay evidencia de un segundo archivo prometido. La guardia específica de 100 IDs no se inicia sin esos IDs y no bloquea el DAG existente. Las entradas literales del Director se conservan sin edición.

| Área | Ubicación | Estado |
|---|---|---|
| T-01..T-10 y contratos | `PLAN-DSL-DAG-00-CONTRATO.yaml`, `PLAN-DSL-DAG-01-NODOS.yaml`, `PLAN-DSL-DAG-UI.yaml` | Canónico; `PLAN.json` solo es marcador auxiliar |
| T-11 | `T-11/` | Contratos y entradas literales; depende de T-10 |
| T-12 | `T-12/` | Especificación pendiente de ejecución |
| Anexos originales | `ANEXOS/` | Fuentes adicionales conservadas sin alterar sus bytes |
| Método aprobado | `PROPUESTA-METODO-DEVIN-ASK-COUNCIL.md`, `DM-METODO-DAG.json` | Política estructurada y gate verificable |
| Diseño | `ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md`, `REFERENCIAS-UI/`, `CATALOGO-REFERENCIAS-UI.json` | 65 referencias; T-06 pendiente de prueba completa |
| Skills y componentes FROMTED | `SKILLS-MAXBRY-UI/diseno/`, `SKILLS-MAXBRY-UI/componentes/` | 82 archivos, movidos con Git conservando bytes; integración funcional pendiente |
| Diagramas del Router y capturas adjuntas | `REFERENCIAS-UI/ARQUITECTURA-ROUTER/`, `REFERENCIAS-UI/ADJUNTOS-CHAT/`, `CATALOGO-ANEXOS-VISUALES.json` | 5 PNG del Router y 12 adjuntos del chat; catalogados como referencia |
| Auditoría cruzada y siguientes acciones | `AUDITORIA-4-PASADAS.json`, `AUDITORIA-4-PASADAS-POST-CODE.json`, `PLAN-ACCION-XRAY.md` | 30 documentos, 82 skills, 82 imágenes y 18 archivos de código; gaps de ejecución explícitos |
| Inventario T-06 | `T-06-INVENTARIO.md` | Controles y estados enumerados; resultados requieren prueba real en navegador |
| Motor reutilizable | `../../Motores descarga extracción búsquedas/➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/📂Motor descarga de componentes y extracción de zip/` | Fuente examinada, no conectado en vivo |

## Cotejo de la carpeta enlazada por el Director

El commit `aa8fed0631913783c77d3b9ad3fcca62e1978c11` contiene 30 archivos bajo `chat router/01-PLAN`: 9 documentos/contratos de raíz, 12 de T-11, 3 de T-12 y 6 anexos. Los 27 blobs distintos están presentes sin alteración en esta rama; T-11 tiene un par de copias idénticas y las tres versiones de T-12 son idénticas por SHA-256. Los encabezados y contratos están inventariados, pero la revisión funcional exhaustiva de cada documento y la ejecución de T-11/T-12 siguen pendientes. Las 12 capturas enviadas en el chat no son archivos del commit enlazado: ahora se conservan en `REFERENCIAS-UI/ADJUNTOS-CHAT/`; dos envíos de la misma captura son idénticos por hash.

Los tres documentos sueltos de despliegue, README y arquitectura de la raíz del enlace se guardan ahora en `ANEXOS/`; los contratos y el plan de trabajo permanecen en la raíz como puntos de entrada. Las rutas anteriores en bloques de entrada literales se conservan como procedencia.

## Regla de reuso previa a cada tarea

1. Identificar capacidad y buscar primero en componentes ya descargados y en código existente; si no basta, investigar alternativas abiertas hasta hallar un candidato que cubra la tarea. La autorización de descargar hasta 100 componentes no es objetivo de volumen.
2. Registrar fuente, licencia, commit de origen, hash, interfaz, permisos, pruebas y riesgo de mantenimiento. Una descarga no demuestra conexión.
3. Usar el motor de descarga/extracción con read-back en modo sin publicación; su variante actual de publicación hace `push` a la rama configurada, por lo que no se ejecutará contra `main`. Inspeccionar historial y adaptar antes de habilitar publicación segura en rama de trabajo.
4. Aplicar Sheriff, adaptación mínima por el harness DeepSeek existente o el validador Fables cuando proceda, pruebas y receipt de operación; si falta un punto, marcar GAP.

En esta fase no se descargó ningún componente nuevo: la auditoría, el catálogo y la UI reutilizan código, contratos, skills y librerías ya presentes.

## Estado de implementación

`11-EVIDENCIA/auditoria_metodo.py` consume `DM-METODO-DAG.json`, valida la política y emite etiquetas `AUDIT-*`, 12 goals, 12 preguntas asesoras, huecos y veredicto con recibos verificables. La presencia del esquema no ejecuta Hermes ni OpenClaw; sin receipts de esos revisores las áreas críticas quedan `INCOMPLETE`. Los dos catálogos clasifican individualmente 82 imágenes: 65 referencias UI, 5 diagramas y 12 capturas adjuntas. Ninguna se sirve como asset de producto hasta revisión funcional y segunda pasada T-06. Los miles de fixtures e imágenes de paquetes descargados permanecen con el código que los usa.
