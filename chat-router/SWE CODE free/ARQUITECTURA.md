# ARQUITECTURA — SWE CODE free y SWEN CODE

## Camino de una petición
`chat / OpenClaw ➡️ plugins ➡️ Harness DeepSeek ➡️ web-bridge :7870 (POST /v1/chat/completions) ➡️ Qwen/DeepSeek web`.
Nada habla directo con el chat ni con el Router MVP. OpenClaw puede llamar al bridge sin pasar por el Router MVP.
El Harness (`chat/backend/deepseek_harness/server.py`) lee `RIU_SWE_BRIDGE_URL`: los ids SWE (`web-*`, `swecode-*`, locales y los `hf-*` del selector) van al bridge. **Si el Router MVP cae**, el Harness no se detiene: responde por el bridge con un modelo local (`RIU_SWE_LOCAL_MODELO`, por defecto `lfm2.5-350m`), **sin herramientas** (GitHub, HF, motor de archivos y memoria del chat viven en el Router MVP y vuelven cuando él vuelve).

## El router propio (web-bridge)
- `model`: `web-qwen38max | web-qwen37max | web-dsv4-flash`, `swecode-<modo>`, `groq/<id>`, `nvidia/<id>` o un local (`lfm2.5-350m`, `qwen2.5-coder-1.5b`, `qwen3.5-0.8b`, `qwen3-0.6b`). `GET /v1/models` los lista; ese es el selector de OpenClaw.
- Cada `conv_id` = una sección = tab propia y chat nuevo en la web (`BRIDGE_MAX_TABS=4`). `consulta` sin modelo = concilio de los 3 + síntesis Qwen 3.8.
- Modos: revisión, solución, arquitectura, archivos, prompt_code, consulta y despliega. Son preámbulos que se inyectan en el bloque 1.
- Credenciales: son de OpenClaw y viajan en cada POST (`cuentas`, `clave`). Nunca en secrets del Space.

- Formato de salida: el bridge antepone el `FORMATO_SALIDA.md` del chat Yaiwes (una sola copia en `chat/backend/mvp/prompts/`) a todo lo que pasa por él, salvo que el Router MVP ya lo haya puesto. Así Liquid y OpenClaw responden con el mismo formato.

## Asesoría antes de ejecutar (`swecode-asesoria` / `SWEN CODE free modo asesoria`)
Primero Groq (las claves del chat Yaiwes); si no responde, la web de SWE CODE free. Devuelve objetivo, plan de acción, mapa mental en texto, estructura a ejecutar y cómo resolver los problemas probables. No ejecuta nada. Cada asesoría se agrega a `BRIDGE_STATE_DIR/proyectos/<proyecto>/ASESORIA.md` (campo `proyecto` del POST; sin él usa el `conv_id`). OpenClaw la relee con `GET /v1/proyectos` y `GET /v1/proyectos/<proyecto>`.

## Respaldo (en este orden)
1. Web: `qwen38max ➡️ qwen37max ➡️ dsv4-flash`; login con la cuenta actual y rotación de correo si cae.
2. Groq ➡️ NVIDIA (mismas claves del chat: `GROQ_API_KEY`, `NVIDIA_API_KEY`, `*_1..N`).
3. HF local `lfm2.5-350m` por `SWECODE_URL_S1..S3` (entra por S1, salta a S2/S3).
4. APK móvil (Chrome del teléfono): último recurso.
La respuesta trae `modelo_usado` y `via_respaldo` (también en los headers `x-modelo-usado` y `x-via-respaldo`).

## Auto-reparación
- `SESSION_EXPIRED`: el bridge ejecuta `salud()` (re-login o rotación de correo) y reintenta una vez; si sigue mal, pasa al respaldo. No espera órdenes.
- Respuesta vacía o `UPSTREAM_TIMEOUT` (100 s): pasa al respaldo.
- Reinicio del puente: el perfil del navegador persiste (`BRIDGE_STATE_DIR/perfiles`) y la sección se retoma sola desde el último bloque.

## Retomar una sección
- Cada bloque enviado se guarda en `checkpoints/<conv_id>.json` con la huella de la tarea.
- Solo se retoma un checkpoint **a medias y de la misma tarea**. Uno completo o de otra tarea empieza de cero (antes devolvía la respuesta vieja).
- `GET /v1/secciones` lista los `conv_id` con su avance (`enviados/total`, `completo`) sin volcar contenido. OpenClaw retoma reenviando el mismo `conv_id` y el mismo texto.
- `BRIDGE_STATE_DIR` debe estar en almacenamiento permanente, o el checkpoint se pierde al reiniciar.

## Auto-evolución
El bridge anota solo cada arreglo propio (re-login, respaldo usado) en `BRIDGE_STATE_DIR/evolucion/lecciones.jsonl`, y `evolucion.py` lee de ahí. También registra a mano (`registrar`); lo que se repite 3 veces se propone como mejora (`PROPUESTAS.md`). Solo dentro de `SWE CODE/` y `SWE CODE free/`.
