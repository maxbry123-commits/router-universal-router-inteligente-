# INPUT BLOCK VERBATIM — Director — 2026-09-29 — PARTE 4
Continuación de `INPUT-BLOCK-VERBATIM-2026-09-29-director.md` (02:06 y 02:35), `…-parte-2.md` (03:26, 03:27 y 04:41) y `…-parte-3.md` (05:15).
Copia textual, sin corregir ortografía ni orden, copiada del mensaje recibido (no de memoria). Zona horaria Bogotá.

---
## BLOQUE 6 — Mar 2026-09-29 05:18 (Bogotá) — mensaje enviado mientras Claude trabajaba

Una sugerencia adicional para evitar errores una vez que hagas una salida cuando termines haces 3 bucles de revisión de todo verificación cruzada con el code fuente y los archivos y las instrucciones 4 pasadas por tarea terminada sin eso no está 100 pass ✅

Si continúa

---
## Cómo lo aplica Claude (interpretación de Claude, NO texto del Director)
Esta sección es de Claude y se puede corregir. Regla fija desde las 05:18, para TODA tarea de los Bloques 1, 2 y 3:

1. Una tarea NO puede marcarse ✅ VERIFICADO sin dejar en el handoff, por tarea, la evidencia de 4 pasadas de revisión:
   - Pasada 1 — instrucciones: releer el mensaje textual del Director (archivos `INPUT-BLOCK-VERBATIM-*`) y comprobar punto por punto que lo pedido está hecho (o anotado 🔴 PENDIENTE con motivo).
   - Pasada 2 — código fuente: releer el código real modificado (no el recuerdo de lo escrito) y cruzarlo con el resto del código que lo llama o lo usa (buscar quién usa cada función cambiada).
   - Pasada 3 — archivos y documentos: comprobar que handoff, bitácora, notas en rojo y arquitectura dicen lo mismo que el código (nada afirmado que no exista, nada existente que no esté anotado).
   - Pasada 4 — ejecución: pruebas corridas de verdad (antes/después) y, cuando se pueda, prueba en vivo; el resultado se copia tal cual (número de run, cuántas pasan y cuáles fallan), no se resume.
2. "3 bucles": esas pasadas se repiten como bucle (revisar → corregir → volver a revisar) hasta que 3 vueltas seguidas de todo el bloque no encuentren nada nuevo. Lo que se encuentre en cada vuelta se anota (qué se halló y qué se cambió), incluso si es pequeño.
3. Marcadores: ✅ VERIFICADO solo con las 4 pasadas y los 3 bucles hechos; 🟡 HECHO SIN PROBAR si falta alguna; 🔴 PENDIENTE si no se hizo; ⛔ BLOQUEADO si depende de algo externo.
4. Sin esto, la tarea no está al 100 %, aunque el código exista y las pruebas pasen.
