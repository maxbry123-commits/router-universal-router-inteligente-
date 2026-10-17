# Secretos (solo nombres, NUNCA valores)
Verificado con la API de HF (`/api/spaces/COMAND-CENTER-1/riu-router/secrets` y `/variables`) el 2026-10-16 22:45 (UTC-5).

## Space `COMAND-CENTER-1/riu-router` → Settings → Variables and secrets
| Nombre | Tipo | Uso |
|---|---|---|
| `HF_TOKEN` | secreto | acceso al bucket `yaiwes-memoria-storage` (sync de memoria, bundle) |
| `RIU_VAULT_PASSPHRASE` | secreto | abre el vault/banco de claves (`/vault`) donde viven las claves de modelos (Qwen, DeepSeek, NVIDIA, Groq) |
| `RIU_FICHA4_TIMEOUT` | variable pública | timeout de la ficha 4 |
| `RIU_ROUTER_URL` | variable pública | URL interna del router |
| `RIU_SECRETOS_PIN` | secreto (**pendiente**) | PIN de la ventana de secretos/MCP de la rama `secretos-watchdog-mcp-rebase`; Antonio lo escribe en el formulario del Space al integrarla |
| `RIU_SENTINELA_GRAPHITI`, `RIU_SENTINELA_EXEC`, `RIU_WATCHDOG_RESTART_SPACE` | variables (opcionales, de ramas sin integrar) | anclaje Graphiti de la Constitución, sandbox del anclaje real, reinicio del Space por el watchdog |

Las claves de modelos NO son secretos del Space: se cargan en el vault desde el chat (pestaña de claves) y quedan cifradas con `RIU_VAULT_PASSPHRASE`.

## Entorno del agente Grok Bot (box)
| Nombre | Uso |
|---|---|
| `HF_TOKEN` | bucket, reinicio del Space, `HANDOFF/actualizar.py` |
| `FICHA_CLAVE_BANCO` | clave de acceso al banco de fichas/vault desde el agente |
| `GITHUB_TOKEN` (opcional) | más cuota de API para `actualizar.py` |
| Conectores GitHub y Vercel | se conectan en el chat de Grok Bot, sin variable |

Pendiente con el sí de Antonio: rotar las claves pegadas en el chat y borrar `/workspace/.model_keys.env` del box viejo.
