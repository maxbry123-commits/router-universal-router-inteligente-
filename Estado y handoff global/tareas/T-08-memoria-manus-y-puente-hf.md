# T-08 — Memoria de Manus y puente con Hugging Face
**Estado:** PENDIENTE · **Depende de:** T-06 · **Nodo:** N-08 · **Paso P3**

## Qué es, en palabras simples
Que el sistema recuerde entre sesiones: la memoria de Manus guarda y el puente la copia a un lugar privado en Hugging Face para que no se pierda.

## Dónde estamos
- Existe el dataset privado `COMAND-CENTER-1/yaiwes-hf-memoria` (verificado 2026-09-29).
- El Router ya monta rutas `/memoria/*`.
- El código de memoria vive en `chat router/04-MEMORIA/`.
- Falta el puente (SQLite → dataset) y el enlace del chat de Manus (pendiente tuyo).

## Cómo se hace
1. Confirmar con una prueba qué hace hoy `/memoria/*`.
2. Conectar la memoria de Manus al Router único.
3. Puente: copiar la base SQLite al dataset privado con el token de escritura de HF (solo su nombre en el repo).
4. Probar: escribir un dato, relanzar, leerlo.

## Listo cuando
Un dato escrito sobrevive a un relanzamiento del Router y aparece en el dataset.

## Pendiente tuyo
El enlace del chat de Manus.
