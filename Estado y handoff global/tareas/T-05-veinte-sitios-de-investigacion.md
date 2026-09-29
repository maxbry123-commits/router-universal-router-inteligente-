# T-05 — 20 sitios de investigación en el motor de búsqueda
**Estado:** PENDIENTE · **Depende de:** T-02 · **Nodo:** N-05

## Qué es, en palabras simples
Los agentes revisan una lista fija de 20 sitios al empezar una tarea (para no inventar) y al terminar reportan los "Gaps" (lo que no encontraron o no cuadra).

## Cómo se hace
1. Abrir el archivo de arquitectura del Director (`81c6cdbf-arquitectura_chat_agentes___NO_TOCAR_________.md`, dentro de `Documentos del proyecto/`) y ver si ya lista los 20 sitios.
2. Si los lista: copiarlos tal cual a las fuentes del motor de búsqueda.
3. Si no: proponerte los 20 mejores (con motivo de cada uno) y esperar tu visto bueno antes de añadirlos.
4. Añadirlos al archivo `sources.json` del motor (hoy tiene 12) dentro de `Motores descarga extracción búsquedas/`.
5. Conectar: al iniciar una tarea el agente consulta el motor; al terminar escribe el reporte de Gaps.

## Listo cuando
`sources.json` con los 20 sitios y una prueba del motor (`riu-websearch.yml`) que devuelva resultados de ellos.

## No hacer
Elegir los sitios sin decirte cuando el archivo no los trae. Usar el buscador para descargar: las descargas van solo por el motor de descarga y extracción.
