# OAuth — 5 MCP pendientes (G2)

| MCP | Env var | URL emisión |
|-----|---------|-------------|
| supabase | `SUPABASE_ACCESS_TOKEN` | https://supabase.com/dashboard/account/tokens |
| notion | `NOTION_TOKEN` | https://www.notion.so/my-integrations |
| stripe | `STRIPE_SECRET_KEY` | https://dashboard.stripe.com/apikeys |
| sentry | `SENTRY_AUTH_TOKEN` | https://sentry.io/settings/account/api/auth-tokens/ |
| linear | `LINEAR_API_KEY` | https://linear.app/settings/api |

**Cómo resolver:** exportar la env var en el Space `space-grupo-1-router-mvp-1` (Settings → Secrets) → re-ejecutar `python scripts/oauth_setup_runner.py --phase=scan`.  
El pool pasa el MCP de `oauth_pending` → `ready` automáticamente. **No bloqueante.**
