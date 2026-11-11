# HANDOFF — 📂 memoria/ (almacenamiento y memoria)

Fecha: 2026-11-09 · Estado: RECEPCIÓN · Ramas: `main` (raíz y documentos), `ccr-f01c3de9-bmry0s` (código de Router 1).

## 1. Qué hay en la raíz

Ver `README.md`. La raíz es `Memoria/`. No se crea una raíz `memoria/` de primer nivel: la organización R-4 pone cada grupo dentro de `chat-router/`.

## 2. Qué se verificó

- Memoria en uso: `chat-router/chat/backend/mvp/memoria.py` (JSON por scope en bucket HF). Verificado.
- Tools del Harness: `chat-router/chat/backend/deepseek_harness/server.py`. Verificado.
- Motor multi-backend `memoria-yaiwes/`: sin importadores fuera de sus pruebas. Verificado.
- Endpoints de Graphiti, Memanto, Graphify y Qdrant: ausentes en `connections/endpoints.yaml`. Verificado.
- Qdrant local: ruta antigua `04-MEMORIA`. Verificado.
- `sqlite_memory.py` (rama de Router 1): sin consumidores. Verificado.

## 3. Lo recibido y no verificado

Ver `ANEXO_INPUT_BLOCK.md`. Resumen de flags:
- 🚩 Fuentes con URLs de terceros sin verificar; algunas incluyen parámetros de rastreo (`utm_source`) y deben limpiarse antes de usarse.
- 🚩 Un mismo contenido aparece duplicado en dos archivos (Wordflow y Resumen OSQUESTADOR).
- 🚩 Cifras de referencia no verificadas: 314 o 323 herramientas MCP en Ruflo; commit `cdd5308` (v3.10.2); "20 millones de contexto".
- 🚩 Contradicción: un documento propone eliminar Graphiti y Graphify y otro propone absorber sus ideas. Hay que decidir una sola postura.
- 🚩 El archivo `66a1c977-Sistema_de_almacenamiento_y_memoria_Yaiwes.md` no se leyó en esta vuelta.

## 4. Gaps técnicos heredados

- G-MEM-1 Dos fuentes de verdad (bucket HF y SQLite de `memoria-yaiwes`).
- G-MEM-2 Componentes vendorizados sin endpoint ni activación.
- G-MEM-3 Ruta obsoleta de Qdrant.
- G-MEM-4 `search` del Router devuelve la clave `"sqlite"` sin consultar SQLite.
- G-MEM-5 `sqlite_memory.py` sin consumidores.
- G-MEM-6 Pruebas J09, J10 y J11 pendientes.

## 5. Preguntas abiertas (para cerrar antes de implementar)

1. ¿Cuál es la fuente de verdad única: bucket HF, SQLite de `memoria-yaiwes`, o SQLite con el bucket como respaldo?
2. ¿Qué componentes se activan (Graphiti, Memanto, Graphify, Qdrant) y con qué servicios?
3. ¿Eliminamos Graphiti y Graphify, o los integramos como ideas en el motor nativo? (Son posturas incompatibles en los documentos recibidos.)
4. ¿`sqlite_memory.py` se conecta al bucket, va a cuarentena, o se borra?
5. ¿Autorizas leer el archivo `66a1c977…` en la siguiente vuelta?
6. ¿Quién ejecuta el frente: Claude Code 4, o un Claude nuevo (5) como indicaste antes? Queda pendiente.

## 6. Pruebas que deben pasar antes de cerrar

- [ ] Pruebas existentes de `memoria-yaiwes` (`test_memoria_yaiwes.py`, `test_memoria_real.py`).
- [ ] `test_memoria.py` del router.
- [ ] Guardar y leer desde otra sesión (persistencia real).
- [ ] Qdrant con ruta válida.
- [ ] Prueba en vivo con llave (🚩 mientras no haya llave).
