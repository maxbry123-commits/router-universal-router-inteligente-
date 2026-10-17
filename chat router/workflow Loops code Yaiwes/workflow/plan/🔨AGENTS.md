# AGENTS — FROMTED × YAIWES

Leer `README.md` + `SKILL.md` antes de editar. El perfil principal es `little`; no sobrescribir los documentos inmutables de la fuente. Mantener archivos originales, actualizar únicamente la pieza afectada, y no inventar paneles o APIs si existe referencia real.

**Ejecución:** REFERENCIA → CONTEXTO → IMPLEMENTACIÓN EDITABLE → SERVIDOR LOCAL → NAVEGADOR → CLICK/TOUCH → COMPARAR → CORREGIR → PRUEBAS → HANDOFF.

**Entrega mínima:** `index.html` + `styles.css` + `app.js` + `assets/` + `manifest.json` + `README.md` + `ACCEPTANCE.md` + tests. `snapshot/index-standalone.html` es solo respaldo/revisión; nunca la fuente canónica.

**Fail-closed:** `chat.send` llama a `window.YAIWES_PLUGIN_BRIDGE.execute(...)`; no respuesta sin confirmación. Los eventos locales `yaiwes:ui-action` no son evidencia de ejecución remota. Mantener secretos solo en backend. No fingir pruebas `PASS` que no se ejecutaron.

**Tema gris:** superficies grises, sin negro puro; indicadores verde progreso, azul encendido, rojo advertencia con contraste apropiado también en Little/Matte/Blanco/otros. La ampliación visual requiere aprobación del propietario.

**Versionado:** cada modificación: explicar archivos cambiados, prueba y gap en `VERSION.md` / `ACCEPTANCE.md`. Nunca afirmar que una demo HTML ya es React.
