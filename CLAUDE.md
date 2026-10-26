# Reglas obligatorias para Claude en este repositorio

Antes de modificar el frontend, inspecciona sus componentes, dependencias, eventos y conexiones HTTP. Conserva las funcionalidades existentes. Modifica exclusivamente los archivos autorizados. Ejecuta las pruebas correspondientes y muestra los resultados reales antes de declarar PASS. No cambies el backend ni la arquitectura sin autorización expresa.

- Arquitectura y ley: `docs/ARQUITECTURA.md`. Controles del chat: `docs/CHAT_CONTROLES.md`.
- Pruebas reales de los modelos: `docs/PRUEBAS_SOL.md` (clonar siempre con `--branch main`).
- Los cambios del frontend anteriores a la reversión están guardados en `docs/legado/frontend_cambios_claude/`.
