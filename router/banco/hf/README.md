# Banco del router (copia en GitHub)

Fuente de verdad del inventario de conexiones y de las credenciales del router.

| Fichero | Qué es |
|---|---|
| `CONEXIONES_ROUTER_10H_10M.json` | Las **10 HTTP** y los **10 MCP** del router: ruta, método, consumidor, auth, estado real y `value_ref` |
| `CONEXIONES_ROUTER_10H_10M.md` | Lo mismo en Markdown, para leerlo de un vistazo |
| `PENDIENTES_SALDO.json` | Cola de lo que necesita crédito de HF o una credencial del owner, con el comando exacto |
| `secrets.json` | Índice legible: qué hay, de qué tipo y si falta |
| `vault.json` | Sobre cifrado con las claves de proveedor (AES-256-GCM, scrypt n=2^15) |

## Lo que NO está aquí

- **La clave maestra**: vive solo en `HF_VAULT_KEY` (= `$UNIVERSAL_KEY`) y en los Secrets de HF. `vault.json` es ciphertext; sin la clave no se abre.
- **Ninguna clave en claro**: este directorio solo tiene rutas, nombres de variable y estados. El gate de seguridad está en `scripts/verify_banco.py`.

## Dónde vive el original

Bucket privado de HF: `hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage/banco/`
(los mismos 5 ficheros, verificados con `sha256` en cada publicación).

## Cómo el proxy recupera sus claves

El Space del proxy ya tiene `HF_VAULT_KEY` y clona este repo, así que el sello
cifrado `fichas/fichas_qwen/sellos/proveedores.sello` viaja con el código:
`external/core/bank_keys.py` lo descifra al arrancar y deja `NVIDIA_KEYS`,
`GROQ_KEYS` y `QWEN_API_KEY` en el entorno (fail-open: si algo falla, el proxy
arranca igual y lo dice en el `diag`).

## Estados a 2026-11-18

- 10 HTTP: 10/10 presentes en el código del proxy; 0/10 vivas (los Spaces están PAUSED por cuota de HF).
- 10 MCP: 3 con credencial (github, playwright, filesystem) · 7 pendientes del owner (context7, firecrawl por api_key; supabase, notion, stripe, sentry, linear por oauth).
- 18 adapters en HF (14 de código + 4 de servicio).
