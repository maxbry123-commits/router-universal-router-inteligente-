# INTEGRATION_LOG — modos del router (fase 1)

## Anclajes encontrados (grep)

- `panel-chat.html` — `composer-bar` (`.row.composer-bar`) contiene los botones; montaje `#mode-selector-mount` entre `btn-copiar-input` y `btn-detener`.
- `panel-chat.js` — envío real: `window.RIU_HARNESS(...)` (siempre, `CFG.harnessUrl` fijado en api.js); `body` solo se usa en el fallback `api("/chat/send")`.
- `api.js` — `harness()` arma `extra` (línea ~181); el objeto `qwen` viaja dentro del payload al puente → fichas_qwen.
- `fichas_qwen/plugin.py` — `_chat(p)`: `mode_request` resuelto solo si `p["mode_request"]` presente o slash `/m…` al inicio; respuesta añade `modo` cuando resolvió.
- `fichas_qwen/mvp.py` — `_modo` entra por `p["_modo"]`; system_block al frente de `conv`; reasoning → `extra_llm`.

## Decisiones

- Copias byte-exactas de los archivos del paquete (fichas/*.md renombrados a su tipo real). Lo que faltaba se escribió mínimo: `--check-state` en `validate_contract.py` (test lo exigía).
- `modes_registry.json` también copiado a `chat frontend/` porque el selector lo sirve estático `/chat/ui/modes_registry.json`; el del paquete (`modos/`) es el canónico del backend. TODO: servir uno solo o sincronizar.
- `route_request` NO corre en cada mensaje: solo si `mode_request` presente o slash de modo inicial — `/ayuda`, `/aprobar` y tráfico legacy quedan intactos.
- `qwen.mode_request` duplicado a nivel payload: garantiza llegada a fichas_qwen sea cual sea el merge del puente.
- Punto F (bucle DAG real): RESUELTO — acción `loop_run` en `fichas_qwen.handle`: carga contrato (dict o archivo del paquete), instancia `LoopController` con ejecutor que corre cada nodo por `pc._chat` (mismo banco/tools/memoria que las fichas), `objective_path` apuntando a `state/objective-{ses}.md`. `ficha.json`: `loop_run` añadido a `allowed_actions` y `timeout_ms` 30000→120000 (tope host 120 s; un DAG con modelos reales necesita más). Verificado en vivo: contrato de 1 nodo → `state: DONE`, `promise_token <<TODO_COMPLETO>>`, nodo `passed` con evidencia. El `_correr` existente sigue para la ruta async; `loop_run` es el controlador por contrato.

## Mapeos de nombres

- `leer_objetivo_fijado` → `_modos_objetivo(ses)` (`state/objective-{ses}.md`)
- `emit_event` → `_modos_emit` (append `state/events.jsonl`)
- `iniciar_bucle` → `_correr` existente (DAG del plugin)
- `fase_actual` → "execute" fuera del bucle
- `req`/`extra_llm` → payload de `pc._chat` vía `_EXTRA_LLM` ContextVar

## Evidencia

- `python3 -m unittest discover -p 'test_*.py'` en modos/ → 49/49 OK
- `python3 check_integration.py <repo>` → VEREDICTO: PASS (5 archivos, backend+frontend con bloques balanceados)
- `node --check` panel-chat.js / api.js / mode_selector.js → OK; `py_compile` plugin.py / mvp.py → OK
