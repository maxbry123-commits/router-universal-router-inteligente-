# CHAT 3 — Canvas YAIWES (mapa mental / DAG)

## Ubicación y alcance
La vista independiente `chat/frontend/canvas-map.html` se abre desde el botón **Mapa mental / DAG** del Canvas multimedia existente. No sustituye `canvas-visor.js`, no crea otra infraestructura y no modifica los controles LOOP/Cola/Watchdog del frontend.

## Flujo real
`panel-canvas.js` → `canvas-map-entry.js` → iframe del mismo origen `canvas-map.html` → `window.RIU_PLUGIN('nct_loop', accion, payload)` → `app.py` (autenticación existente) → `loop_puente.llamar_canvas` → `nct_loop/canvas_bridge.py` → `canvas_graph.py`.

Las acciones permitidas son `canvas_validate`, `canvas_from_dag`, `canvas_save`, `canvas_load`. El frontend no recibe secretos ni ejecuta herramientas del LOOP. Se usan contratos de grafo tipado y las reglas de evidencia de `canvas-graph.schema.json`.

## Persistencia
Guardar utiliza `memoria.aplicar("save")` y el proveedor HF ya existente. Recuperar y el read-back posterior al guardado consultan `hf_store.leer` directamente. El resultado `verified:true` solo se entrega cuando coincide la revisión y la huella SHA-256 del contenido releído.

## Verificación
`python -m unittest discover -s "chat-router/Loop cola wachdog/Loop/tests" -p test_canvas_graph.py -v` — 13 tests de contrato y callbacks (no certifican el servidor externo).
`node --check chat-router/chat/frontend/canvas-map.js` y `node --check chat-router/chat/frontend/canvas-map-entry.js`.

## Limitaciones declaradas
- No implica ejecución de agentes, ni verificación material de `evidence_refs` aportadas por JSON externo.
- `expected_revision` no es un CAS distribuido; evitar escritores concurrentes para un mismo grafo.
- El paso a producción requiere smoke HTTP autenticado, lectura fresca desde HF y regresión visual en navegador real.
- El estado inicial de la interfaz es **EJEMPLO LOCAL** y no se presenta como resultado remoto.

Se conserva todo dentro de la raíz actual `chat-router/`.
