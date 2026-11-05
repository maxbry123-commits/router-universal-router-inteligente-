# Continuidad de generación por secciones — propuestas aprobadas

Alcance aprobado por Antonio: aplicar los puntos 1–6 y 8–10 de A1, excluyendo el punto 7 (temperatura baja/seed fijo). Se incorporan además las reglas simples de corte, cambio de proveedor y reanudación tras caída.

## Requisitos de continuidad

1. **Prefill de reanudación:** al retomar una generación, enviar como mensaje `assistant` parcial el último fragmento confirmado, para que el modelo continúe en vez de reiniciar.
2. **Continuación automática:** si `finish_reason=length`, continuar desde el último punto confirmado. Si `finish_reason=stop` pero no se detecta el cierre esperado, continuar/reintentar esa sección.
3. **Índice primero:** generar primero un índice numerado; después generar cada sección mediante una llamada independiente.
4. **Centinela por sección:** cada sección termina con `<<FIN_SECCION_n>>`. Si falta o no coincide con el número de sección esperado, volver a solicitar únicamente esa sección.
5. **Unión sin duplicados:** al combinar fragmentos, detectar y eliminar líneas duplicadas en el solapamiento entre fragmentos, preservando el orden y el contenido único.
6. **Contexto compacto de reanudación:** enviar un resumen breve y las últimas aproximadamente 50 líneas literales; no reenviar todo el historial.
7. **Checkpoint validable:** persistir cada fragmento como una operación equivalente a `write_chunk`, con número de sección, punto de continuación y estado de validación.
8. **Selección de modelo por capacidad real:** elegir proveedor/modelo según su límite efectivo de `max_completion_tokens`; incluir Groq y NVIDIA/Muse en la comprobación y no asumir que el límite declarado equivale a salida utilizable.
9. **Validación y reparación selectiva:** al finalizar, ejecutar parser/linter y validaciones de cierre; si algo falla, regenerar solo las secciones afectadas, sin rehacer las aprobadas.

## Reglas operativas simples

- Cortar la salida cada 200 líneas, guardar el checkpoint y solicitar otra continuación.
- Al reanudar, indicar explícitamente: **«Sigue desde la línea N»**, junto con el checkpoint y el contexto compacto.
- Si Groq falla o se agota, continuar con NVIDIA desde el mismo punto guardado; no reiniciar el documento ni descartar fragmentos validados.
- Si se cae el chat, exponer una acción **«Retomar»** que continúe automáticamente desde el último checkpoint válido.

## Exclusión expresa

No aplicar el antiguo punto 7 de A1: no imponer temperatura 0–0.3 ni seed fijo. Este documento registra el alcance aprobado; no acredita que el comportamiento esté implementado en el runtime.
