# README de fichas (ancla de todas las fichas, presentes y futuras)

## Regla principal
1 FICHA = 1 TAREA = 1 MINI-SISTEMA. Cada ficha lleva su DSL, su scheduler local, su ejecutor, su verificador, su cache y su ledger. NO existe scheduler central. La ficha termina y se apaga.

## Lo unico compartido
1. La COLA GLOBAL (Puerta): presta puestos de API, maximo 4, por prioridad y llegada, espera hasta 10 min, libera si la ficha muere. Su limite vive SOLO en `motor/puerta.config.json` (pool qwen-token-plan); las fichas apuntan al pool.
2. El registro de CANDADOS de rutas: dos fichas no escriben el mismo recurso a la vez. No administra tareas.
3. El almacen fisico del Harness (memoria).

```
FICHA A (scheduler A) -+
FICHA B (scheduler B) -+--> COLA GLOBAL --> [P1][P2][P3][P4] --> API Qwen Token Plan
FICHA C (scheduler C) -+
```

## API (Token Plan)
Clave `sk-sp-...` + base `https://token-plan.maas.qwencloudapi.com/compatible-mode/v1` (header Authorization: Bearer). Nunca mezclar con coding-intl, dashscope ni pay-as-you-go. La clave solo vive cifrada en `modelos-14`.

## Ask Council
Es de 3 analizadores en paralelo (DeepSeek V4 Pro, GLM 5.2, Qwen 3.7 Max) y luego un ejecutor, dos revisiones y la SALIDA. Los GOALS (12 de entrada y 12 de salida) van en las fichas 2 y 3: son datos/criterios con 0 llamadas a la API y los reciben los modelos del flujo. La ficha 1 (modelos individuales) NO lleva goals ni Council. No hay modelos de imagen ni voz dentro del Council.

## Salida, presupuesto y cache
La SALIDA (el texto del ultimo paso) siempre se entrega. Aparte lleva una etiqueta: verificada solo si el Harness devuelve evidencia (exit_code 0, archivos, tests ejecutados y pasados, receipt); si no, queda SIN VERIFICAR (GAP_HARNESS_EXECUTOR) y no se promueve a la memoria del proyecto. El presupuesto de tokens (`task_budget`) es de la FICHA completa; `max_output_tokens` es el tope por llamada. La cache local no se cuenta como cached_tokens de la API.

## Memoria
Sin almacenamiento propio: la ficha solo lleva su namespace (task_id) y promueve al proyecto solo lo verificado. GAP: `motor/memoria.py` (conectar_harness) falta cablearlo a memoria_yaiwes.

## Crear una ficha nueva (checklist)
1. Copiar una carpeta fichaN y cambiar ficha.json (nodos, modelos, depende_de, rutas).
2. Mantener `readme: ../README-FICHAS.md`, `api: modelos-14` y `cola: {pool: qwen-token-plan}`.
3. Validar y probar: python -m motor.prueba_fichas (job de 16 GB, no Vercel).
4. Cifrar: FICHA_CLAVE_BANCO=... python -m motor.sellar sellar ficha.json (y actualizar la copia de auditoria/).
5. Correr: python -m motor.ficha_os ficha.json --tarea T-001 --texto "..."

## Modelos 10 a 14 (imagen y voz): adaptadores propios (motor/modelos_especiales.py)
- Imagen (Qwen Image 3.0 Pro, Wan 2.7 Image): POST https://token-plan.maas.qwencloudapi.com/api/v1/services/aigc/multimodal-generation/generation (docs.qwencloud.com, integrate-multimodal-gen). La salida es la URL de la imagen.
- Texto a voz (Qwen TTS): WebSocket del SDK dashscope, wss://token-plan.maas.qwencloudapi.com/api-ws/v1/inference. La salida es el archivo mp3.
- Voz a texto (Qwen ASR): mismo POST de multimodal-generation con el audio (URL o Base64). Formato segun la documentacion de Model Studio; sin verificar en el Token Plan.
- Voz en vivo (Qwen Realtime): WebSocket wss://token-plan.maas.qwencloudapi.com/api-ws/v1/realtime?model=qwen-audio-3.0-realtime-plus (cliente websocket-client). Manda el texto y junta la respuesta; el formato de eventos sigue la documentacion y se verifica con la llamada real.
- Estado: probados con servidor falso; SIN prueba real todavia.

## AVISO sobre el Token Plan Individual: segun docs.qwencloud.com (token-plan-personal-overview) el plan es para uso interactivo dentro de herramientas de programacion y agentes, una persona y un dispositivo. Scripts de automatizacion, backends propios y llamadas batch no interactivas quedan fuera de alcance y pueden causar suspension del plan o bloqueo de la clave. Para colas de agentes y jobs automaticos conviene la API Standard (pago por uso).

## Plantilla del Director (PLANTILLA XRAY-V2)
Es `plantilla/PLANTILLA_XRAY_V2.yaml`, tal cual la dio el Director (verbatim, sin resumir). El agente la carga COMPLETA en cada llamada de cada ficha: el bloque `<user_query mode="verbatim">` lleva la entrada del nodo y despues se suman las mejoras (`plantilla/MEJORAS_FICHAS.yaml`). FichaOS se niega a correr una ficha sin plantilla. Como la plantilla pesa unos 13.000 caracteres, el limite de llamada de las fichas es `motor.limite_llamada_chars` (60.000 Qwen, 30.000 NVIDIA/Groq) en lugar de los 18.000 de antes.

## Ficha 4 y pools de API
La ficha 4 es el Ask Council de NVIDIA y Groq (Kimi K3, GLM 5.3, Qwen 3.8 Groq, Glimmer 30B). Cada API tiene su pool de puestos (`motor/puerta.config.json` = qwen-token-plan, `motor/pools/nvidia-groq.json`); la ficha apunta a su pool.
