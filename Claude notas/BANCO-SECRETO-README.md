# BANCO SECRETO — README para otros entornos de Claude (2026-09-20)

Regla del Director: las claves NO van a GitHub Secrets ni al chat ni a archivos. Van al banco propio (YAIWES Secret Bank).
Diseño completo: `PLAN-ANEXO-A-SECRET-BANK.md`. Código: `Chat Mvp/secret_bank/` (`vault.py`, `session.py`, `broker.py`) y sus tests en `Chat Mvp/tests/test_secret_bank.py`.

## Qué es
- Una base SQLite cifrada (`vault.db`): cada valor con AES-256-GCM; la clave sale de la contraseña maestra con scrypt y nunca se guarda (solo vive en memoria mientras la sesión está abierta).
- Cada clave se identifica con un `credential_ref` = `proveedor/cuenta` (ejemplos: `nvidia/digi-maxbry`, `github/planeta123`, `github/abc1tienda-web`, `huggingface/primary`).
- El Router y los agentes usan el `credential_ref`; el broker resuelve la clave por dentro. Un agente recibe la respuesta, nunca la clave. No existe una función pública para "leer" una clave.
- El archivo `vault.db` vive FUERA de git (el repo es público): en el almacenamiento privado de `COMAND-CENTER-1` (bucket/disco del Space), no en el repo.

## Cómo accede otro entorno de Claude
1. Nunca pidas ni repitas una clave. Si el Director pega una en el chat: no la uses, no la guardes, no la copies a ningún archivo y dile que la cargue en el banco.
2. Para usar una clave: pide al broker con el `credential_ref` (ver `broker.py`). Para gestionar el banco (poner, rotar, listar, auditar) hace falta la contraseña maestra, que solo tiene el Director. Claude no la guarda.
3. API del vault (leída en `vault.py`): `Vault(ruta).initialize(passphrase)` crea el banco (mínimo 12 caracteres); `Vault(ruta).unlock(passphrase)` lo abre; abierto: `put(ref, secreto, ...)`, `rotate(ref, nuevo)`, `list()`, `get_record(ref)`, `set_enabled`, `delete`, `audit_log()`. Cada uso queda auditado sin el valor.
4. Cada credencial puede limitarse por agentes, modelos y rutas permitidos.

## Estado real (2026-09-20)
- Hecho: núcleo del banco (vault, sesión, broker) con tests, según la nota de otro chat (`RIU-0110`); no re-ejecutado aquí.
- NO hecho: banco inicializado (falta la contraseña maestra del Director y el lugar privado), pantalla `/vault` del chat, y cableado del broker en el gateway y el chat (pasos S2.4 y S2.5).
- Mientras tanto, los workflows del repo siguen usando las claves ya cargadas en GitHub Actions Secrets (arranque). Por orden del Director NO se añaden más ahí.
- Claves pendientes de cargar en el banco: `github/planeta123` (token nuevo), `github/abc1tienda-web` (token nuevo). Los valores pegados en el chat NO se guardaron en ningún sitio.

## Recomendación
Rotar las claves que se pegaron en el chat (GitHub, Hugging Face y NVIDIA) y cargar las nuevas en el banco.
