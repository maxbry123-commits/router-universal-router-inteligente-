# CIERRE X-RAY — LOOP CODA (8 segmentos)

Ámbito único: `maxbry123-commits/router-universal-router-inteligente-`.
Raíces autorizadas: `router-mvp/` (Router MVP + fichas) y `chat-router/` (Harness DeepSeek, YAIWES, SWE CODE, SWEN, OpenClaw UI).
No crear otra raíz, otro router, GitHub Actions, LFS ni desplegar fuera del repositorio autorizado.

## Estado de verificación
- Base tomada antes de corregir: `fb3437207d5014b0d2ca6101310fe2badbca95f4`.
- Correcciones realizadas:
  1. `e28ac9826b2e802d42f5fe88a6bcc6297f0d0a29`: identidad del proveedor real en YAIWES; reenvío de métricas Router → Harness → `/chat/send`; métricas al reanudar tareas. Prueba añadida: `chat/backend/mvp/test_xray1_trazabilidad.py`.
  2. `0e19e3cddce1c81c88afc014d0506560ecb4ae94`: cancelar HTTP no-stream del bridge con AbortSignal; no rotar claves ni saltar servidor después de Detener.
  3. `d88a8e5735ebbddb6eb23db8949b7540cd6efa20`: detener también el descubrimiento `GET /models`, cerrar failover al cancelar; pruebas nuevas `SWE CODE/web-bridge/test/xray2_cancelacion.test.mjs`.
- Todos los cambios anteriores están dentro de `chat-router/`. Sin cambios al repositorio independiente OpenClaw.
- Auditoría estática: realizada. Pruebas de integración locales y proveedores reales: **NO EJECUTADAS / NO CERTIFICADAS**. Despliegue HF, proxy, Gateway OpenClaw: **NO CERTIFICADOS**.

## Segmentos de cierre

| Segmento | Alcance | Estado | Criterio para PASS real |
|---|---|---|---|
| 1 | Reconstruir diff e instrucciones y descartar GAPS obsoletos | EN PROGRESO | diff por SHA y archivos trazados |
| 2 | Banco, autenticación, secretos y roles | CÓDIGO CORREGIDO PARCIAL; PRUEBAS AÚN SIN EJECUTAR | no secretos en logs/LS; 401/403; operador individual |
| 3 | Fichas y Router MVP, Groq/NVIDIA, SSE, contexto, latencia | CÓDIGO CORREGIDO PARCIAL | pruebas unitarias y llamada real por id |
| 4 | Harness, permisos Tools ON/OFF, tools, MCP, checkpoint | CÓDIGO CORREGIDO PARCIAL | llamada de herramienta y reanudación con recibo |
| 5 | Router SWE, SSE, cancelación, fallback y métricas | CÓDIGO CORREGIDO PARCIAL | pruebas de cancelación y SSE reales |
| 6 | Frontend YAIWES, modelos vs ejecutores y progreso | PENDIENTE DE E2E | browser: selector, controles, respuesta parcial |
| 7 | Plugin de OpenClaw UI y contrato bidireccional | PENDIENTE DE E2E REAL | Control UI del Gateway ejecutando plugin instalado |
| 8 | Pruebas cruzadas, versión desplegada HF/Vercel y cierre | BLOQUEADO HASTA PRUEBAS | SHA desplegado, contratos API, PASS/GAP/BLOQUEO |

## Pruebas solicitadas (no ejecutadas aquí)
Desde la raíz, con dependencias y PYTHONPATH existentes:
```bash
PYTHONPATH="router-mvp:chat-router" python3 -m unittest mvp.test_xray1_trazabilidad
PYTHONPATH="router-mvp:chat-router" python3 -m unittest mvp.test_externos_nuevos mvp.test_externos_a5
node --test "chat-router/SWE CODE/web-bridge/test/xray2_cancelacion.test.mjs"
node --test "chat-router/SWE CODE/web-bridge/test/respaldo_stream.test.mjs"
```
No activar GitHub Actions ni cambiar el despliegue para ejecutar estas pruebas.

## Reglas de cierre
- PASS de código = fuente y rutas inspeccionadas; PASS de ejecución requiere prueba real.
- Los ids de Groq/NVIDIA no se consideran DISPONIBLES hasta consultarlos con las credenciales y permisos reales.
- Ante un fallo después de emitir texto, preservar parcial/checkpoint y nunca duplicar una operación con efectos.
- El usuario no autorizó modificar `maxbry123-commits/openclaw` ni `~/.openclaw/openclaw.json`.
- Mantener este archivo como bitácora de segmentos; no declarar DONE total mientras queden bloqueos.

## Segmento 2 — persistencia de secretos (parche)
- `SWE CODE/web-bridge/src/server.js`: POST/DELETE de claves confirma solo después de escritura cifrada; una inyección autorizada por petición tampoco activa claves cuando falla el banco. Retorna 503 `BANCO_NO_GUARDADO`/`BANCO_NO_BORRADO` sin secretos.
- `chat/frontend/swe-claves.js`: exige `local:true` para confirmar escritura; distingue banco local de respaldo externo `persistido:true`, evitando prometer persistencia tras reinicios del Space.
- Pruebas ampliadas: `SWE CODE/web-bridge/test/seguridad.test.mjs` y `chat/frontend/test/swe-claves.test.mjs`. Aún no ejecutadas en entorno Node real.
- Pendiente: verificar servidor real, caja de claves HF persistente, publicación cifrada en rama exclusiva y permisos del operador. No hay nuevo router ni terceros.

## Segmento 3 — Router MVP, fichas y aceleradores (parche X-Ray)
- Fichas existentes: `router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json` verificada en lectura; sin mover la ficha ni cambiar las políticas Qwen.
- `chat/backend/mvp/compute.py`: conservar los IDs reales de tool_calls; si NVIDIA/Groq omiten uno, generar un identificador único para que el Harness pueda contestar el resultado. Argumentos vacíos normalizados a `{}`.
- `chat/backend/mvp/externos.py`: no declarar éxito si el stream terminó sin texto ni herramientas; el catálogo `GET /models` de una clave no bloquea automáticamente un modelo permitido para otras claves con permisos distintos. Nunca se cambia el modelo solicitado.
- Prueba nueva: `chat/backend/mvp/test_xray3_aceleradores.py` (sin credenciales reales; simulación).
- Verificado estáticamente: contratos de `politicas_modelo.json`, `compute.py`, `externos.py`, `app.py` y pruebas anteriores. Pendiente: ejecución de las pruebas y test real de proveedor/Space.
