# Plan de acción tras cotejo X-Ray

Estado: EN CURSO. Fuente: commit `aa8fed0631913783c77d3b9ad3fcca62e1978c11`, los skills trasladados y las capturas adjuntas al chat. Este plan conserva los contratos literales: no los convierte en ejecución por aparecer en el repositorio.

## Cuatro pasadas y verificación cruzada

1. **Procedencia.** Los 30 documentos del enlace (27 contenidos distintos) y 82 skills se preservaron bajo `01-PLAN/`; 65 referencias, 5 diagramas y 12 capturas suman 82 PNG. Los hashes de las 12 capturas coinciden con los 12 adjuntos descargados de la conversación; las dos copias de la captura `052636` tienen el mismo SHA-256. La captura `093043` se añadió como `UI-EXTRA-017`. `AUDITORIA-4-PASADAS.json` conserva fuente, destino, SHA-256 y duplicados por archivo.
2. **Estructura.** La auditoría registra sintaxis comprobable de Python/JSON/YAML/JS/shell, integridad ZIP y encabezados del plan; 6 TSX siguen `🚩 PENDIENTE: TSX_NOT_PARSED`. Los 82 PNG pasan firma, dimensiones declaradas y hash. Un PNG legible no prueba que el texto de la captura sea verdadero.
3. **Integración.** `AUDITORIA-4-PASADAS-POST-CODE.json` registra 17 archivos de código y la prueba local del endpoint autenticado `/chat/org/visual-references`: verifica los 82 hashes y expone solo metadatos. `/chat/send` guarda el turno en SQLite vía fachada de memoria, lo vuelve a leer y aísla el scope por propietario. Los documentos y skills sin prueba de ejecución permanecen `🚩 PENDIENTE`; las imágenes son `REFERENCE_ONLY`. La captura de GPT-6 Sol prueba lo que muestra la pantalla, no el modelo interno de Devin.
4. **Evidencia.** 64 pruebas focalizadas pasan (27 del gate T07 simulado); las suites gate/DAG se solapan con esta selección. El verificador rechaza claims no tipados, hashes falsos y carpetas presentadas como archivos; el recibo de un reviewer debe identificar al actor correspondiente. El compilador produce IDs reproducibles y consultas tipadas, y el paquete de evidencia conserva hashes de contenido y URLs de hechos admitidos. El hash es una suma de control local, no una firma ni identidad autenticada de Sentinel, Hermes u OpenClaw. Un test de proveedores espera ocho entradas mientras `openai` figura tanto en el código como en la prueba de `origin/main`. Ruff del backend y los módulos T-11 modificados pasa. No hay respuesta OpenAI real, receipts de revisores externos, conexión runtime Graphiti/Graphify, restauración HF ni prueba visual completa; ninguna recibe `PASS`. La ruta organizativa exige Bitácora en GitHub y devuelve 503 sin esa escritura: la prueba aislada sustituye ese transporte, no lo certifica remotamente.

## Orden ejecutable

| ID | Entrada contractual | Acción y criterio de salida | Estado |
|---|---|---|---|
| X-01 | `T-11-02-PROGRAMACION-NUEVO-01-A-19.md` | Reusar parser, compilador y Puerta existentes: 12 instrucciones conocidas se clasifican de forma determinista, una orden ambigua/negada produce `UNKNOWN`, ninguna query y ningún PASS. Mapear los demás contratos, fanout y EvidencePacket antes de cerrarlo | PARCIAL; 🚩 PENDIENTE: RESTO T-11 |
| X-02 | `T-11-05-HANDOFF-TESTS-PASS-FAIL.md` | Claims falsos, hash incorrecto y reviewer actor suplantado se rechazan localmente; faltan recibos firmados o autenticados de actores externos, lease, replay, recovery y autoridad Judge | PARCIAL; 🚩 PENDIENTE: RESTO T-11 |
| X-03 | `T-11-I-01-SKILL-RUNTIME-SCHEMA-CODE.md` y catálogo de 82 skills | Separar `DOCUMENTATION_ONLY` de código ejecutable; registrar entrada, salida, hash, licencias y adapter Fables antes de activar un skill | 🚩 PENDIENTE |
| X-04 | `T-11-04-HUELLA-DIGITAL-ARCHITECTURE-XRAY.md` | Crear huella de componentes, rutas, tests y conectividad real; marcar `CONFIGURED` distinto de `ACTIVE` | 🚩 PENDIENTE |
| X-05 | Contrato T-12 de investigación sin LLM | Inspeccionar entrypoint del motor de búsqueda existente y ejecutar normalización/deduplicación con `LLM_CALLS=0`; no lanzar 20 búsquedas sin contrato verificado | 🚩 PENDIENTE |
| X-06 | Catálogos de 82 imágenes y Maxbry UI | Mantener metadata backend y roles individuales; revisar contenido visual, secretos y componentes frontend solo al cerrar backend | 🚩 PENDIENTE: VISUAL/FRONTEND |
| X-07 | Memoria Manus y `/chat/send` | Validar aislamiento, persistencia y read-back de SQLite; comprobar con evidencia independiente servicios externos y HF antes de `CONNECTED` | LOCAL VERIFICADO; 🚩 PENDIENTE: EXTERNOS |
| X-08 | T-11 cierre y T-06 | Ejecutar suite backend, comparar revisión publicada y probada, luego prueba desktop/tablet/móvil con segunda pasada; no desplegar todavía | 🚩 PENDIENTE |

El endpoint de referencias comprueba schema, conteo, IDs únicos, ruta y SHA-256; devuelve 503 ante JSON corrupto o entradas inválidas. Solo entrega metadatos; la validación visual independiente sigue 🚩 PENDIENTE.

Siguiente acción exacta: completar T-11-C con fanout de adaptadores autorizados, timeout por motor y observaciones tipadas de error; verificar que un fallo no invalida resultados de otros motores, antes de conectar más servicios. 🚩 PENDIENTE: demostrar identidad y ejecución independiente de los reviewers. GitHub Actions no se usa para esta validación.
