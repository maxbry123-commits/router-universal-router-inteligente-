# INSTRUCCIONES PARA DEVIN — Selector de 11 modos + router (edición quirúrgica)

Paquete **nuevo y aditivo**. No reescribe nada de los archivos anteriores (`loop_contract.*`, `validate_contract*.py`). Se apoya en ellos: `modes_registry.json` declara `extends_contract: loop_contract.example.v1_1.json`.

## 0. Reglas de la intervención (obligatorias)

1. **Aditivo y reversible.** Cada inserción en archivos existentes va entre marcadores `>>> MODOS BEGIN` / `<<< MODOS END`. Rollback = borrar lo que está entre marcadores.
2. **No reescribir ni reformatear** archivos del chat. Solo insertar o envolver.
3. **Un módulo, una autoridad.** El backend (`mode_router.py`) decide el modo. El front solo propone.
4. **Cero cableado nuevo.** El botón usa el mismo payload, el mismo endpoint, el mismo bus de eventos y el mismo cargador de fichas que el chat ya usa.
5. **Fail-closed.** Modo desconocido o fuente inválida = error 400, nunca caer en silencio a otro modo.
6. **Evidencia.** No declares terminado sin la salida real de los comandos de la sección 8.

## 1. Archivos del paquete y dónde van

| Archivo | Destino sugerido | Capa |
|---|---|---|
| `modes_registry.json` | `config/` (junto a las fichas JSON del modelo) | datos |
| `research_sources.json` | `config/` (misma carpeta) | datos |
| `mode_router.py` | backend, junto al módulo que carga las fichas | backend |
| `validate_modes.py` | misma carpeta que `mode_router.py` (se importa) | backend |
| `mode_selector.js` | carpeta de scripts/componentes del front | front |
| `test_mode_router.py`, `check_integration.py` | `tests/` o raíz | verificación |

`modes_registry.json` **es** la ficha del router: cualquier cambio de modos se hace ahí, sin tocar código.

## 2. Mapa de tu pantalla de 4 puntos → los 11 modos

| Tu lista inicial | Modo |
|---|---|
| 1. Respuestas normales rápidas | `m05_respuesta_rapida` |
| 2. Arquitectura y proyecto | `m01_plan` |
| 3. Objetivo siempre presente | `m02_objetivo` (y el paso `pin_objective` en todos los modos con objetivo) |
| 4. Agéntico en loops hasta terminar | `m04_agentico_loop` |

Los modos 3, 6 a 11 de tu segunda lista son los nuevos: investigación, orquestador, tool, auto-evolución, Mythos, agenda, max paralelo.

## 3. Los 11 modos (fuente de verdad: `modes_registry.json`)

| Modo | Slash | Qué hace | Autónomo | Auto-elegible |
|---|---|---|---|---|
| m01_plan | `/plan` | Plan y arquitectura; entrega DAG, no ejecuta | no | sí |
| m02_objetivo | `/objetivo` | Investiga, crea recursos, diseña, ejecuta, prueba, entrega | sí | no |
| m03_investigacion | `/investigar` | Recorre las 20 fuentes, extrae métodos y luego planifica | no | sí |
| m04_agentico_loop | `/agentico` | Bucle de código y frontend hasta terminar todas las tareas | sí | no |
| m05_respuesta_rapida | `/rapido` | Respuesta directa, sin tools ni bucle | no | sí |
| m06_orquestador_pool | `/orquestador` | Delega a modelos y agentes; no escribe código (pool de 4) | sí | no |
| m07_tool | `/tool` | Ejecuta tools y devuelve el resultado tal cual | no | sí |
| m08_auto_evolucion | `/evolucion` | Audita su ficha, backend y frontend; corrige en rama; abre PR | sí | no |
| m09_mythos | `/mythos` | Investiga antes de cada paso; hasta 10 ciclos hasta cerrar gaps | sí | no |
| m10_agenda | `/agenda` | Prioridades, input verbatim, verificación cruzada, colas, watchdog | no | sí |
| m11_max_paralelo | `/paralelo` | Hasta 10 tareas a la vez; el excedente va a cola | sí | no |

