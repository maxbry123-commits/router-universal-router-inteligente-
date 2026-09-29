# ESQUEMA OBLIGATORIO yaiwes.gate/v1 — diseño de Opus (el agente 35 lo replica en código)
Regla: NINGÚN agente ejecuta un chain.yaml sin pasar por las 5 puertas. No es una skill opcional: es código que el ejecutor (chain.py) llama siempre.
Si una puerta falla → status BLOCKED + GAP en crazy_wall.state.json. Nunca se salta.

## Flujo
ORDEN → G0 ENTRADA → G1 PROMPT → G2 MÍNIMO → [EJECUCIÓN del paso] → G3 VERIFICACIÓN → G4 MEMORIA → CIERRE

| Puerta | Origen | Qué hace (determinista) | Falla si |
|---|---|---|---|
| G0 ENTRADA | Director | input_block literal presente; agente con CLAUDE.md; ruta de modelo permitida; flag PAUSED=false | falta input_block, agente pausado o ruta no permitida |
| G1 PROMPT | Prompt Master | normaliza cada task: objetivo, entrada, salida exacta, formato, límites; rechaza tareas vagas | task sin salida verificable o sin checks |
| G2 MÍNIMO | Ponytail | antes de escribir código: busca en repo/stdlib/componentes descargados algo que ya lo resuelva; registra "reusa X" o "nuevo porque Y" | propone código nuevo sin justificar por qué no reutiliza |
| G3 VERIFICACIÓN | ECC (reglas, seguridad, verificación) | checks del paso + no_secrets + sintaxis (python_ast / js_syntax) + regla de seguridad ECC aplicable | cualquier check falla |
| G4 MEMORIA | Memanto (cuando exista) / memory_adapter | guarda resultado, decisiones y GAPs en MEMORIA.md del agente y en memoria global; marca duplicados | no se pudo guardar |

Agent Skills = formato de empaquetado: cada puerta vive como carpeta `gates/<Gx>/SKILL.md` + `gate.py` con una sola función `check(ctx) -> (ok: bool, motivo: str)`.

## Contrato de código (lo que el agente 35 debe producir)
```
gates/
  registry.yaml        # orden fijo: [G0, G1, G2, G3, G4]; obligatorio: true
  G0_entrada/gate.py
  G1_prompt/gate.py
  G2_minimo/gate.py
  G3_verificacion/gate.py
  G4_memoria/gate.py
gate_runner.py         # run_gates(fase, ctx) -> PASS / BLOCKED(motivo)
```
En chain.py: `run_gates("pre", ctx)` antes de cada paso (G0–G2) y `run_gates("post", ctx)` después (G3–G4). Sin bandera para desactivarlo.

## Prueba de éxito
1. Un chain.yaml sin input_block → BLOCKED en G0.
2. Una task sin checks → BLOCKED en G1.
3. Un paso que devuelve una clave → BLOCKED en G3.
4. Un chain.yaml correcto → CLOSED y queda línea nueva en MEMORIA.md.
