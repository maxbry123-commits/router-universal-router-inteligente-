# Secretos (solo nombres, NUNCA valores)
| Variable | Dónde se configura |
|---|---|
| `HF_TOKEN` | Secrets del Space `COMAND-CENTER-1/riu-router` y entorno del agente (acceso al bucket y reinicio) |
| `FICHA_CLAVE_BANCO` | Secrets del Space y entorno del agente (banco de claves de fichas) |
| `QWEN` / DashScope (Token Plan) | Secrets del Space (lo leen las fichas Qwen) |
| `GROQ_API_KEY_*` | Secrets del Space (GROQ_API_KEY_1 en retiro, rama tools-staff) |
| `NVIDIA_API_KEY_*` (5) | Secrets del Space: 1 para Nemotron 3 Pro, 4 para la ficha de código |
| `DEEPSEEK_API_KEY` | Secrets del Space (ficha 4) |
| Token GitHub | Conector GitHub del chat Grok Bot (no hace falta en el Space) |
| Token Vercel | Conector Vercel del chat Grok Bot |

Notas: en el box viejo existía `/workspace/.model_keys.env` (perm 600); hay que borrarlo cuando Antonio lo apruebe y rotar las claves que se pegaron en el chat. Confirma los nombres exactos en la pestaña Settings → Secrets del Space.
