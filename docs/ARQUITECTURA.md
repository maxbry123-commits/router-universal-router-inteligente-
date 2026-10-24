# Arquitectura YAIWES (resumen operativo de la ley, 23-oct-2026)

Texto íntegro de la ley: lo conserva Antonio; este archivo resume lo que el código debe cumplir. Todo lo no comprobado con una ejecución real se marca **NO VERIFICADO**.

## Dos edificios
- **Edificio 1 — Router** (`mvp/`, `router/`, `fichas/`): puerta única HTTP, banco de claves, permisos, ficha → prompt. No tiene modelos ni APIs dentro: viven en la ficha (`mvp/modelos.json`).
- **Edificio 2 — Harness y plugins** (`plugins/`): ejecuta el trabajo (bucle de herramientas, chat, memoria, motores).
- Entre edificios solo HTTP o MCP (`POST /plugins/<id>/call/<accion>`, `POST /mcp`). Ningún import cruzado.

## Reglas
1. Un banco y una llave de acceso; los secretos no salen del servidor ni van a GitHub.
2. Los permisos los decide el servidor (`mvp/control.py`); el navegador solo los muestra.
3. Cambios quirúrgicos; el código nuevo del MVP va en `mvp/`; archivos ≤100 líneas y funciones ≤25 en código nuevo.
4. PASS solo con salida cruda de una ejecución real; si no, NO VERIFICADO.
5. Prohibido: GitHub Actions, HF Jobs, SSH, LFS, memoria en GitHub, editar o recortar el system prompt.

## Mapa
Mapas por carpeta: `raiz_router/ARQUITECTURA.md`, `raiz_fichas_prompt/ARQUITECTURA.md`, `plugins/deepseek_harness/README.md`, `docs/MEMORIA.md`, `docs/CHAT_CONTROLES.md`. Pruebas de integración para Sol: `docs/PRUEBAS_SOL.dag.json`.
