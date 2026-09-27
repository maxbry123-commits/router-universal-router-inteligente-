# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 02:40 UTC por Opus. Director: Max.

## Orden de lectura
1. `../02-ARQUITECTURA/📂readme chat Arquitectura.md` (cómo es el sistema)
2. `../01-PLAN/PLAN-MAESTRO-CHAT.yaml` (nodos A1…E1, qué falta y cómo se cierra cada uno)
3. `../00-INSTRUCCIONES/` (todas las instrucciones del Director, verbatim, partes 1–5)
4. Este archivo + `STATE.json` + `CRAZY_WALL.json` + `BITACORA.jsonl`

## Dónde estamos
- **Nodo activo:** A1 — OmniRoute privado dentro del Router 16 GB. Prueba lanzada 27-sep 00:51 (`.github/workflows/prueba-omniroute-router.yml`). Revisar su resultado.
- **Hecho:** Router en Job 16 GB de pago; OmniRoute arranca dentro (`router inteligente universal/keeper/start_omniroute.sh`) y el Router lo expone en `/omniroute/*`; conector MCP sin OAuth; forks de OpenClaw y Hermes; raíz del chat ordenada; limpieza de piezas sueltas.
- **Siguiente:** A1 (confirmar) → B1 State Hub → A3 OmniRoute como proveedor del Router → A2 aviso Kimi K3/DeepSeek V4 en el chat → B2 memoria cableada con componentes ya descargados.

## GAPs abiertos
- G1: `ui_bridge.py` guarda grupos/workflows/órdenes en `chat router/data/`; esa carpeta se movió a `03-ESTADO/data/` → ajustar la constante `DATA` en `ui_bridge.py` (nodo B1).
- G2: enlace del chat que desplegó Manus (el Director lo tiene) → nodo D1.
- G3: Groq sin clave en secretos del Router.
- G4: Parte 2 del verbatim (documentos del 25-sep) incompleta; está en la conversación de Opus.

## Reglas para quien continúe
Anotar cada instrucción nueva verbatim en `00-INSTRUCCIONES/` ANTES de ejecutar; 1 chat = 1 nodo en CRAZY_WALL; evento en BITACORA por cada cambio; no crear archivos fuera de esta raíz; no cambiar diseño/herramientas del Director sin autorización; todo modelo por nuestro Router.

## STATE (foto actual)
```json
{"schema":"yaiwes.state/v1","proyecto":"chat-yaiwes","actualizado":"2026-09-27T02:40Z",
 "fase":"A","nodo_activo":"A1","hechos":["router_16gb","omniroute_dentro_arrancando","mcp_sin_oauth","forks_openclaw_hermes","raiz_ordenada"],
 "siguientes":["A1","B1","A3","A2","B2"],"gaps":["G1","G2","G3","G4"]}
```

## CRAZY WALL (1 chat = 1 nodo)
```json
{"schema":"yaiwes.crazy-wall/v1","nodos":{"A1":{"status":"CLAIMED","agente":"opus","chat":"opus-2026-09-27","fase":"PRUEBA","siguiente":"revisar prueba-omniroute-router"}}}
```
