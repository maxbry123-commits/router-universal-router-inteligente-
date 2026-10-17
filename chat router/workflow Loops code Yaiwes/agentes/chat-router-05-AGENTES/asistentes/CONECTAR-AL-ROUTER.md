# Conectar Hermes y OpenClaw al Router

Idea: Hermes y OpenClaw no eligen modelo ni llaves. Hablan con el Router y el Router aplica la regla del Director (NVIDIA primero, rotando las llaves 1-4; si están ocupadas salta a GLM, Groq, DeepSeek y Nemotron al final). Grupo del Router: `assistants`.

## Lo que ya está hecho (puente Python)
`puente_asistentes.py` ya no llama a NVIDIA. Usa `colmena/router_cliente.py` con `group="assistants"` -> `POST <RIU_ROUTER_URL>/chat/route` con `{"group":"assistants","message":...}` y lee `reply`. En `SIMULADO=1` no toca la red.

## Lo que debe dar el Director (sin escribir valores aquí)
- `RIU_ROUTER_URL`: URL viva del Router (la del job de Hugging Face).
- `RIU_ROUTER_API_KEY`: la llave del Router (va en la cabecera `X-API-Key`).
- `HF_TOKEN`: solo si la URL es el job `https://<job>--8000.hf.jobs` (el proxy pide `Authorization: Bearer <HF_TOKEN>`).
- Requisito: la puerta `/v1/router/*` (fichero `openai_route.py`) debe estar en main y desplegada; hoy solo está en un clon local.

## Hermes (v2026.9.24) -> `~/.hermes/config.yaml`
Verificado en `website/docs/integrations/providers.md` (Custom Endpoint, `providers:` con `api`, `key_env`, `extra_headers`, `default_model`):
```yaml
model:
  provider: router-yaiwes
  default: assistants
providers:
  router-yaiwes:
    api: https://<RIU_ROUTER_URL>/v1/router
    key_env: HF_TOKEN            # Hermes lo manda como Authorization: Bearer (lo pide el proxy HF)
    transport: chat_completions
    extra_headers:
      X-API-Key: "<valor de RIU_ROUTER_API_KEY>"   # UNVERIFIED: si extra_headers acepta ${VAR}; si no, poner el valor en el config privado, nunca en git
```
Alternativa mínima (docs: `provider: custom` con `base_url` y `api_key`): `base_url: <RIU_ROUTER_URL>/v1/router`, `api_key: <clave>`, `default: assistants`. UNVERIFIED: que esa forma envíe `X-API-Key`; el Router hoy exige esa cabecera, por eso se recomienda `extra_headers`.

## OpenClaw (v2026.9.6) -> config del gateway
Verificado en `docs/gateway/local-models.md` (proveedor propio con `baseUrl`, `apiKey`, `api: "openai-completions"`, `models[].id` sin prefijo):
```json5
{
  agents: { defaults: { model: { primary: "router/assistants" } } },
  models: {
    mode: "merge",
    providers: {
      router: {
        baseUrl: "https://<RIU_ROUTER_URL>/v1/router",
        apiKey: "<valor de RIU_ROUTER_API_KEY o HF_TOKEN>",   // la doc menciona sustitución ${VAR} (docs/gateway/configuration.md); sintaxis exacta UNVERIFIED
        api: "openai-completions",
        timeoutSeconds: 300,
        models: [{ id: "assistants", name: "Router assistants", reasoning: false, input: ["text"],
                   contextWindow: 120000, maxTokens: 8192 }]
      }
    }
  }
}
```
UNVERIFIED: cómo añadir la cabecera `X-API-Key` en un proveedor de OpenClaw (no encontrada en las docs leídas). Sin ella, `apiKey` viaja como `Authorization: Bearer`. Si el Router solo acepta `X-API-Key`, hace falta una de dos: cabecera personalizada (a confirmar) o que el Router acepte también Bearer en `/v1/router`.

## Limitaciones
- `/v1/router/chat/completions` no hace streaming (devuelve JSON normal); si el cliente exige streaming, fallará: UNVERIFIED en ambos.
- Modelos válidos en la puerta: `assistants`, `auto` (= `default`) y los demás grupos; `kimi-k3` ya no se usa en ninguna parte.