Regla de seguridad: **un modo autónomo solo se activa por botón o slash**, nunca por el clasificador automático. Así una frase suelta no dispara un bucle de horas.

## 4. Flujo completo (el mismo cableado del chat)

```
[Botón "Modo"] ──► mode_request {mode_id, source:"button"}   (dentro del MISMO payload del mensaje)
[/slash en texto] ─┐
[Auto] ────────────┴─► mismo endpoint de chat
                          │
                          ▼
        route_request()  (mode_router.py)   precedencia: botón > slash > auto > default
                          │  emite mode_resolved por el bus de eventos existente
                          ▼
        ficha_modo = {system_block, reasoning, tool_choice, tools, pipeline, limits, parallel, ...}
                          │
        ┌─────────────────┴──────────────────┐
        ▼                                    ▼
 tu ensamblador de prompt              ¿autonomous_loop?
 (agrega system_block)                  sí → controlador de bucle (contrato v1.1) con limits del modo
                                        ¿parallel.enabled? → ParallelPool (≤10, resto en cola)
```

## 5. Ediciones quirúrgicas (puntos de contacto)

No conozco tu código, así que **no hay números de línea**. Ubica cada ancla con `grep`, edita solo ahí y envuelve con marcadores.

### Punto A — Front: montar el botón
- **Ancla:** barra del compositor donde están los botones `+` y `/` (el icono `/` indica que ya hay slash commands).
- **Buscar:** `grep -rniE "composer|toolbar|slash|chat-input|send-button" src/`
- **Insertar** un contenedor al lado del `/` y llamar a `initModeSelector`:

```html
<!-- >>> MODOS BEGIN -->
<div id="mode-selector-mount"></div>
<!-- <<< MODOS END -->
```
```js
// >>> MODOS BEGIN
import { initModeSelector } from "./mode_selector.js";
const modeUI = await initModeSelector({
  mountEl: document.getElementById("mode-selector-mount"),
  registryUrl: "/config/modes_registry.json",   // sirve el JSON como estático o por tu API de fichas
  conversationId: currentConversationId,         // variable que el chat YA tiene
  composerEl: document.querySelector("<SELECTOR_DEL_TEXTAREA>"),
  thinkingToggleEl: document.querySelector("<SELECTOR_DEL_ICONO_CEREBRO>"),
});
// <<< MODOS END
```

### Punto B — Front: envolver el envío
- **Ancla:** la función que arma el body del POST del mensaje. **Buscar:** `grep -rniE "fetch\(.*chat|sendMessage|submitMessage|postMessage" src/`
- **Envolver** esa función; no cambiar su cuerpo:

```js
// >>> MODOS BEGIN
const sendMessage = modeUI.wrapSend(sendMessageOriginal);
// <<< MODOS END
```
Resultado: el payload original más `mode_request: {mode_id, source}`.

### Punto C — Front: interruptor de thinking (cerebro)
Ya pasa por `thinkingToggleEl` en el punto A. En modos autónomos el interruptor queda deshabilitado («controlado por el modo activo»). Motivo: política `mode_wins`; un thinking global activado no debe pisar `execute: none` de los modos de bucle.

### Punto D — Backend: entrada del endpoint
- **Ancla:** el handler de chat, antes de elegir/cargar la ficha. **Buscar:** `grep -rniE "def .*chat|/api/chat|load_ficha|get_ficha|ficha" backend/`

```python
# >>> MODOS BEGIN
from mode_router import load_registry, route_request, ModeError
MODOS_REG = load_registry("config/modes_registry.json", strict=True)  # una vez, al arrancar
# <<< MODOS END

# dentro del handler, ANTES de cargar la ficha:
# >>> MODOS BEGIN
try:
    routed = route_request(MODOS_REG, payload,
                           objective=leer_objetivo_fijado(payload),   # None en el primer turno
                           emit=emit_event)                            # tu bus de eventos existente
except ModeError as e:
    raise HTTPException(status_code=400, detail={"code": e.code, "detail": e.detail})
payload["message"] = routed["message"]        # ya sin el /slash
ficha_modo = routed["ficha"]
# <<< MODOS END
```
`leer_objetivo_fijado` lee `state/objective.md` (parseado a dict con `goal, done_when, constraints, out_of_scope, deliverables`). En el primer turno devuelve `None`: el paso `pin_objective` lo crea y desde la siguiente iteración se reinyecta.

