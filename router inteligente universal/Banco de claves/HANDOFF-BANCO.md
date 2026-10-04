# HANDOFF — BANCO DE SECRETOS (fuente de la verdad)

Actualizado: 2026-10-03 (Opus). Manual general: `router inteligente universal/MANUAL-AGENTES.md`.

## Qué es

- **Un solo banco** con todas las claves de APIs y SDK (NVIDIA, Groq, OpenAI, Hugging Face, GitHub...) y el registro de tokens de agentes.
- Está **cifrado** con la clave maestra del Director. Nadie ve las claves: el Router las usa por dentro.
- Vive en el almacenamiento permanente de HF, dentro de la raíz del Router. No existe ningún otro banco activo.

## Dónde vive

Bucket privado `COMAND-CENTER-1/yaiwes-memoria-storage` → `router-inteligente-universal/banco/`:

| Archivo | Qué es |
|---|---|
| `vault.db.gz.b64` | el banco cifrado (lo único que contiene claves, siempre cifradas) |
| `vault.db.gz.b64.bak-AAAAMMDDHHMM[SS]` | copias automáticas antes de cada cambio |
| `providers.json` | qué API es cada proveedor y su `base_url` (sin claves) |
| `tokens.json` | tokens de agentes: **solo huellas sha256**, nombre, permisos, límite, ficha, activo |
| `archivo-bancos-viejos/` | un banco viejo (2026-09-21, otra clave maestra) guardado por si tenía claves; no se usa. Borrarlo solo si el Director lo confirma |

Código: `router inteligente universal/Banco de claves/secret_bank/vault.py` (núcleo), `integration/chat_mvp/vault_bridge.py`, `vault_api.py`, `control_plane.py` (banco vivo), `tokens.py`.

## Cómo lo usa el Router (automático)

1. Al arrancar, el Router baja `vault.db.gz.b64` y lo abre con la clave maestra (secreto `RIU_VAULT_PASSPHRASE` del Space; nunca en archivos).
2. Cada **5 minutos** lo relee: si alguien agregó o cambió claves, las usa **sin reiniciar**.
3. Para cada proveedor rota entre todas sus claves; si una falla, pasa a la siguiente y luego al siguiente proveedor de la cadena.
4. `providers.json` también se relee: una API nueva tipo OpenAI aparece sola en el catálogo, el laboratorio y las fichas.

## Contenido al 2026-10-03 noche (42 claves)

openai 14 (válidas, **sin saldo**) · github 12 · groq 6 (la groq-1 se borró por inválida) · nvidia 5 · huggingface 4 · router 1 (clave del harness).

- El Director entregó el 2026-10-03 sus tokens de GitHub y Hugging Face; quedaron en el banco con nombres claros (`github/full-acceso`, `github/acceso-total-pat`, `github/clasico-claude-1`, `github/full-acceso-2`, `github/cuenta-maxbry123`, `github/cuenta-abc1tienda-web`, `github/cuenta-planeta123-usa`, `huggingface/token-1-new`, `huggingface/mcp-claude-permanent`, `huggingface/maxbry123`).
- Comprobado ese día: 4 tokens de GitHub tienen acceso total (admin) a este repo; `abc1tienda-web` y `planeta123-usa` solo lectura; `github/cuenta-maxbry123` **inválido** (401). `huggingface/token-1-new` lee y escribe el almacenamiento del Router.
- **Regla:** cuando un agente o el Router necesita un token, lo saca del banco. No se le pide de nuevo al Director.
Estado vivo sin claves: `Ventana status router inteligente universal/banco.json` y `GET <puerta>/vault/status`.

## Cómo agregar claves (solo el Director)

Todas estas llamadas exigen la cabecera `X-Director-Key`. El banco se guarda solo en HF con copia de respaldo.

**Una clave de un proveedor que ya existe** (ej. otra de NVIDIA):
```bash
curl -s -X POST <puerta>/vault/credentials -H "X-API-Key: <clave del Router>" -H "X-Director-Key: <clave del Director>" \
  -H "Content-Type: application/json" -d '{"ref": "nvidia/cuenta-nueva", "secret": "<la clave>", "scope": "inference"}'
```
- `ref` = `proveedor/nombre` en minúsculas (`nvidia/...`, `groq/...`, `openai/...`, `huggingface/...`).
- En ≤ 5 minutos el Router la está usando (o al instante si se relanza).

**Cambiar una clave:** igual pero en `/vault/rotate` con el mismo `ref`.

**100 claves de una vez:** repetir la llamada (un script de 100 líneas) o importar un banco completo con `/vault/import`.

**Un proveedor nuevo** (API tipo OpenAI que el Router aún no conoce):
1. Agregar su entrada en `banco/providers.json`. **No hay ruta HTTP para esto**: es un archivo del almacenamiento HF y solo lo edita el Director (o un agente con su orden explícita) con un token HF del banco (`huggingface/token-1-new`), bajando el archivo, agregando la línea y subiéndolo. Ejemplo de entrada:
   `"mistral": {"base_url": "https://api.mistral.ai/v1", "env": "MISTRAL_API_KEY"}` (`env` es solo el nombre de respaldo de la variable; las claves salen del banco).
2. Agregar su clave con `/vault/credentials` (`ref: "mistral/principal"`).
3. Listo: en ≤ 5 minutos aparece en `GET /fichas/catalog` y se usa con `model: "mistral:<modelo>"`.

**Cabeceras de todas las rutas del Director:** tu token (`Authorization: Bearer riu_...` o `X-API-Key`) **y** `X-Director-Key`. Pon ambas en variables de entorno, no en archivos.

**Errores y límites:** `ref` repetido → `409` (usa `/vault/rotate`). No existe ruta para borrar una clave: avisa al Director. Para muchas claves, máximo ~40 llamadas a la vez desde una máquina (más que eso, la puerta de HF responde `429`). Cada escritura deja una copia `.bak`.

## Cómo probar el banco

- `POST <puerta>/lab/run`: prueba **todas** las claves (3 pruebas cada una, numeradas N01..., sin mostrar claves). No hay filtro por proveedor; espera ≥ 5 min después de agregar claves para que el Router ya las tenga.
- `GET <puerta>/lab/last`: último informe. También en `Ventana status .../laboratorio.json`.

## Tokens de agentes (también en el banco)

- Se crean con `POST /tokens` (clave del Director). El banco guarda solo la huella; el token se entrega una vez.
- Detalle: `MANUAL-AGENTES.md`, sección 5.

## Reglas

- Nadie escribe claves en archivos, commits, chats ni memoria.
- Ningún agente agrega, cambia, importa ni bloquea claves sin la clave del Director (el candado lo impide).
- No crear otro banco. Si aparece uno, se archiva en `banco/archivo-bancos-viejos/` y se avisa al Director.
- Si la clave maestra se cambia, hay que actualizar el secreto `RIU_VAULT_PASSPHRASE` del Space y relanzar el Router.
