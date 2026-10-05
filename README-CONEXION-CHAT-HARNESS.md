# Conexión del chat — v5

> **Estado vigente 2026-10-05: Router detenido por orden del Director. Renovación eliminada. La interfaz se abre sin solicitar clave; no hay backend HF activo. Las descripciones de actividad que siguen son históricas. No reactivar sin nueva orden.**

Actualizado: 2026-10-05. Sin claves en este archivo.

La pantalla está en https://riu-jev-bridge.vercel.app. El servidor, puente, herramientas, banco y memoria están en Hugging Face, en un Job cpu-upgrade de 32 GB. El Space anterior permanece pausado.

## Dirección y autenticación

La dirección vigente está en `router inteligente universal/LIVE_URL.json` en main. La pantalla consulta ese archivo cada 30 segundos antes de hacer llamadas. Job actual: `6ac40a4b404719ba37658c12`. Base actual: https://6ac40a4b404719ba37658c12--8000.hf.jobs.

Puente: `<LIVE_URL>/plugins/puente_chat/call`. Todas las llamadas usan `X-API-Key: <clave del chat>`; la clave está en el banco cifrado, referencia `router/chat-ui-director`. La pantalla la conserva por pestaña en sessionStorage. Vercel aloja únicamente la interfaz estática.

## Modelos

| ID | Proveedor |
|---|---|
| nv-kimi-k3 | NVIDIA Kimi K3 |
| nv-glm-5-3 | NVIDIA GLM 5.3 |
| nv-nemotron-super | NVIDIA Nemotron 3 Super |
| nv-nemotron-lightning | NVIDIA Nemotron 3.5 Lightning |
| groq-qwen-3-8 | Groq Qwen 3.8 |
| hf-1-qwen-3-8 | Qwen 3.8 27B GGUF, L4 en HF |
| hf-2-qwen-3-6 | Qwen 3.6 35B A3B GGUF, L4 en HF |

Los siete tienen herramientas HTTP de internet, GitHub y HF. Las credenciales se leen del banco y no se envían al modelo. Los cinco modelos API rotan claves del mismo modelo; no se cambia el modelo seleccionado.

## Protocolo

POST JSON a `<puente>/<acción>`, respuesta `{status:"ok",result:{...}}`.

- `modelos`, `status`: estado y modelos.
- `chat_async`: cuerpo `{model,messages,max_tokens,sesion,respaldo_url?}`; devuelve `{estado:"procesando",proceso_id}`.
- `resultado`: cuerpo `{proceso_id}`; consultar hasta obtener el resultado final, con `choices[0].message.content` y `memoria_guardada`.
- Modelos HF sin respaldo: resultado `{estado:"encendiendo",job_id,url}`; consultar `estado` con `{job,url}` y repetir chat_async con respaldo_url cuando esté listo.
- `apagar` con `{job}`, `apagar_todo`: apagar únicamente los respaldos L4.

## Memoria, almacenamiento y renovación

Cada turno se guarda por sesión en SQLite y se sincroniza al bucket `COMAND-CENTER-1/yaiwes-memoria-storage`, bajo `router-inteligente-universal/memoria`. API de memoria: `/memoria/save`, `/memoria/load`; archivos: `/espacio/<ruta>`. El chat recupera los últimos turnos de su sesión.

`riu_kernel.py` se ejecuta cada diez minutos mediante el schedule HF `6ac40924fbc85ba6823aca1b`. Mantiene un Router de 32 GB, renueva el Job de 24 horas, publica LIVE_URL, conserva memoria y retira el anterior después de comprobar el sucesor. No escala automáticamente. Los L4 se encienden al pedir un modelo HF y se apagan después de responder o al quedar inactivos.

## Verificación realizada

Los siete modelos respondieron con herramientas reales de internet/HF y memoria guardada. GitHub tiene permisos de administración/escritura sobre el repositorio. Lectura/escritura/borrado de archivos y memoria persistente respondieron correctamente. Evidencia en el bucket, carpeta `laboratorio`. La autenticación de la pantalla se corrigió a X-API-Key después de detectar el 401 de Authorization.
