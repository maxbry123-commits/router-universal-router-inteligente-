# Importar sesión web autorizada (storageState) — sin eludir captcha

Cuando `/web/v1/web/diagnostico` muestre `RETO_ANTIBOT`, `LOGIN_RECHAZADO_TODAS_CUENTAS` o `SIN_SESION_EN_PERFIL`, el titular:

1. En SU PC: `npx playwright codegen --save-storage=qwen.json https://chat.qwen.ai/` (o deepseek / claude.ai), inicia sesión y resuelve la verificación oficial a mano, cierra la ventana.
2. Envía al bridge (clave de acceso del chat):
```
curl -X POST "https://comand-center-1-riu-router.hf.space/web/v1/web/sesion/importar" \
  -H "X-API-Key: $CLAVE" -H "content-type: application/json" \
  -d "{\"site\":\"qwen\",\"storageState\":$(cat qwen.json)}"
```
Sitios: `qwen`, `deepseek`, `claude`. Solo se aceptan cookies del dominio del sitio; se inyectan en el perfil Chromium persistente existente y se verifica con `asegurar()`. Respuesta: `SESION_IMPORTADA_Y_VERIFICADA` o `SESION_IMPORTADA_PERO_NO_VALIDA` + motivo. Nunca se registran valores.
