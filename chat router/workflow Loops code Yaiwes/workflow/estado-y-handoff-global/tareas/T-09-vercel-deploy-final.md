# T-09 — Un solo despliegue final en Vercel
**Estado:** BLOQUEADO POR ORDEN DEL DIRECTOR · **Depende de:** T-08 · **Nodo:** N-09 · **Paso P4 (último)**

## Qué es, en palabras simples
Publicar los chats como una sola página "Riu". Es lo ÚLTIMO y solo cuando tú lo ordenes. Vercel es solo pantalla; el trabajo real lo hace el Router.

## Cuenta y proyecto (verificado)
- Cuenta `maxbry123@gmail.com` (usuario `maxbry123-8833`, plan Hobby), team `maxbry123-8833s-projects`.
- Proyecto `riu-jev-bridge` (`prj_m8Lk3iaB3eN6dwlIq1ND2un8FWTD`). Despliegue automático apagado: los últimos intentos salen CANCELED.
- Variables (solo nombres): `RIU_CHAT_PASSWORD`, `RIU_ROUTER_API_KEY`, `RIU_ROUTER_URL`, `HF_JOB_FLAVOR`, `HF_TOKEN_1`.

## Antes del deploy
1. Ver `Vercel/HANDOFF-VERCEL.md` (rutas y qué carpeta se publica).
2. `vercel.json` sigue en la raíz: apunta a `router inteligente universal/vercel-ui`. Confirmar carpeta final del chat antes de publicar.
3. Decidir con el Director qué pasa con las variables (conservar o borrar).
4. Una sola publicación, con su orden.

## No hacer
Instalar nada en Vercel antes de que todo esté listo. Publicar más de una vez. Borrar las variables sin tu decisión (son irrecuperables).
