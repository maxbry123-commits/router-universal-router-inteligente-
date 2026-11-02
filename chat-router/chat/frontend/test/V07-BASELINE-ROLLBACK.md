# V07 · Salida 1/10 — Protección antes de modificar la UI

**Rama:** main. **Punto de partida:** `13ec88d06e4d4b5c5b60cc718e3d0e652dd0f103` (consultado 2026-11-02).
**Restricción:** exclusivamente `chat-router/chat/frontend/`; no tocar `shell.html`, `shell.js`, Python, Hugging Face ni Vercel. No duplicar el anclaje ⚓, Canvas o los motores.

**Skill fuente:** `chat-router/workflow-loop-code-yaiwes/skills/workflow-loop-yaiwes/fromted-yaiwes-frontend-factory/😄SKILL.md`. Su README fija la variante gris V07, estados funcionales azules únicamente tras confirmación.

## Ejecutar gates antes/después de cada segmento
```bash
cd chat-router/chat/frontend
node --test test/v07-proteccion.test.mjs
```

Se protegen los cuatro paneles A/B/C/D, las dependencias HTML, ID únicos, rollback, el mismo origen de `postMessage`, ausencia de credenciales en iframe, anclaje universal, revisiones DSL, no generar 50 pasos por defecto y rutas del despliegue existente.

## Retorno quirúrgico sin force push
- Mantener la ruta y el commit exactos de cada cambio; comparar `git diff` por archivo.
- Restaurar **un único archivo** si hay un GAP, siempre conciliando primero trabajo concurrente:
```bash
git restore --source=13ec88d06e4d4b5c5b60cc718e3d0e652dd0f103 -- chat-router/chat/frontend/NOMBRE_DEL_ARCHIVO
```
- Validar y crear commit normal. Nunca hacer hard reset/force-push de main.

**Estado de esta salida:** se añaden pruebas y documentación; no se cambia el chat ejecutable. Los gates estáticos no son pruebas E2E de Vercel/Hugging Face ni cubren móvil 360/390/430px.
