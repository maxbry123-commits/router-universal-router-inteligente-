# HANDOFF — Router Inteligente Universal (estado verificado)

Actualizado: 2026-10-03 noche (Opus). Primero lee `README.md` y `MANUAL-AGENTES.md` de esta carpeta. Aquí solo va el estado y lo pendiente.

## Estado verificado hoy en producción

| Pieza | Estado | Prueba |
|---|---|---|
| Puerta + kernel | OK | `/door/status`: Router de turno cambiado sin corte al código nuevo |
| Router | OK, Job 24/7 cpu-basic 16 GB | Arranca con el paquete del commit `53f755f59` |
| Candado del Director | OK | Sin clave: `403` en tokens, banco y fichas; clave falsa: `403` |
| Fichas | OK | `/secciones/validar` responde `valida: true`; `/secciones/probar` disponible |
| Conexión universal | OK | 1000 tokens creados en 0,8 s |
| 1000 conexiones a la vez | OK 1000/1000 | `/tokens/yo` con 1000 tokens distintos al mismo tiempo: p50 12,7 s, p95 18,3 s |
| Memoria por token | OK 1000/1000 | Guardar + leer con 1000 tokens (40 a la vez): 30 s en total, p50 1,2 s, p95 1,9 s; cada token ve solo lo suyo |
| Banco | OK, 42 claves | Abierto con la clave maestra; copia de respaldo antes de cada cambio |
| Autoscale | OK por RAM | A 93 % de RAM encendió 3 relevos de 32 GB; se apagaron solos a los 5 min sin uso |
| Router de respaldo | OK | Apagado; se enciende con la primera llamada (~7 min) y se apaga a los 5 min |

Tokens de prueba (2001) borrados del registro al terminar. Registro de tokens: 0.

## Lo que hay que saber

- **Límite de Hugging Face:** si **una sola máquina** lanza miles de llamadas seguidas, la puerta de HF corta con `429` (página HTML de HF, no del Router). Con 40 llamadas a la vez por máquina no hubo ni un fallo. Agentes en máquinas distintas no se afectan entre sí.
- **Autoscale por CPU:** corregido en código (mide contra los núcleos pagados), falta repetir la prueba en vivo.
- **OpenAI:** las 14 claves son válidas pero **sin saldo**.
- **GitHub:** el token `github/cuenta-maxbry123` del banco es inválido (401).

## Pendiente (decide el Director)

1. Orden final del repo (dejar solo las raíces del Router y del chat en `main`): **no hecho**. El control automático de seguridad de la sesión bloqueó mover y borrar carpetas en masa; queda para que el Director lo autorice o lo haga.
2. Cargar saldo en OpenAI si se quiere usar.
3. Cambiar los tokens que se pegaron en el chat del 2026-10-03 cuando todo esté estable.
4. Repetir la prueba de autoscale por CPU.

## Cómo se actualiza el código del Router (solo con orden del Director)

1. Commit en la rama de trabajo.
2. Reconstruir el paquete `router-inteligente-universal/codigo/router-bundle.tar.gz` (+ `.json`) con los archivos de `integration`, `security`, `red`, `enchufe`, `Banco de claves`, `requirements.txt` y `chat router/{03-ESTADO,memoria,05-AGENTES,ui}`. Hallazgo: `red/enchufe_gate.py` usa `domain/` para validar contratos v2 y el paquete actual no lo lleva (esa validación falla cerrada); agregar `domain` en el próximo paquete.
3. Pedir el relanzamiento: `POST <puerta>/hf/hardware {"flavor": "cpu-basic", "relaunch_now": true}` con `X-Director-Key`. El kernel cambia de Router sin corte en 1–2 min.
