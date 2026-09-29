# T-03 — Quitar Cerebras del código del Router y poner Groq en la cadena
**Estado:** PENDIENTE · **Depende de:** T-01 · **Nodo:** N-03

## Qué es, en palabras simples
Tú dijiste "borra a Cerebras del mapa". El enrutado de agentes ya lo excluye, pero el nombre sigue escrito en tres archivos del Router. Además Groq (tu segundo proveedor) hoy no está en ninguna cadena.

## Cómo se hace (sin escribir código nuevo, solo quitar y ajustar)
1. `router inteligente universal/integration/chat_mvp/providers.py`: quitar la entrada de Cerebras y su comentario.
2. `…/resilience.py`: quitar Cerebras de la cadena g2; poner Groq entre NVIDIA y DeepSeek.
3. `…/vault_bridge.py`: quitar Cerebras del mapa de proveedores.
4. Comprobar con el smoke (`riu-router-smoke.yml`) después de relanzar.

## Orden final de modelos
NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic.

## Ojo
El Router repull cada 60 s pero el código ya importado no cambia sin relanzar el Job. Relanzar apaga el anterior: **se pide tu permiso antes**.

## Listo cuando
El smoke muestra cadena `NVIDIA → Groq → DeepSeek` y ninguna mención de Cerebras en el estado del Router.

## Evidencia (del punto de partida)
`/chat/router/status` (run 36513612455): Cerebras "sin modelo"; Groq en ninguna cadena.
