# PROMPT PARA PEGAR A DEVIN

Copia todo lo que está debajo de la línea y pégalo como tarea.

---

## TAREA: integrar el selector de 11 modos, el router y el bucle en el chat

**Repositorio:** el repo del chat. **Rama:** crea `feat/modos-router` desde la rama principal.

**Material:** la carpeta del paquete (`router-loop/`). Léelos en este orden: `INSTRUCCIONES_DEVIN_MODOS.md`, `INSTRUCCIONES_ADICIONALES.md`. Son tu especificación.

### Reglas (no negociables)

1. Cambios **aditivos y reversibles**. Todo lo que insertes en archivos existentes va entre los marcadores `>>> MODOS BEGIN` y `<<< MODOS END` (con la sintaxis de comentario del lenguaje).
2. **No reformatees ni reescribas** archivos existentes. No renombres nada. No toques estilos ni lógica ajena.
3. **No inventes** líneas ni nombres. Ubica cada ancla con `grep` y pega la salida del `grep` en `INTEGRATION_LOG.md`. Si hay varios candidatos, elige el que está en el camino principal de envío de mensajes y anota por qué. Si no hay ninguno, pega exactamente lo que devolvió el `grep` y detente en ese punto.
4. **No modifiques** `hard_limit_caps`, `selector.gate`, `selector.on_unknown_mode`, `self_modification` ni `immutable_sections` en `modes_registry.json`.
5. **Ningún secreto** en el repo. Ni en prompts importados ni en configuración.
6. Nada se da por terminado sin la **salida real** de los comandos del paso 8.

### Pasos

**1. Copiar archivos.** Copia el paquete a las rutas de la tabla de `INSTRUCCIONES_DEVIN_MODOS.md` §1. Además: `mythos_engine.json` y `mythos_engine.py`, `loop_controller.py`, `objective_store.py`, `prompt_import.py`, `validate_contract.py`, `validate_contract_v11.py`, `loop_contract.example.v1_1.json`, `loop_contract.schema.v1_1.json`, los tests y `modes-ci.yml` (a `.github/workflows/modes-ci.yml`). No cambies su contenido.

**2. Frontend.** Aplica los puntos A, B y C de `INSTRUCCIONES_DEVIN_MODOS.md` §5: contenedor del botón junto al `/` y al cerebro, `initModeSelector` y `wrapSend` sobre la función de envío existente.

**3. Backend: entrada.** Punto D. `route_request` antes de cargar la ficha, error 400 con `code` ante `ModeError`.

**4. Backend: objetivo.** Implementa `leer_objetivo_fijado(payload)` con `objective_store.read_objective("state/objective.md")` (ver `INSTRUCCIONES_ADICIONALES.md` §5).

**5. Backend: solicitud al modelo.** Punto E. Mapea `reasoning_effort` y `tool_choice` a los **nombres reales** del proveedor que usa el chat. Después del `system_block`, aplica `prompt_import.apply_prompt_import(...)`.

**6. Backend: bucle y pool.** Punto F con `LoopController` (§3 de las instrucciones adicionales) y, en el modo Mythos, `MythosEngine` (§2). El `executor` y los callbacks del motor se conectan al modelo y las herramientas que el chat ya usa.

**7. Prompts de Fable.** Convierte cada prompt al formato de `prompt_import.example.json`, un archivo por modo. Cada uno debe pasar `python3 prompt_import.py <archivo> modes_registry.json`. Pon la ruta en `prompt_import_slot` del modo (en `modes_registry.json`, campo de ese modo; es la única edición permitida a ese archivo). Si el validador rechaza una línea, **reescríbela** (no la desactives) y anótalo en el log.

**8. Evidencia.** Corre y pega la salida completa de:

```bash
python3 validate_modes.py --strict
python3 mythos_engine.py mythos_engine.json
python3 -m unittest test_mode_router test_additional -v
pip install jsonschema && python3 validate_contract_v11.py loop_contract.example.v1_1.json
node --check mode_selector.js
python3 check_integration.py .
git diff --stat main...HEAD
```
Y las 6 pruebas manuales de `INSTRUCCIONES_DEVIN_MODOS.md` §8, con captura o salida de cada una.

**9. Entrega.** Abre un PR con: `INTEGRATION_LOG.md` (anclas encontradas y decisiones), la evidencia del paso 8 y la lista de nombres que mapeaste (`emit_event`, `iniciar_bucle`, etc.). **No hagas merge.**

### Criterio de aceptación

PASS solo si: todas las salidas del paso 8 son verdes, `--strict` no reporta placeholders, y el `git diff` solo contiene archivos nuevos del paquete más bloques entre marcadores. Si algo falla, repórtalo tal cual con la salida real; no lo declares como terminado.

### Rollback

`git revert` del PR, o borrar los bloques entre marcadores y los archivos del paquete. No debe quedar nada más.
