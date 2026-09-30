# banco (bloque4) - Banco secreto listo para 15 SDK

Archivos: integration/chat_mvp/vault_bridge.py (editado), integration/chat_mvp/providers.json (nuevo), tests/test_vault_providers_autolock.py (nuevo).

## Uso por cada SDK nuevo (sin tocar codigo)
1. Una linea en providers.json, dentro de "providers": "acme": {"env": "ACME_API_KEY", "base_url": "https://...", "auth": "bearer"}. Solo el nombre es obligatorio; vault_provider por defecto = nombre; auth: bearer|x-api-key|header|query|none. Se recarga solo al cambiar el archivo (sin reiniciar). Entrada invalida = se salta; archivo roto/ausente = mapa de 6 proveedores del codigo.
2. Con el Router vivo: POST /vault/unlock {passphrase}; luego POST /vault/credentials {"ref": "acme/cuenta", "secret": "<clave>"} (ref = <vault_provider>/<cuenta>, minusculas). Ningun endpoint devuelve la clave.
3. Los consumidores leen vault_hook.provider_keys("acme"). Varias cuentas = varias claves (la mas antigua primero).

## Autolock
RIU_VAULT_AUTOLOCK_S: 0 = nunca (DEFECTO, 24/7). 3600 = 1 h. RIU_VAULT_TTL antiguo se respeta si AUTOLOCK no esta. /vault/status muestra autolock_s y ttl_seconds (null = sin cierre).

## Como se guarda (leido del codigo)
SQLite + AES-256-GCM por valor, clave scrypt de la contrasena maestra (nunca guardada). Sin logs de valores. Test: el secreto no aparece en el .db, respuesta, status ni logs.

## Pendiente / limites
- Tras reiniciar el proceso el banco vuelve a estar cerrado: hay que POST /vault/unlock otra vez (la contrasena no se guarda).
- providers.py (PROVIDERS del chat) sigue siendo una lista en codigo: un SDK nuevo aparece en el banco con 1 linea JSON, pero para usarlo como modelo en el chat hace falta su entrada alli (no tocado, cambio quirurgico).
- Con autolock 0 las claves quedan en memoria mientras el proceso viva.
