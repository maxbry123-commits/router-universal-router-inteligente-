# RIU-0111 — RESULTADO de la cola (0), Paso 1 y Paso 2 — 2026-09-20

Instrucciones de origen (ya anotadas ANTES de ejecutar): `INPUT-VERBATIM-2026-09-20-b-claves-nvidia-plantilla.md` y bitácora `INPUT-0107-2026-09-20-b.md`.
DSL de Fables registrado verbatim: `DSL-FABLES-yaiwes-node-executor-xray-v2.md`.
Numeración: se usa 0111 porque otro chat ya usó 0107-0110.

## (0) "Las claves de GitHub no pueden no servir" — evidencia
- El valor guardado en el secret es IDÉNTICO al pegado (sha256 coincide: GH_ACCOUNT_1 `5601f35834fd`, GH_ACCOUNT_2 `3327fb31ca7f`; 40 caracteres, prefijo `ghp_`). No hay error de copia.
- GitHub responde `401 Bad credentials` a GH_ACCOUNT_1 y GH_ACCOUNT_2 con los dos esquemas (`Bearer` y `token`). La misma prueba con GH_ACCOUNT_3 da 200 (`planeta123-usa`). Run `35525077586`.
- Conclusión: GitHub rechaza esos dos tokens (revocados, vencidos o regenerados); no es el método de prueba. Los tokens de `maxbry123-commits` (GH_CLASSIC_FULL_1/2 y GH_PAT_FINE_FULL) sí funcionan. Sin token válido para la cuenta `abc123`. Solución: crear un token clásico nuevo con esa cuenta (scopes `repo`, `workflow`) y pasarlo.

## Paso 1 — modelos Kimi K3 / MiniMax / DeepSeek V4 y el cobro en la cuenta de HF
- SÍ están puestos y funcionando por el router de Hugging Face con `HF_TOKEN_1` (cuenta `COMAND-CENTER-1`). Prueba real por `/chat/send` y por el DAG: Kimi K3, DeepSeek V4 Flash, DeepSeek V4 Pro y MiniMax M3 = 200 (runs `35523915544`, `35525147466`).
- La cuenta que se cobra es la del token: `COMAND-CENTER-1`, `canPay=True`, `isPro=False` (run `35525077586`). NO se verificó el saldo ni el cargo exacto (no hay llamada a facturación en el repo).
- Lo que NO existe (y por eso dije "no hecho"): las APIs DIRECTAS de DeepSeek, Moonshot/Kimi y MiniMax con sus propias claves (caché nativa). El proveedor está en el código pero sin claves.

## Paso 2 — claves NVIDIA
- Guardadas cifradas: `NVIDIA_API_KEY_1..5` (Actions Secrets). Sin valores en ningún archivo.
- Las 5 autentican: `GET /v1/models` = 200 con 82 modelos cada una.
- `minimaxai/minimax-m2.7` NO funciona: NVIDIA responde `410 Gone` (modelo retirado) y no está en el catálogo. MiniMax queda por Hugging Face (M3 = 200).
- El catálogo NVIDIA sí trae: `deepseek-ai/deepseek-v4-flash-0731`, `moonshotai/kimi-k3`, `moonshotai/kimi-k2.6`, `z-ai/glm-5.3`, `z-ai/glm-5.3-flash`, varios `nvidia/nemotron-*`.
- Chat real con `deepseek-ai/deepseek-v4-flash-0731`: clave 1 por el chat/Router = 200 (run `35525147466`, `nvidia:deepseek-ai/deepseek-v4-flash-0731 200`); claves 3, 4 y 5 directas = 200 ("OK"); claves 1 y 2 en la sonda directa = `TimeoutError` a los 90 s (capacidad intermitente del endpoint gratuito; la clave 1 respondió 200 por el Router en la otra corrida). No es un rechazo de clave.
- 🚩 Groq, DeepSeek, Moonshot y MiniMax directos siguen sin clave. Cerebras: 402.

## Estado
Cola (0), Paso 1 y Paso 2: `RESUELTO_CON_EVIDENCIA` (con las salvedades de arriba).
EN COLA, NO iniciadas (regla del Director: una a la vez): Q1 plantilla de trabajo desde el YAML de Fables; Q2 Crazy Wall/bitácora/handoff permanente anclado en el chat; Q3 plantilla fija YAML (reglas) + JSON (indicaciones) + Python (motor).
Recomendación (una línea): rotar las claves pegadas en el chat (GitHub, HF y NVIDIA).
