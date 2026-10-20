# HANDOFF SOL — Router YAIWES (recuperacion)

## Resumen (5 lineas)
1. El Space corre desde git pull (feat/modos-router); el bundle del bucket ya no existe.
2. Las 10 ORDENES del Director estan aplicadas como codigo en HEAD; falta la verificacion real por orden (PASS/FAIL con evidencia).
3. Chat de los modelos: POST /plugins/fichas_qwen/call/chat_async (auth X-Chat-Password), aprobacion con mensaje "/aprobar" en la misma sesion.
4. Cada ORDEN tiene su input block verbatim en orden_XX.md (esta carpeta); la cola en queue.json; instrucciones de orquestacion en instrucciones_sol.md.
5. Regla: sin commit/recibo real = NO_VERIFICADO; no aceptar exito declarado.

## Enlaces
- Ordenes (input verbatim): router inteligente universal/plugins/fichas_qwen/fichas/handoff-sol/orden_01.md ... orden_10.md
- Cola: router inteligente universal/plugins/fichas_qwen/fichas/handoff-sol/queue.json
- Instrucciones para Sol: router inteligente universal/plugins/fichas_qwen/fichas/handoff-sol/instrucciones_sol.md
- Fuente original: rama fichas-tareas-nuevas -> router inteligente universal/plugins/fichas_qwen/fichas/tareas-nuevas-antonio/10_ORDENES_CORRECCION_QWEN_YAIWES.md
