# memory-agente-minimax-01.md

> Estado, handoff y bitacora del agente MCode (MiniMax M3.1 Flash) sobre el repositorio canonico
> `maxbry123-commits/router-universal-router-inteligente-`. **Fuente de verdad del bucle.**
> Actualizado: 2026-11-03. Las claves solo se referencian como variables cifradas, nunca en claro.

## 1. Identidad y credenciales
- GitHub: `maxbry123-commits` (cuenta real). `abc1tienda-web` es espejo: no usar.
- Hugging Face: `COMAND-CENTER-1`.
- Credenciales (almacen cifrado de secretos): `${UNIVERSAL_KEY}`, `${HF_TOKEN_1_NEW}`,
  `${HF_MCP_CLAUDE_PERMANENT}`, `${GITHUB_TOKEN}` (PAT de escritura aun NO provisto).
- Router RIU: `https://comand-center-1-riu-router.hf.space`, clave `${UNIVERSAL_KEY}` en
  `X-API-Key` y `Authorization: Bearer`. 14 tools MCP. Commit vivo `d82217f15e`.
  Herramientas clave: `github_leer`, `github_escribir`, `github_api`, `archivos`, `memoria`.

## 2. Metodo de trabajo (skill)
Skill `mcode-metodo-de-trabajo` (en `.skills/`): ciclo Loops de 11 pasos, 20 fuentes obligatorias antes de
cada objetivo, 10 alternativas ante gaps, puertas FAIL_CLOSED, formato de salida unico.
Referencias: `conexion-riu.md`, `paneles-iframe.md`, `investigacion-comunidad.md` (20+ fuentes).

## 3. Reglas permanentes
- Sin GitHub Actions. Sin Vercel ni HF sin autorizacion explicita en el chat actual.
- Motores canonicos intocables, copy-only, blob SHA fijados. Prohibido adquirir componentes con
  git clone/fetch, curl/wget, pip/npm. Gap = `MOTOR_ONLY_COMPONENT_GAP`. Modificar un motor =
  `MOTOR_CODE_LOCK_GAP`. PASS solo con read-back + hashes.
- Frontend: edicion quirurgica, nunca reconstruir, 3 revisiones visuales.
- No guardar estado en sandbox ni memoria del agente: el estado vive en este archivo.

## 4. Cableado canonico verificado
- Motores: `➡️📂motores de descarga extraccion copiado movimiento archivos router-universal-router-inteligente-/`
  + skill `➡️📂 skills descargar extraer zip copiar mover archivos readme.md`.
- Motor de busqueda (implementa la regla de 20 fuentes, sin LLM): `➡️📂 motor de busqueda/`
  (`websearch_engine.py`, `research_prepass.py`, `source_registry.json`).
- Fichas de cableado: `chat-router/cableado.manifest.json`, `chat-router/MAPA.md`,
  `chat-router/CIERRE_XRAY_LOOP_CODA.md`.
- Frontend del chat: `chat-router/chat/frontend/` (`shell.html`, `shell.js`, `api/loop.js`,
  `api/power.js`, `api/ecc_motor.py`, `loop-panel.*`, `ventana-*.js`, `chat-ventanas.js`).
- Contrato declarativo del LOOP: `chat-router/chat/frontend/LOOP-wachdog-cola.json`.
- Memoria de agentes (Sistema 1): `chat-router/memoria/` -> este archivo.

## 5. Auditoria forense X-RAY (2026-11-03) - hallazgos
1. El plan de paneles iframe **ya esta parcialmente ejecutado**: existen `loop-panel.html` (13 KB) y
   `loop-panel.js` (17.7 KB) con CSS/JS propios (`yaiwes-panel.css`, `loop-proyecto.css`,
   `loop-colas.css`, `loop-triggers.css`, `loop-ejecucion.css`, `yaiwes-panel-bridge.js`, ...) y banner
   de modo seguro ("abrir el HTML local no enciende el motor Python"). El boton `#btn-loop` ya existe.
2. **GAP G1**: no existen `watchdog-panel.html` ni `cola-panel.html`. Watchdog y Cola siguen en ventanas
   legacy (`ventana-watchdog.js` 9.1 KB, `ventana-cola.js` 10 KB). Migracion pendiente =缺口 real.
3. `chat-router/chat/frontend/api/loop.js`: estado **en memoria de proceso** (`new Map()`), tope de 8
   pasos, motor `ecc_motor.py` via `spawnSync` con timeout 2 s. **No es motor persistente**: ninguna vista
   puede prometer ejecucion de horas.
4. **GAP G2** (`cableado.manifest.json`): `connectivity`, `hf_compute`, `hf_storage` y `lifeguard` tienen
   `"destino": ""` y `"enlace": false` -> plugins sin cablear.
5. `LOOP-wachdog-cola.json` es el **contrato declarativo** (raiz, plugin, harness
   `/plugins/loop_wachdog/call/paso`, botones, watchdog `intervalo_ms` 3000, `tope` 8, `pausa_si`).
   Los paneles nuevos deben derivarse de aqui, no hardcodear valores.
6. `CIERRE_XRAY_LOOP_CODA.md`: 8 segmentos; 2-8 pendientes de pruebas reales (codigo corregido != PASS de
   ejecucion). Vigente: no crear otra raiz, no GitHub Actions, no LFS, no desplegar fuera del repo
   autorizado, no declarar DONE con bloqueos.
7. `MAPA.md`: Fase 1 hecha; la Fase 6 (backend) **requiere autorizacion expresa**.

## 6. Estado del bucle
| Fase | Estado |
|---|---|
| Auditoria forense X-Ray + verificacion cruzada | HECHO |
| 20+ fuentes de comunidad | HECHO |
| Gaps detectados (G1, G2) | HECHO |
| Skill de metodo + referencias | HECHO |
| Implementacion watchdog/cola panel | PENDIENTE |
| 3 revisiones visuales frontend | PENDIENTE |
| Job HF 32 RAM CPU | PENDIENTE (solo si es necesario) |
| Cierre G2 (plugins sin cablear) | PENDIENTE |

## 7. Pendiente (siguiente iteracion, en este orden)
1. Leer `yaiwes-panel-bridge.js` y `loop-panel.js` y derivar el contrato real del bridge (origen, nonce,
   envelope). No escribir paneles sin verificar el contrato: seria sobre-ingenieria a ciegas.
2. Crear `watchdog-panel.html` y `cola-panel.html` siguiendo el patron de `loop-panel.html` y el
   contrato `LOOP-wachdog-cola.json` (data-driven, sin estado propio del LOOP).
3. Cableado: anadir entradas en `cableado.manifest.json` y el boton/ventana en `chat-ventanas.js`,
   sin tocar `shell.js`/`shell.html` salvo lo minimo indispensable.
4. 3 revisiones visuales con render headless (Chromium) + captura: consola sin errores, sin 404,
   foco/scroll/responsive correctos, y el chat sigue enviando mensajes.
5. Un commit por panel (loop -> watchdog -> cola) para rollback granular.
6. Cerrar G2 leyendo `MAPA.md` de la fase correspondiente antes de mover nada.

## 8. Bitacora
- 2026-11-03 - Auditoria X-RAY + 20+ fuentes + skill `mcode-metodo-de-trabajo` + este archivo en `main`.
  Gaps G1 y G2 documentados. Sin cambios de codigo en este ciclo.
