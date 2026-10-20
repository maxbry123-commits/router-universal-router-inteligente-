# INSTRUCCIONES PARA SOL — orquestacion de las 10 ordenes

## Como escribir a cada modelo
POST https://comand-center-1-riu-router.hf.space/plugins/fichas_qwen/call/chat_async
headers: X-Chat-Password: <chat password>  +  Content-Type: application/json
body: {"action":"chat_async","ficha_qwen":"2","modelo":"<ficha modelo>","request_id":"<id unico>","motor":true,"sesion":"<sesion persistente por modelo>","message":"<input block verbatim de orden_XX.md>"}

## Como aprobar
Cuando el proceso termina con estado_tarea=ESPERANDO_APROBACION: mandar otro chat_async con la MISMA sesion y message="/aprobar". No lanzar proceso nuevo.

## Como verificar commit real
- Tras /aprobar y cierre: GET /plugins/fichas_qwen/call/resultado {"proceso_id":...} -> herramientas[] con github_escribir mutacion_real=true.
- Despues verificar en GitHub: el commit y el archivo existen en la rama destino (commits?sha=<rama>). Sin eso = NO_VERIFICADO.

## Si un modelo declara exito sin commit
Re-pedir en la misma sesion: "GAP SIN_EVIDENCIA: repite con commit real". No aceptar. Registrar el modelo y el fallo; no corregir codigo salvo orden del Director.

## Sesiones/modelos (verificados hoy)
- ficha-qwen38max  (sesion sugerida: sol-qwen)
- ficha-glm52      (sol-glm)
- ficha-dsv4pro    (sol-ds)

## Orden de ejecucion
Seguir queue.json cola_backend por prioridad 01..10. Cada orden: input verbatim -> run -> /aprobar -> evidencia -> registrar PASS/FAIL. Si falla, GAP exacto y pasar a la siguiente (o detenerse si la orden lo exige).
