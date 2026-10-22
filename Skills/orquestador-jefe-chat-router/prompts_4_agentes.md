# Colas de tareas por bot

Cada bot escribe solo su sección, de uno en uno, con pull antes de escribir. Las instrucciones de Antonio están en `SKILL.md`.

## HF Centinela

1. Coordinar el grupo según las instrucciones de Antonio: dar las órdenes (quién ejecuta, los demás en pausa), asignar en paralelo solo lo que no se pisa y cerrar cada paso con PASS o BLOCKED después de Guardián y Sheriff.
2. Verificar que cada despliegue caiga en el lugar indicado y que no se toque nada más; exigir evidencia real (SHA, diff, estado del Space, HTTP).
3. Hugging Face S10: N09, N10 y V10 cerrados en PASS; cerrar N11 con la evidencia autenticada de Ejecutor 1 y luego N12 con Sheriff y Guardián.
4. Auditar el router en GitHub y el cableado del chat con Code 1 y Sol Auditor, respetando la ruta chat y selector team Qwen ➡️ plugin Harness DeepSeek ➡️ HTTP ➡️ enrutador HTTP del router, sin cambiar la arquitectura.
5. Lograr que el chat funcione en el selector team Qwen con todos los modelos en https://riu-jev-bridge.vercel.app/ y controlar a los equipos y los chats de Sol para que no alucinen.
6. No escalar a Antonio; a Claude solo cuando se agoten todas las posibilidades. Al terminar, congelar a todos en pausa.

## HF Sheriff Validador

1. Bloquear cualquier salida de código, tarea o acción de computadora que no sean las instrucciones de Antonio, o cuyo código no sea el que él dio.
2. Validar con evidencia real (SHA, diff, estado del Space, respuestas HTTP) cada nodo que ordene Centinela y responder SHERIFF_PASS o SHERIFF_BLOCKED.
3. Vigilar que ninguna clave quede escrita en el chat, en archivos ni en git, y que nadie toque nada fuera de su alcance, con push normal, sin force push ni LFS.
4. Cerrar N12 de Hugging Face junto con Centinela y Guardián cuando N09–N11 tengan evidencia.
5. Validar los gaps y arreglos de Code 1 y de Sol Auditor contra las instrucciones de Antonio: solo lectura sin PASS, arquitectura sin cambios, edición quirúrgica.
6. Después de Hugging Face: vigilar que se cumplan los objetivos (chat team Qwen, pruebas reales del frontend y el backend, MCP `riu-router-github`) y hacer mis 4 pruebas reales del chat https://riu-jev-bridge.vercel.app/ en distintas sesiones.

## HF Guardián Refactoria

1. Antes de que cualquier bot actúe, revisar que la acción esté dentro de las instrucciones de Antonio; si no, bloquearla.
2. Revisar cada salida y cada mensaje a Sol: solo lectura sin PASS, sin cambiar arquitectura, sin sobreingeniería, edición quirúrgica, sin claves en chat, archivos ni git.
3. Vigilar que nadie toque nada fuera de su alcance (en `reorganizacion`, solo `Skills/orquestador-jefe-chat-router/`), con push normal, sin force push ni LFS.
4. Cerrar N12 de Hugging Face con GUARDIAN_PASS cuando N09–N11 tengan evidencia.
5. Después de Hugging Face: mi parte del reparto y 4 pruebas reales del chat https://riu-jev-bridge.vercel.app/ en distintas sesiones.
6. Si el bucle completo se agota, escalar a Claude, por medio de Ejecutor 2, con la bitácora, los problemas y la investigación. Nunca escalar a Antonio.

## Huggueface Ejecutor (Ejecutor 1)

## Ejecutor 2

1. Reescribir el skill (hecho, commit `42cbc90`).
2. N11, solo lectura, cuando N10 tenga PASS: estado RUNNING, `/health`, `/chat`, `/mcp`, `/almacen`, 401 sin clave, `MVP_COMMIT` = `0ff3bb7` en logs.
3. Después de Hugging Face (I07): pedir a 🎯 Sol GrokBot los handoff del backend y del frontend; poner a los modelos team Qwen a hacer tareas reales que escriban en GitHub; probar en mi computadora https://riu-jev-bridge.vercel.app/ de arriba abajo, con 3 revisiones.
4. Probar el MCP `riu-router-github`: tools/list (6), listar_fichas, chat, resultado con team Qwen.
5. Ser el puente a Claude si Guardián escala.

## Code 1

1. Copiar palabra por palabra los prompts de 📌router Sol GPT DSL-DAG (hecho: 4 prompts, `cableado_mcp_chat_v1`, S10 Hugging Face, `modelos_token_plan_v2` y `mvp_router_construir_v3`, guardados en mi computadora; el primero contiene la clave del MCP y no se sube).
2. En 🚀 Rol auditor refactoría, Sol revisa en solo lectura el cableado y el historial de commits contra la ruta chat y selector team Qwen ➡️ plugin Harness DeepSeek ➡️ HTTP ➡️ enrutador HTTP del router. Los gaps van a Centinela, Sheriff y Guardián; no se arregla nada sin PASS.
3. Pedir a Sol un prompt con todo el planteamiento y abrir la investigación profunda en ese mismo chat, con el handoff de todos los archivos del router.
4. Repetir la auditoría y la investigación con el prompt 3 (`mvp_router_construir_v3` + `modelos_token_plan_v2`), aunque no esté terminado.
5. Arreglos quirúrgicos solo con PASS: primero Sol Auditor, después yo; si no funciona, Guardián escala a Claude con la bitácora.
6. Después de Hugging Face: probar el chat team Qwen, el frontend y el MCP `riu-router-github` con trabajo real.
