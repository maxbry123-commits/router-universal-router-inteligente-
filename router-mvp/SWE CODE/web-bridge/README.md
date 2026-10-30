# web-bridge — SWEN CODE free

Puente OpenAI-compatible que conduce las cuentas WEB de Qwen y DeepSeek
(chat.qwen.ai / chat.deepseek.com) desde un Space HF scale-to-zero.

## Flujo
- `POST /v1/chat/completions` con `model`:
  - `web-dsv4-flash` | `web-qwen37max` | `web-qwen38max` → objetivo directo
  - `swecode-consulta` / `swecode-plan` → fan-out a los 3 + síntesis Qwen3.8Max
  - `swecode-revision|solucion|arquitectura|archivos|prompt_code` → objetivo único
- Entrada grande → bloques `[BLOQUE n/N · MODO X]` (~2500 chars) + `checkpoint.json`
  en `BRIDGE_STATE_DIR` (montar dataset permanente) → retoma tras reinicio.
- Sesión caída → login con cuenta actual; falla → rota al siguiente correo
  (`WEB_ACCOUNTS`, misma `WEB_PASS`). Errores tipados: `SESSION_EXPIRED`,
  `SELECTOR_BROKEN`, `INPUT_NO_ENCONTRADO`.
- `POST /refresh_session` → chequea sesiones vivas (herramienta nativa del agente).

## Secrets del Space
`WEB_ACCOUNTS` (correos separados por coma), `WEB_PASS`, `BRIDGE_PROXY` (opcional).

## Pendiente honesto
- Los selectores `@@` en `src/sites.js` son candidatos genéricos: calibrarlos
  contra la página real en el primer arranque (la web cambia su DOM seguido).
- Login inicial por correo+clave vía script; si el sitio pide captcha/2FA,
  hay que resolverlo una vez manual (fallback: proxy residencial en `BRIDGE_PROXY`).
