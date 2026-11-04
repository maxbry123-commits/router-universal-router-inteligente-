# Importar sesión web autorizada — storageState / cookies / tokens

Cuando `/web/v1/web/diagnostico` muestre `ESPERANDO_LOGIN`, `RETO_ANTIBOT`,
`SSO_REQUIERE_IMPORT`, `LOGIN_RECHAZADO_TODAS_CUENTAS` o `SIN_SESION_EN_PERFIL`,
**el titular** aporta una sesión ya autenticada. El bridge **no** usa `WEB_PASS`
por defecto (sin churn de login). Claude nunca usa password del pool.

## 1) Exportar en tu PC

```bash
# Desde el repo (o copia export-sesion.js):
node "chat-router/SWE CODE free/export-sesion.js" qwen ./qwen.json
# deepseek | claude igual
```

Alternativa Playwright codegen:

```bash
npx playwright codegen --save-storage=qwen.json https://chat.qwen.ai/
```

Inicia sesión, resuelve captcha/OTP/age-gate a mano, cierra la ventana.

## 2) Importar al Space

`POST /web/v1/web/sesion/importar` (clave de acceso del chat).

### Formatos aceptados

| Formato | Body |
|---|---|
| Playwright storageState | `{ "site":"qwen", "storageState": { "cookies":[...], "origins":[...] } }` |
| Cookie JSON array | `{ "site":"qwen", "cookies":[ {"name","value","domain",...} ] }` |
| Cookie header | `{ "site":"qwen", "cookie":"a=1; b=2" }` o header `X-Session-Cookie` |
| Netscape cookies.txt | `{ "site":"qwen", "netscape":"# Netscape..." }` |
| Claude sessionKey | `{ "site":"claude", "sessionKey":"..." }` |
| DeepSeek userToken | `{ "site":"deepseek", "userToken":"..." }` |
| Qwen token | `{ "site":"qwen", "token":"..." }` |

### Ejemplo curl

```bash
curl -X POST "https://comand-center-1-riu-router.hf.space/web/v1/web/sesion/importar" \
  -H "X-API-Key: $CLAVE" -H "content-type: application/json" \
  -d "{\"site\":\"qwen\",\"storageState\":$(cat qwen.json)}"
```

### Respuesta

```json
{ "ok": true, "sitio": "qwen", "expira": "2026-12-01T00:00:00.000Z", "code": "SESION_IMPORTADA_Y_VERIFICADA" }
```

o `{ "ok": false, "sitio", "expira", "code": "SESION_IMPORTADA_PERO_NO_VALIDA", "motivo" }`.

Tras OK se valida con profile API (vía 14) y se guarda atómico en
`/data/state/sesiones/<sitio>.json` (persistente HF).

Sitios: `qwen`, `deepseek`, `claude`. Solo cookies del dominio del sitio.
Nunca se registran valores de cookies/tokens en logs.
