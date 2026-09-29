# T-07 — Skills convertidas al esquema Sheriff / DSL DAG
**Estado:** PENDIENTE · **Depende de:** T-05 · **Nodo:** N-07

## Qué es, en palabras simples
Tomar las skills que tú indicaste (ECC de `affaan-m/ECC`, Archify, Agent Skills, Ponytail) y dejarlas en el mismo formato de tareas que usa todo el sistema (esquema Sheriff / DSL DAG), para que los agentes las lean igual.

## Cómo se hace
1. Bajarlas SOLO con el motor de descarga y extracción (nunca a mano).
2. Por cada skill: qué hace, qué recibe, qué entrega, cómo se comprueba (formato DAG).
3. Guardarlas dentro de la raíz del chat, en su carpeta de skills.
4. Registrar en la bitácora cuáles se convirtieron y cuáles no.

## Listo cuando
Cada skill tiene su ficha en formato DAG y una prueba que la carga sin error.

## No hacer
Inventar qué es "Prompt Master": no está verificado; se busca en `Documentos del proyecto/Notas del Director (verbatim)/` y, si no aparece, se te pregunta.
