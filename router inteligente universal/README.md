# Router Inteligente Universal — README y arquitectura

Actualizado: 2026-10-03 noche (Opus, orden del Director Hy). **Si algo se contradice, vale `MANUAL-AGENTES.md`.** Las guías viejas de esta carpeta (`CONECTAR-*`, `HANDOFF-CABLEADO`, `HANDOFF-PROVISIONAL-ROUTER`) y las adendas de `Readme arquitectura…` están superadas.

## Empieza aquí (orden de lectura)

| # | Archivo | Para qué |
|---|---|---|
| 1 | `MANUAL-AGENTES.md` | Manual completo: cómo conectarse con un token, permisos, rutas, errores |
| 2 | `HANDOFF-ROUTER-UNIVERSAL-OPUS.md` | Estado verificado de hoy y pendientes |
| 3 | `HANDOFF-FICHA.md` | Paso a paso para crear, probar y publicar una ficha (sección nueva) |
| 4 | `Banco de claves/HANDOFF-BANCO.md` | Banco de secretos: dónde vive, qué tiene, cómo se agregan claves |
| 5 | `fichas/_plantilla.json` | Plantilla vacía de ficha |

## Reglas que no se rompen

1. Nadie toca el código del Router para conectarse: todo entra por la puerta con un token `riu_...`.
2. Nunca se escriben claves ni tokens en archivos, commits, chats ni memoria. Viven en el banco. Si necesitas un token, sale del banco.
3. Todo cambio del sistema (banco, tokens, fichas publicadas, procesador, borrar) exige la **clave del Director**. Sin ella el Router responde `403 CLAVE_DIRECTOR_REQUERIDA`: para y avisa.
4. Sin GitHub Actions. El cómputo corre en Hugging Face (pagado).

## La arquitectura en palabras simples

```
Agente / instancia (con su token riu_...)
        │  HTTP (tipo OpenAI)  o  MCP
        ▼
Puerta fija (Space HF pagado, siempre la misma dirección)  ── /mini/... ──▶ Router de respaldo T4/L4
        │  candado: clave del Director + permisos + límite por token
        ▼
Router 24/7 (Job HF 16 GB) ──▶ banco de secretos ──▶ APIs (NVIDIA, Groq, OpenAI, HF...)
        │                   ──▶ memoria · espacio propio · fichas (secciones) · laboratorio
        ▼
Almacenamiento HF permanente (raíz del Router: router-inteligente-universal/; el respaldo usa router-respaldo/)
```

- **Puerta:** `https://comand-center-1-claude-github-mcp-backup.hf.space`. Nunca cambia. Su micro-kernel enciende un Router nuevo antes de que venza el actual y cambia sin corte.
- **Router:** Job de Hugging Face 24/7 (CPU, 16 GB). Arranca con el código empaquetado en el almacenamiento HF (`codigo/router-bundle.tar.gz`), no necesita GitHub.
- **Relevos automáticos:** si el Router pasa del 85 % de CPU o RAM, enciende procesadores de relevo (16 GB por CPU, 32 GB por RAM) y los apaga tras 5 min sin uso.
- **Conexión universal:** un token por agente sirve para chat tipo OpenAI, MCP, memoria, archivos propios, fichas, cómputo y terminal. Hasta 10.000 tokens, cada uno con su límite y su espacio.
- **Fichas = secciones vivas:** cada ficha nueva en el almacenamiento aparece sola como sección nueva, sin reiniciar.
- **Banco:** único, cifrado con la clave maestra del Director; el Router lo relee cada 5 min (las claves nuevas entran solas).
- **Ventana status:** el Router escribe solo su estado (conectados, banco sin claves, laboratorio, secciones, tokens) en `router-inteligente-universal/Ventana status router inteligente universal/`.

## Código del Router

| Carpeta | Qué es |
|---|---|
| `integration/chat_mvp/` | App del Router: `app.py`, `candado.py` (clave del Director y permisos), `tokens.py`, `secciones.py` (fichas), `ventana.py`, `rutas.py`, `control_plane.py` (banco vivo, laboratorio, fichas), `mcp_api.py`, `openai_route.py` |
| `integration/hf_*.py`, `integration/huggingface/` | Puente HF, cómputo y autoscale |
| `security/`, `red/`, `enchufe/`, `domain/` | Seguridad, red universal, enchufe Fables y su esquema |
| `Banco de claves/` | Banco cifrado (`secret_bank/`) |
| `plugins/` | Plugins del Router (cada uno con su `ficha.json`) |
| `sdk/` | Clientes de un archivo para conectarse con el token (Python y Node) |
| `tests/` | Pruebas (`test_conexion_universal.py` = candado, tokens, fichas) |

Las demás carpetas de esta raíz (componentes descargados: openclaw, hermes, rowboat, deepseek-harness-router, `Componente open soure…`, `Componentes del Router`, agentes) **no son parte del Router en ejecución**. Su orden final está pendiente de decisión del Director.

## Fuera de esta carpeta

- `chat router/`: el chat YAIWES y sus agentes (Hermes, OpenClaw, harness DeepSeek, memoria). Se conecta al Router como cualquier instancia. Su estado: `chat router/03-ESTADO/`.
- Space HF `COMAND-CENTER-1/claude-github-mcp-backup`: `door.py` (puerta + kernel), `mini.py` (router de respaldo). También es el conector MCP de GitHub del Director: no se reconstruye sin su orden.
