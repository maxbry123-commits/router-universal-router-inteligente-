# ADENDA A LA ARQUITECTURA — RIU-0110 — Secret Bank implementado (núcleo) — 2026-09-20

Anclas: `../Chat Mvp/secret_bank/` · `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0110-AVANCE-S0-S1-S2.md`. No modifica `README.md`.

## Lo que existe y está probado (9 tests en runner real, check-run `106037887491`)
- Vault: un archivo SQLite (`vault.db`) con tablas `meta`, `credentials`, `audit`. Cada valor va cifrado con AES-256-GCM (nonce aleatorio de 12 bytes por valor); el identificador `proveedor/cuenta` viaja como dato asociado, así que un valor cifrado no se puede pasar a otra fila (el intento falla con `CREDENTIAL_DECRYPT_FAILED`).
- Clave: derivada con scrypt (n=2^15, r=8, p=1 por defecto) de la contraseña maestra (mínimo 12 caracteres) y una sal aleatoria; nunca se guarda; solo vive en memoria dentro de la sesión. Un verificador cifrado detecta la contraseña incorrecta.
- Sesión: `login` una vez → id aleatorio de 256 bits con TTL; mientras dura, el broker no pide la contraseña otra vez.
- Broker: `with_secret(session, credential_ref, agent, model, route, fn)`. El secreto solo llega a `fn`; el agente recibe el resultado, no la clave. Las listas de agentes, modelos y rutas permitidos son fail-closed: vacía deniega, `*` permite todo. Se comprueba habilitada y caducidad.
- Auditoría: eventos PUT, ROTATE, ENABLE, DISABLE, DELETE, USE y DENIED, sin valores.
- La copia de `vault.db` es restaurable con la contraseña; sin ella no revela nada. Por eso es seguro guardarla en un repo privado de Hugging Face.

## Lo que NO existe todavía
API HTTP, integración con el gateway (sigue leyendo `HF_TOKEN` del entorno), página `/bank`, copia automática a HF, passkey/WebAuthn.

## Límites honestos
Cifrado a nivel de aplicación con librería estándar (`cryptography`); no es SQLCipher (decisión D3 aprobada por el Director). Quien tenga la contraseña maestra y el archivo tiene las claves. Al reiniciar el proceso hay que iniciar sesión otra vez. La sesión guarda la clave en memoria del proceso.