### Punto E — Backend: ensamblar la solicitud al modelo
- **Ancla:** donde hoy se agrega el texto de la ficha al prompt y se arma el request al modelo.
- **Insertar justo después**, sin quitar nada:

```python
# >>> MODOS BEGIN
req["messages"] = [{"role": "system", "content": ficha_modo["system_block"]}] + req["messages"]
fase = fase_actual or "execute"                       # plan | execute | verify (lo fija el controlador de bucle)
req["reasoning_effort"] = ficha_modo["reasoning"][fase]   # mapea al campo REAL de tu proveedor
req["tool_choice"] = ficha_modo["tool_choice"][fase]
if ficha_modo["tools"] != ["registered_tools"]:
    req["tools"] = [t for t in req.get("tools", []) if t["name"] in ficha_modo["tools"]]
# <<< MODOS END
```
- `prompt_import_slot`: aquí vas a conectar los prompts de Fable/Devin que conviertas a JSON. Si el campo de un modo trae una ruta, concatena ese contenido **después** del `system_block`. Está en `null` en todos.
- Si `tool_choice` es `required`, el registro ya exige `reasoning: none` para esa fase (el validador lo comprueba).

### Punto F — Backend: lanzar bucle y pool
```python
# >>> MODOS BEGIN
if ficha_modo["autonomous_loop"]:
    iniciar_bucle(contrato="loop_contract.example.v1_1.json",
                  base_mode=ficha_modo["base_mode"],
                  limits=ficha_modo["limits"],          # topes duros del modo
                  pipeline=ficha_modo["pipeline"])
if ficha_modo["parallel"]["enabled"]:
    from mode_router import ParallelPool
    pool = ParallelPool(max_running=ficha_modo["parallel"]["max_running"], on_event=emit_event)
# <<< MODOS END
```
`iniciar_bucle` es tu controlador existente o el que implementes sobre el contrato v1.1 ya entregado.

### Punto G — Trazabilidad
Eventos que debes dejar pasar por **tu mismo bus**: `mode_resolved`, `objective_pinned`, `step_started`, `step_passed`, `step_failed`, `cycle_started`, `cycle_closed`, `task_queued`, `task_started`, `task_blocked`, `watchdog_stall`, `limit_reached`, `terminal` (lista en `registry.events`). El folio sigue el formato del contrato (`LOOP-{YYYYMMDD}-{seq}`).

## 6. Cómo trabajan los modos clave

