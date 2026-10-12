# PARCHE DE RECUPERACION 2 - TODAS LAS FICHAS (2026-10-12)
1. Las fichas son DAG en JSON dentro de sellos cifrados: plugins/fichas_qwen/sellos/*.sello (cabecera FICHA-SELLO-1 + salt16 + nonce12 + AESGCM, scrypt n=2**15 r=8 p=1, clave FICHA_CLAVE_BANCO). fichas_qwen._modelos() lee todos los sellos y busca bloques ficha-...
2. Ficha 1 (texto): ficha-qwen38max, ficha-qwen38flash, ficha-qwen37max, ficha-qwen37plus, ficha-qwen36flash, ficha-dsv4pro, ficha-dsv4pro0813, ficha-dsv4flash, ficha-glm52. Imagen (2) y voz (3): GAP_NO_EXECUTOR permitido.
3. Ficha 2 = DAG de codigo. Ficha 3 = DAG de frontend (N1 Qwen 3.8 Max, N2 GLM 5.2, N3 Qwen 3.7 Max, N3B y N3D DeepSeek V4 Pro, N4 DeepSeek V4 Flash ejecuta; unos 105 s). Ficha 4 = copia fiel de la Ficha 1, la usa el Harness por HTTP.
4. Ruta de Ficha 4 (_ficha4_modelo en plugins/fichas_qwen/plugin.py): small/simple/tool/lookup/code/debug/refactor -> ficha-qwen38flash; frontend -> ficha-dsv4flash; reason -> ficha-qwen37max; complex/architecture/planning -> ficha-qwen38max.
5. Arquitectura que NO se toca: COMPONENTE -> HARNESS puente_chat -> HTTP -> FICHA -> MODELO -> HTTP -> HARNESS. Graphiti va Harness -> HTTP -> Ficha 4, nunca un modelo directo.
6. Llamadas: POST /plugins/fichas_qwen/call/chat_async con {ficha_qwen:"1|2|3|4", modelo, messages:[{role,content}], sesion} y luego /resultado con proceso_id. El campo del mensaje es messages.
7. Selectores de la pantalla: Nvidia groq team, Ask consil Nvidia groq, Team qwen (ficha 1), Ask consil code qwen team (ficha 2), Ask consil fromtend qwen team (ficha 3), workflow Loops code Yaiwes.
8. Probado 2026-10-12 en el Router vivo: las 4 fichas terminan con respuesta.
