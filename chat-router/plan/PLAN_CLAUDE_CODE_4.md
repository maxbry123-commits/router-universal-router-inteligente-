# PLAN — Claude Code 4 (chat delegador)

Estado: 2026-11-09 · Ubicación: `chat-router/plan/` (main) · Un solo archivo de trabajo: este.
Fuente de verdad: `Claude.md` (checklist del input block) y `Claude notas.md` (pizarra compartida, con sección temporal de archivos cableados).

## 1. Rol

Claude Code 4 no implementa el router. Delega, audita, coordina y revisa.
Equipo:
- Router 1 (ROUTER MVP v1 + llm system HF/llm_router): trabajo de cómputo, control de LLM, enrutadores.
- Router 2 (HUGGUEFACE SPACE/, rama ccr-42f0e753-ni96xs): auditoría y copia de los Spaces de Hugging Face.
- Claude Code 4 (este chat): auditoría forense, frontend, agentes, revisión final.
- SWE CODE free: en curso en otro chat. No se toca salvo que el owner lo pida.

## 2. Tareas

### A. Búsqueda y auditoría (prioridad, delegada a sub-agente de auditoría)
A1. Rufo y Rotboat: buscar en TODAS las ramas remotas y en TODO el repo (texto, nombres de archivo, commits). Resultado: ubicación exacta o "no existe" con evidencia.
A2. Auditoría forense X-Ray de 3 pasadas: buscar en todas las ramas y en el repo completo. Si no existe como documento, rehacerla (3 pasadas: inventario, cruce con código fuente, verificación cruzada). Resultado: `chat-router/plan/XRAY_3_PASADAS.md`... (SOLO si no existe; si existe, solo reportar su ubicación).
A3. Skill "Maxbry UI frontend": buscar en todo el repo y todas las ramas. Si existe, cablear al README de arquitectura y a `Claude notas.md`. Si no existe, reportar y no inventarlo.

### B. Frontend (2 vías, aislado)
B1. Preparar en sandbox la ventana nueva del selector de dos vías (modelo que razona + agente que ejecuta), como HTML separado, con prueba local.
B2. Entregar el HTML al owner. No editar la ventana vieja hasta recibir "Ok".
B3. Tras "Ok": edición quirúrgica, eliminar la ventana vieja, dejar reglas de frontend en archivos separados, cablear al README y a `Claude notas.md`.
B4. Criterio: todo cambio de frontend sigue el protocolo de ALERTA de `Claude notas.md`.

### C. Agentes, memoria y almacenamiento (Paso 2)
C1. Mapear chat → Harness DeepSeek → plugins → agentes → memoria/almacenamiento → router de cómputo. Solo lectura primero.
C2. Proponer el cableado. Implementar solo tras aprobación.

### D. Revisión (un solo revisor por entrega)
D1. Revisar la entrega de Router 1 y Router 2 contra el input block verbatim. Reportar PASS, FAIL o 🚩, con evidencia.
D2. El revisor no escribe código. Solo verifica.

## 3. Sub-agentes

- Máximo 1 sub-agente de revisión por entrega.
- Sub-agente de auditoría (A1–A3) puede dividirse en 3 partes, una por tarea.
- Si el sub-agente genera ruido, su salida va a la sección temporal de `Claude notas.md`. No se mezcla con el resto.

## 4. Reglas

- Modo Loop: avanzar tarea por tarea hasta terminar. No parar por dudas menores.
- Dudas: se resuelven con el input block y este plan. Si aún así no se resuelven, se anotan como 🚩 al final.
- Ninguna preguntas en medio del loop. Al terminar, una lista de preguntas por inciso, y el loop sigue.
- Cada tarea: DSL DAG en `Claude notas.md`, handoff JSON, y al cerrarse se marca y se borra de la sección activa (queda en la sección temporal archivada).
- Atribución: `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>` y `Claude-Session: https://claude.ai/code/session_01BK5y7GKUQ8CNDJSn8vc749`.
- Sin GitHub Actions, sin LFS, sin despliegue nuevo en Vercel o Hugging Face sin autorización.
- Claves y secretos: nunca en archivos, logs ni respuestas.
- Un archivo = una responsabilidad. Máximo 200 líneas.
- Integración automática: auto pull siempre. Ninguna integración se fusiona sin test en sandbox y autorización del owner.

## 5. Entregables

- Por tarea: estado, evidencia (commit o ruta), DSL DAG, handoff JSON.
- Al final del loop: lista de 🚩 y lista de preguntas por inciso.
- Para Paso 4 (cierre de Router 1 y Router 2): reporte de PASS local y de contrato, y lista de lo que queda como 🚩 por depender de servicios externos.

## 6. Handoff JSON (plantilla)

```json
{
  "router": "CLAUDE CODE 4",
  "tarea": "A1|A2|A3|B1|B2|B3|B4|C1|C2|D1|D2",
  "estado": "pendiente|en_curso|cerrado|flag",
  "evidencia": "commit o ruta",
  "subagente": "auditoria|frontend|revision|ninguno",
  "flags": []
}
```

## 7. Prompt de activación (copiar tal cual)

```
Eres CLAUDE CODE 4 (chat delegador). Modo Loop: avanza tarea por tarea hasta terminar todas. No pares, no escales, no expliques de más.

Lee primero:
- Plan: chat-router/plan/PLAN_CLAUDE_CODE_4.md (main)
- Checklist: Claude.md (main)
- Pizarra: Claude notas.md (main)
- Input block verbatim: kernel/INPUT_BLOCK_YAIWES_CABLEADO.md (main)

Empieza por A1, A2 y A3 (búsqueda en todas las ramas y todo el repo). Delega la búsqueda a un sub-agente. Después sigue con B1 (ventana en sandbox), luego C1 (mapa de cableado, solo lectura) y D1 (revisión de las entregas de Router 1 y Router 2).

Reglas:
- Las dudas se resuelven con el input block y el plan. Si no se resuelven, márcalas 🚩 y sigue.
- No hagas preguntas en medio del loop. Al terminar todo, da la lista de preguntas por inciso.
- No edites la ventana de frontend vieja sin el "Ok" del owner.
- No escribas claves ni secretos en ningún archivo.
- Atribución en cada commit: Co-Authored-By y Claude-Session.
- Al cerrar una tarea, actualízala en Claude notas.md y muévela a la sección archivada.
```

## 8. Dudas que este chat deja al owner (para la salida 3)

1. ¿Dónde está el skill "Maxbry UI frontend"? (A3 lo busca, pero si no aparece, lo necesito.)
2. ¿Autorizas el selector de dos vías como ventana nueva aislada en `chat-router/chat/frontend/`?