- **Objetivo siempre presente.** Todo modo con objetivo empieza con `pin_objective`: escribe `state/objective.md` con `goal, done_when, constraints, out_of_scope, deliverables`. `validate_objective()` lo rechaza si falta algo. `system_block` lo reinyecta en cada iteración para que el modelo no se desvíe.
- **Mythos (`m09`).** Cada ciclo hace `research_before_step → execute_dag_loop → run_tests → detect_gaps`, máximo 10 ciclos, hasta que `state/gaps.json` quede vacío. Sobre «OpenMythos»: es una reconstrucción teórica y comunitaria en PyTorch de una arquitectura de modelo (transformer recurrente), sin relación con Anthropic. **No es un flujo de agente ni algo que se pueda "usar" desde el chat.** Lo que implementé es el comportamiento que describiste (investigar antes de cada paso y mejorar en ciclos). Si querías otra cosa, dímelo.
- **Auto-evolución (`m08`).** Solo en ramas `self-evolve/*`, cambios aditivos, PR sin merge automático, pruebas en verde obligatorias. Las secciones `selector.gate`, `hard_limit_caps`, `self_modification` e `immutable_sections` son inmutables: `immutable_violations(viejo, nuevo)` detecta cualquier intento de aflojarlas. Sin esto, un modo que se edita a sí mismo podría quitarse sus propios límites.
- **Agenda (`m10`).** «Verbartin» lo interpreté como *verbatim*: guarda tu input original sin modificar (con sha256), y la verificación cruzada exige que cada tarea se trace a un fragmento del input y viceversa. Si no era eso, avísame.
- **Max paralelo (`m11`) y Orquestador (`m06`).** `ParallelPool`: hasta 10 en ejecución, el resto en cola por prioridad, watchdog por tarea (timeout → reintento → `blocked_with_evidence`). El orquestador nunca tiene `edit_file` ni `bash` (lo valida el registro).
- **Investigación (`m03`).** Usa `research_sources.json` (20 fuentes: GitHub, Hugging Face y su foro, Stack Overflow, HN, Reddit, dev.to, Lobsters, arXiv, ingeniería de Anthropic, docs de LangChain, LlamaIndex, Haystack, Chroma, Qdrant, OpenAI cookbook, blogs de expertos, Stack Exchange, PyPI). Una fuente caída no detiene el modo: se registra en `state/research_failed.md`, con mínimo de 8 exitosas.

## 7. Qué sigue limitado (por diseño)

«Sin escalar y sin parar» está implementado como **no pedir ayuda y no detenerse hasta terminar**, pero con topes duros (`hard_limit_caps`: 1000 iteraciones, 24 h, 300 USD, 10 en paralelo, 10 ciclos). Si se alcanza un tope, el modo termina con reporte. Súbelos si quieres; no los quites. Un bucle sin tope es un bug que gasta dinero sin límite.

## 8. Verificación (Devin debe pegar la salida real)

```bash
# 1) Registro y fuentes válidos
python3 validate_modes.py modes_registry.json research_sources.json
# 2) Después de llenar self_modification.targets (reemplazar los <EDITAR ...>)
python3 validate_modes.py --strict
# 3) Router, precedencia, pool y límites (19 pruebas)
python3 -m unittest test_mode_router -v
# 4) Integración aplicada en el repo del chat
python3 check_integration.py /ruta/al/repo-del-chat
# 5) Contrato base sigue en verde (no debe cambiar)
pip install jsonschema && python3 validate_contract_v11.py loop_contract.example.v1_1.json
```

Criterios de aceptación manuales:
1. Botón visible junto al `/` y al cerebro, con la lista de 11 modos + Auto.
2. Elegir «Objetivo» y mandar «hola»: el request lleva `mode_request.mode_id = m02_objetivo`, `source = button`, y el evento `mode_resolved` aparece en la traza.
3. Escribir `/rapido ¿qué hora es en Tokio?` sin botón: modo `m05`, el texto llega sin el `/rapido`.
4. Mandar `mode_id: "m99"` por la API: responde 400 `UNKNOWN_MODE`.
5. En modo Max Paralelo con 25 tareas: nunca más de 10 en ejecución y 15 en cola.
6. Con un modo autónomo activo, el interruptor de thinking aparece deshabilitado.

## 9. Lo que NO verifiqué (honestidad)

- No vi tu código: los anclas son patrones de búsqueda, no líneas exactas. Los nombres `leer_objetivo_fijado`, `emit_event`, `iniciar_bucle`, `fase_actual`, `req` son marcadores que Devin debe mapear a los reales.
- Probé: validador del registro, 19 pruebas del backend (precedencia, rechazo de modos inválidos, pool, topes, inmutables) y el módulo JS con un DOM simulado. **No lo probé en un navegador real ni contra tu chat.**
- La validación por esquema del contrato v1.1 necesita `jsonschema` (no pude instalarlo aquí).
- Las 20 fuentes son una lista semilla elegida por criterio, no medida por tráfico ni verificada en vivo.
- Los nombres de campos del proveedor (`reasoning_effort`, `tool_choice`) pueden diferir en tu API; mapea al real.
