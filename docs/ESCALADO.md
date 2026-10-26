# Escalado bajo demanda (hasta 3 servidores HF CPU 32 GB)

Código: `mvp/escalado.py` (elección de destino), `mvp/trabajos.py` (registro persistente), `mvp/app.py` (`_correr`, `_remoto`, `_recuperar`). Sin HF Jobs, restart, keep-alive ni cron.

## Reglas implementadas
- **Destinos:** este Router (`local`) + hasta 2 URLs https de `RIU_SCALE_TARGETS` (coma). Un cuarto o duplicado se ignora. Sin la variable, todo corre local como antes.
- **Umbral:** CPU real del servidor 0–100 (`psutil.cpu_percent`, no RAM). `< 85 %` → local; `≥ 85 %` → siguiente destino con capacidad. Capacidad por servidor: `RIU_SCALE_CAPACITY` (6 trabajos).
- **Sin duplicar ni mover:** un trabajo ya enviado no se reasigna. Reintento con el mismo `request_id` ⇒ mismo `proceso_id`, nunca doble ejecución.
- **Cola:** si los tres están ocupados o caídos, el trabajo queda `procesando/en_cola` en el Router de entrada (máx. 200; luego 429).
- **Despertar:** un destino sin contacto >290 s se considera dormido: no se le sondea; se le envía el trabajo por HTTP y se reintenta cada 3 s hasta 180 s. Solo se consulta `GET /health` (campo `cpu`) a destinos despiertos. Un destino caído se salta 30 s.
- **Resultado entre procesos:** cada trabajo se guarda en `/almacen` HF (`trabajos/<pid>.json`). `resultado` lo recupera si el proceso no es el que lo inició; un trabajo local `procesando` sin avance >15 min se da por interrumpido y puede relanzarse con el mismo `request_id`.
- `/chat/send` usa el mismo circuito cuando hay destinos configurados.

## Contrato para Devin (solo configuración HF)
1. Máx. 3 Spaces, hardware `cpu-upgrade`, 1 réplica cada uno, sleep 300 s. El Router de entrada es el que recibe tráfico (Vercel apunta a él).
2. En el Router de entrada: `RIU_SCALE_TARGETS=https://<destino2>.hf.space,https://<destino3>.hf.space` (no secreto).
3. Los destinos corren el mismo `mvp` (`main`), con **la misma clave de acceso** (`RIU_API_KEY` y variantes), el mismo banco y el mismo bucket `yaiwes-memoria-storage`. No llevan `RIU_SCALE_TARGETS`.
4. Endpoints usados: `GET /health` (cpu), `POST /plugins/puente_chat/call/chat_async` y `.../resultado`.

## Límites (NO VERIFICADO en vivo)
Pruebas: `mvp/test_escalado.py` (simulado, sin red). Dos Routers que reciben `chat_async` a la vez con el mismo `request_id` pueden ejecutarlo una vez cada uno (no hay candado distribuido). El estado del chat (`control.json`) lo comparten los destinos solo si usan el mismo bucket.
