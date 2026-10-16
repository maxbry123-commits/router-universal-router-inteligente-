# Router Inteligente Universal — README

Actualizado 2026-10-16. Para handoff operativo: [HANDOFF-CABLEADO.md](HANDOFF-CABLEADO.md).

## ARQUITECTURA ACTUAL

Chat
→ Router
→ cómputo
→ almacenamiento

El Router:
- solo enruta/conecta;
- no contiene modelos;
- no contiene proveedores;
- no contiene las fichas;
- no decide los modelos.

Las fichas/plugins conservan su arquitectura existente.

## RUNTIME ACTUAL

- Space: `COMAND-CENTER-1/riu-router`
- URL: https://comand-center-1-riu-router.hf.space

## HARDWARE

- HF CPU Upgrade
- 8 vCPU
- 32 GB RAM
- 24/7
- sleep_time = -1

## ESTADO

- Router: RUNNING
- Chat: activo
- Cola existente: intacta
- Almacenamiento: intacto
- HF Router Jobs activos: 0
- HF scheduled Router Jobs: 0

## FUENTE DE DIRECCIÓN

`router inteligente universal/LIVE_URL.json` — única dirección viva del Router. El chat la lee y valida `*.hf.space`.

## Plugins

Todo lo demás sigue siendo plugin: una carpeta `plugins/<id>/` con `ficha.json` y `plugin.py` (función `handle(action, payload)`). El Plugin Host las lee, valida y llama por HTTP; si un plugin falla, solo ese queda marcado y el Router sigue.
