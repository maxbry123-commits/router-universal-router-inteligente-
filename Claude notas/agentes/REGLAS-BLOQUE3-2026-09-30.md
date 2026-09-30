# REGLAS DE LOS AGENTES — BLOQUE 3 (2026-09-30 ~02:10 Bogotá)
Las escribe Claude (coordinador). Cada agente las lee PRIMERO y cumple TODAS. Órdenes del Director: `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-5.md` y las de hoy 01:48 y 01:58 (resumen fiel abajo; el literal lo anota Claude aparte).

## Orden del Director de hoy (01:48 y 01:58)
- El núcleo del Router queda lo MÍNIMO; todo lo demás se conecta por separado como plugins, como piezas de lego. Nada de código monolítico.
- Cadena: Kimi K3 → GLM 5.3 → DeepSeek V4, hasta 1,5 min por modelo; el chat es un plugin conectado.
- Enchufe de Fables + plugin del harness de DeepSeek + sistema paralelo dentro del Router; revisar conectividad MCP / HTTP / FastAPI.
- Puentes como plugins: almacenamiento (permanente de Hugging Face), dataset del repo, datasets de HF y biblioteca de skills de HF (estos dos se conectan POR LLAMADA: no viven en el Router), cómputo.
- Una tarea por agente; sin sobre-ingeniería; cuidar el cómputo.

## Conector y repo
- Solo el conector MCP_SECRET_HF (GitHub + Hugging Face). Cárgalo con ToolSearch: `select:mcp__MCP_SECRET_HF__github_api,mcp__MCP_SECRET_HF__get_file,mcp__MCP_SECRET_HF__create_or_update_file,mcp__MCP_SECRET_HF__create_branch,mcp__MCP_SECRET_HF__storage_list,mcp__MCP_SECRET_HF__storage_read,mcp__MCP_SECRET_HF__storage_write`. Si no aparece, PARA y dilo en una línea. Nada de curl, WebFetch ni otros conectores.
- Repo: `maxbry123-commits/router-universal-router-inteligente-` (PÚBLICO: jamás valores de claves, solo nombres de secretos).
- Tu rama: `bloque3-<tu nombre>`, creada desde main con create_branch. No escribas en main salvo que tu tarea lo diga. Commits con `[skip ci]` salvo cuando necesites CI.
- Las respuestas de github_api pueden ser enormes (límite de 25 000 tokens): usa rutas estrechas (contents de una carpeta, commits con `path=` y `per_page` ≤ 5) y get_file para leer un archivo. No listes commits enteros.

## Prohibido
- delete_repository, delete_branch, delete_file y cualquier DELETE por github_api.
- Tocar el Space `claude-github-mcp-backup`, Vercel, o relanzar/cancelar el Job del Router (eso lo hace solo Claude con orden del Director).
- Borrar componentes (solo reubicar), crear otro router, usar APIs de Anthropic, usar Cerebras u OmniRoute, escribir código desde cero si ya existe algo (se poda y se cablea lo descargado).
- Ejecutar código de terceros descargado.

## Cómo trabajar
- No inventes. Todo dato que afirmes lo leíste; lo que no verificaste se escribe SIN VERIFICAR. Nada se marca ✅. Solo 🟡 hecho sin probar, 🔴 pendiente, ⛔ bloqueado.
- Sin sobre-ingeniería: lo mínimo que cumple la tarea.
- Cuida el cómputo: lee solo lo necesario, no repitas lecturas, no esperes ni consultes en bucle: ejecutas, lees el resultado UNA vez y paras. Máximo ~40 llamadas a herramientas. Si un paso falla 2 veces, PARA y repórtalo.
- No hay Python con el repo en local: las pruebas se corren en CI de GitHub con un workflow temporal `tmp-<tu nombre>-verify.yml` (workflow_dispatch; copia el patrón de `tmp-bloque2-verify.yml`). Dile a Claude si lo creaste (lo borra él al final).
- Plugins nuevos: carpeta `router inteligente universal/plugins/<id>/` con `ficha.json` (schema `plugin_host/v1`) y `plugin.py` con `handle(action, payload)`; plantilla: `plugins/chat/` y `plugins/README-ROJO.md`. `enabled_default: false`. El id usa guion bajo, no guion.

## Entrega
1. Escribe tu handoff en `Claude notas/agentes/<tu nombre>.md` (en tu rama): qué hiciste, archivos con su blob sha, qué quedó 🔴, qué NO pudiste verificar.
2. Responde en ≤ 10 líneas, español simple, sin código: qué hiciste, rama y commits, qué queda pendiente, qué no verificaste.
