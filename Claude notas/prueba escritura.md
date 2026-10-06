# Prueba de escritura — Claude (Moonshot/Kimi K3)

Fecha: 2026-10-05. Escribo en el repo `router-universal-router-inteligente-` (rama main) para comprobar que puedo escribir. Si ves este archivo en GitHub, la escritura funciona.

**Resumen del estado de "claude notas 1.md" que revisé:**

## Lo que hay resuelto ya
- Router vivo: 1 job cpu-basic (16 GB), autoscaler y /hf/compute limitados a cpu-basic.
- Space puerta reanudado (RUNNING en cpu-upgrade 32 GB; pasar a cpu-basic da 402: hay que cambiarlo a mano en los ajustes del Space).
- puente_chat v0.2.0 con 5 seguridades de apagado del L4 (30 s tras salida, 5 min sin pedidos, tope 1200 s, barrendero, un solo L4 a la vez). Probado en vivo.
- Vercel: solo UI publicada, /api/chat da 404, harnessUrl apunta a la puerta fija del Router.
- Modelos locales en HF: `router-respaldo/modelos/`.

## Cómo resolver lo que falta
1. **Parche de recuperación para Opus:** completo la lista de comprobaciones pendientes aquí (ya pedida por el Director a las 23:58).
2. **Space puerta → cpu-basic:** hacerlo a mano en Settings del Space (la API devuelve 402).
3. **Sentinela anti-caída:** cambiar el Space por un simple job + script vigilante que lo reenciente si cae (orden 23:33).
4. **Salto al 85% de RAM/CPU:** añadir al autoscaler/hf_worker_pool la regla: si cpu-basic llega al 85%, encender el siguiente cpu-basic (cadena de 16 GB).
5. **Seguir el DAG:** S1 lectura en main (ya hecha en gran parte) → S2 plugin de fichas en `plugins/fichas/` → S3 conexiones (laboratorio, JSON vivo, enchufe Fables, harness) → S4 fichas 0-2 → S5 router de respaldo HF → S6 sacar modelos del Router → S7 pruebas punta a punta + README + handoff.
6. **Reglas de seguridad:** claves solo del banco (nunca en archivos ni chat), candado binario con huella (nunca la clave) para tocar fichas, nada vive dentro del Router, nada en GitHub Actions.

## Dudas abiertas que hay que cerrar con el Director
1. ¿Los comandos `razona`/`ejecuta`/`refactoriza` solo en el router de respaldo HF o también en fichas 1 y 2?
2. ¿Frontend de ficha 2 = Nemotron 3.5 Lightning → muse-glimmer-30b? (asumido)
3. GLM 5.3: cadena de respaldo tomada de la orden 17:18 (Lightning → muse-glimmer-30b), no la de 17:10 (Kimi K3). ¿Confirmas?

Archivo creado por prueba de escritura. Puedes borrarlo.
