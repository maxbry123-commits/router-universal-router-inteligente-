# PARCHE DE RECUPERACION 4 - BANCO (2026-10-12)
Nunca lleva claves aqui.
1. BANCO OPERATIVO UNIFICADO = plugins/fichas_qwen/sellos/proveedores.sello. Clave de apertura: secreto del job FICHA_CLAVE_BANCO.
2. Formato: cabecera FICHA-SELLO-1 + salt16 + nonce12 + AESGCM (scrypt n=2**15, r=8, p=1). Contenido JSON por proveedor: nvidia (5 cuentas), groq (7), qwen (1).
3. Lectura unica: integration/chat_mvp/vault_hook.py -> _banco_unico(provider) -> provider_keys -> providers.env_keys, que usan las fichas modelo-nv-* y modelo-groq-* (claves:"banco").
4. Los tokens de HF y GitHub NO van en este banco: son secretos del job.
5. El kernel sigue abriendo el banco viejo del bucket (banco/vault.db.gz.b64, montado en /vault) con RIU_VAULT_PASSPHRASE para rearmar los secretos del Router al relanzar.
6. Regenerar el sello: cifrar el JSON con la misma cabecera y clave, guardar en sellos/proveedores.sello y comprobar la longitud de cada clave antes de cifrar.
