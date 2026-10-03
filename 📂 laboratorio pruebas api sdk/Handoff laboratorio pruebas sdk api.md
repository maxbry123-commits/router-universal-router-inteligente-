# Handoff: laboratorio pruebas SDK / API
Actualizado: 2026-10-03. Quien continue: lee primero `README pruebas.md` de esta carpeta.

## Conexiones
| Pieza | Donde | Estado |
|---|---|---|
| Motor | `Laboratorio Code de pruebas.py` | escrito por GPT; sin ejecutar |
| Plugin | `router inteligente universal/plugins/openai_sdk_lab/` | subido 2026-10-03; apagado por defecto |
| Banco | `vault_hook.provider_keys("openai")` | 14 claves segun el commit agent 30; sin verificar |
| Router | LIVE_URL en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` | vivo (health 200 el 2026-10-03) |
| Arquitectura | `Readme arquitectura router inteligente universal/` y `router inteligente universal/HANDOFF-CABLEADO.md` | sin cambios |

## Flujo
`LABORATORIO -> PLUGIN HOST -> PLUGIN -> VAULT_HOOK -> BANCO -> OPENAI -> RESUMEN SIN CLAVES -> RESULTADOS`

## Pendiente (en orden)
1. Clave del Router (X-API-Key) del Director: no esta en el repo; solo en secretos de GitHub.
2. Correr los 4 pasos del README y anotar el resultado en el README.
3. Si PASS: los agentes usan el SDK por el Router con el proveedor openai (grupo sdk de policies.json). Verificarlo en la misma corrida.
4. Laboratorio temporal: al terminar, `POST /plugins/openai_sdk_lab/disable`.

## GAP
- `openai` no esta en los pip del Router: el plugin lo instala la primera vez; tras relanzar el Job se reinstala solo. Para dejarlo fijo, anadir `openai` a los pip del guardian.
- Un commit anterior (ci: trigger secure OpenAI probe) sugiere GitHub Actions, que esta prohibido. Sin verificar.

## Reglas
Sin GitHub Actions, sin LFS, sin Jobs nuevos, sin tocar el nucleo del Router, sin claves en el repo.
