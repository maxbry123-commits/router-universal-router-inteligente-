# Conectar un SDK/API nuevo (y meter sus claves) - procedimiento leido del codigo real

Fuente: integration/chat_mvp/vault_api.py, vault_bridge.py, vault_hook.py y Banco de claves/secret_bank/vault.py (2026-09-30). Volver al [README](README.md).

## Respuesta corta sobre las 15 claves
El banco NO se puede llenar desde fuera del Router: no hay archivo ni comando offline en el repo para escribir claves. Las claves entran por HTTP en /vault/credentials con el Router vivo, con la API key del Router y la contrasena maestra para abrir el banco. La clave viaja solo en el cuerpo de la peticion (HTTPS), nunca en el repo ni en un archivo.

## Como se guarda una credencial (real)
1. Abrir el banco: POST /vault/unlock con {"passphrase": "..."} (cabecera X-API-Key = API key del Router). La contrasena solo abre el banco en memoria; 5 fallos bloquean 10 minutos; se cierra solo tras RIU_VAULT_TTL (1 h por defecto). Tambien hay una pagina /vault en el navegador (sirve desde el telefono).
2. Guardar: POST /vault/credentials con {"ref": "proveedor/cuenta", "secret": "<clave>", "scope": "inference"}. El ref debe cumplir ^[a-z0-9][a-z0-9_.-]*/[a-z0-9][a-z0-9_.-]*$ (minusculas). El secreto admite 1 a 4096 caracteres. Ningun endpoint devuelve el secreto; solo lista los ref.
3. Rotar: POST /vault/rotate con el mismo cuerpo. Importar en bloque: POST /vault/import con {"b64gz": "..."} (base64 de un gzip); el formato interno del gzip NO lo verifique: leer vault_bridge.import_b64gz antes de usarlo.
4. Cifrado: SQLite + AES-256-GCM por valor, clave derivada con scrypt de la contrasena maestra (nunca guardada). Archivo: variable RIU_VAULT_PATH o /data/riu_vault.db (o riu_data/riu_vault.db si /data no es escribible).

## Quien consume la clave
- vault_bridge.PROVIDER_MAP hoy solo conoce: nvidia, hf (ref huggingface/...), groq, deepseek, moonshot, minimax. Mientras el banco esta abierto, esas claves se suman al conjunto de claves del proveedor (la mas vieja primero) via vault_hook.provider_keys(nombre). Las de scope github se exportan como variables de entorno del proceso.
- Un SDK nuevo con un proveedor fuera de ese mapa SE GUARDA bien, pero nadie la lee hasta: (a) agregar UNA linea a PROVIDER_MAP en vault_bridge.py (edicion quirurgica del vivo, decision del Director), o (b) que su plugin la pida directo al banco. La plantilla plugins/_plantilla_sdk usa vault_hook.provider_keys(PROVIDER), o sea necesita (a).
- No verifique si vault.py tiene lista cerrada de proveedores o de scopes: confirmarlo con una prueba de /vault/credentials con una clave de mentira.

## Pasos para cada SDK nuevo
1. Copiar plugins/_plantilla_sdk a plugins/<id>/ (id minusculas, igual a la carpeta, patron ^[a-z0-9][a-z0-9_-]{0,39}$); reemplazar todos los CAMBIAR; conservar enabled_default false. La carpeta con _ la ignora el host.
2. Rellenar conecta_con.plugin_anterior con el id del ultimo plugin de la cadena (regla propuesta en HANDOFF-CABLEADO.md; hoy el host no la lee).
3. Validar con el host: python3 -c con integration.plugin_host.host.check_v1(ficha, id); debe devolver lista vacia (codigos H00-H11 si falla).
4. Con el Router vivo: /vault/unlock y luego /vault/credentials con ref <proveedor>/<cuenta>.
5. Si hace falta en la cadena de modelos: agregar el proveedor al grupo de integration/chat_mvp/policies.json (el campo sdk esta esperando la lista del Director).
6. Encender con POST /plugins/<id>/enable solo cuando el Director lo ordene. El host lee las fichas al arrancar o con reload: si el Router no recarga solo, hace falta el reinicio unico o el boton de recarga (decision pendiente del Director).

## Limite que conviene decidir
El banco se cierra solo (TTL) y tras cada reinicio del Router queda cerrado: para operar 24/7 alguien debe abrirlo de nuevo o se sube RIU_VAULT_TTL. No se escribe ninguna clave ni contrasena en el repo.
