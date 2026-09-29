# Handoff de Vercel (rutas)
Actualizado: 2026-09-29. Solo hechos verificados.

- Cuenta: `maxbry123@gmail.com` · usuario `maxbry123-8833` · plan Hobby · team `maxbry123-8833s-projects` (`team_hG9df7zIgfZFY0oxFFsIRr1u`).
- Proyecto: `riu-jev-bridge` (`prj_m8Lk3iaB3eN6dwlIq1ND2un8FWTD`). Sin despliegue vivo; despliegue automático apagado.
- Variables (solo nombres): `RIU_CHAT_PASSWORD`, `RIU_ROUTER_API_KEY`, `RIU_ROUTER_URL`, `HF_JOB_FLAVOR`, `HF_TOKEN_1`. No se borraron.
- Rutas en este repo:
  - `Vercel/vercel-chat/` — la pantalla del chat.
  - `vercel.json` (raíz) — apunta a `router inteligente universal/vercel-ui`.
  - `router inteligente universal/vercel-jev-bridge/` — puente hacia el Router.
- El chat solo habla con el Router único (`RIU_ROUTER_URL`).
- Regla: Vercel = solo pantalla; no instalar nada hasta que todo esté listo; un único despliegue final, solo con orden del Director.
- Nota de nota: con el árbol nuevo, Vercel debe apuntar a la carpeta correcta al desplegar (revisar `Vercel/vercel-chat` frente a `vercel-ui` antes del deploy).
