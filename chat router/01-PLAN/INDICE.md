# Índice canónico del plan

La fuente del plan de 100 pasos es `PLAN.json`; continúa en recepción y no se inicia el reloj sin fuente verificable. Las entradas literales del Director se conservan sin edición, y los documentos T-11/T-12 se han agrupado sin cambiar sus bytes.

| Área | Ubicación | Estado |
|---|---|---|
| T-01..T-10 y plan original | `PLAN-DSL-DAG-00-CONTRATO.yaml`, `PLAN-DSL-DAG-01-NODOS.yaml`, `PLAN-DSL-DAG-UI.yaml`, `PLAN.json` | Canónico |
| T-11 | `T-11/` | Contratos y entradas literales; depende de T-10 |
| T-12 | `T-12/` | Especificación pendiente de ejecución |
| Anexos originales | `ANEXOS/` | Fuentes adicionales conservadas sin alterar sus bytes |
| Método aprobado | `PROPUESTA-METODO-DEVIN-ASK-COUNCIL.md`, `DM-METODO-DAG.json` | Política estructurada y gate verificable |
| Diseño | `ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md`, `REFERENCIAS-UI/`, `CATALOGO-REFERENCIAS-UI.json` | Referencias; T-06 pendiente de prueba completa |
| Inventario T-06 | `T-06-INVENTARIO.md` | Controles y estados enumerados; resultados requieren prueba real en navegador |
| Motor reutilizable | `../../Motores descarga extracción búsquedas/➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/📂Motor descarga de componentes y extracción de zip/` | Fuente examinada, no conectado en vivo |

## Regla de reuso previa a cada tarea

1. Identificar capacidad y buscar primero en componentes ya descargados y en código existente; si no basta, investigar alternativas abiertas hasta hallar un candidato que cubra la tarea. La autorización de descargar hasta 100 componentes no es objetivo de volumen.
2. Registrar fuente, licencia, commit de origen, hash, interfaz, permisos, pruebas y riesgo de mantenimiento. Una descarga no demuestra conexión.
3. Usar el motor de descarga/extracción con read-back en modo sin publicación; su variante actual de publicación hace `push` a la rama configurada, por lo que no se ejecutará contra `main`. Inspeccionar historial y adaptar antes de habilitar publicación segura en rama de trabajo.
4. Aplicar Sheriff, adaptación mínima por el harness DeepSeek existente o el validador Fables cuando proceda, pruebas y receipt de operación; si falta un punto, marcar GAP.

En esta fase no se descargó ningún componente nuevo: la auditoría, el catálogo y la UI reutilizan código, contratos, skills y librerías ya presentes.

## Estado de implementación

`11-EVIDENCIA/auditoria_metodo.py` consume `DM-METODO-DAG.json`, valida la política y emite etiquetas `AUDIT-*`, 12 goals, 12 preguntas asesoras, huecos y veredicto con recibos verificables. La presencia del esquema no ejecuta Hermes ni OpenClaw; sin receipts de esos revisores las áreas críticas quedan `INCOMPLETE`. `CATALOGO-REFERENCIAS-UI.json` clasifica individualmente 65 imágenes conservadas por `git mv`; ninguna se sirve como asset de producto hasta revisión de secretos y segunda pasada T-06.
