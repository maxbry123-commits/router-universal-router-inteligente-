# Investigación forense: fallos de ejecución real de herramientas en Qwen, DeepSeek y GLM

**Fecha de corte:** 19 de octubre de 2026  
**Objeto:** incidencias `ACK_SIN_EJECUTAR`, `HERRAMIENTA_NO_EJECUTADA`, `TIMEOUT_NODO` y truncamiento de lecturas GitHub en un orquestador multinodo.  
**Tipo de documento:** investigación de fuentes públicas, diagnóstico diferencial y guía de implementación.  
**Importante:** no se ha inspeccionado el código fuente ni los registros completos del ejecutor de este proyecto. Las causas específicas de cada nodo son hipótesis hasta comparar solicitudes y respuestas HTTP originales. Los PASS/FAIL descritos a continuación son resultados reportados por el operador, no pruebas reproducidas aquí.

---

## 1. Veredicto ejecutivo

**No hay una única avería.** Los síntomas encajan en **cuatro capas de fallo independientes**:

1. **Decisión del modelo / prompt:** el modelo entiende la tarea, pero responde con un acuse («Entendido», «Estoy listo») en lugar de emitir una llamada estructurada. Que entienda una instrucción *no implica* que solicite una herramienta.
2. **Serialización del protocolo:** los modelos o los adaptadores pueden producir texto que parece una llamada pero no aparece en `tool_calls`; perder llamadas en streaming; omitir `reasoning_content`; volver a enviar `tool_calls` sin sus resultados; o usar una plantilla/parser incompatible. Existen reportes públicos reproducibles para Qwen, DeepSeek y GLM.
3. **Ejecutor y puerta de evidencia:** aun si el modelo devuelve `tool_calls`, la ejecución física depende del cliente. **`finish_reason="tool_calls"` no es una prueba de herramienta ejecutada**. La prueba exige una invocación del handler, su resultado y un recibo verificable.
4. **Presupuesto temporal y volumen documental:** un segundo intento consume más tiempo; si el plazo total es 150 s, el fallback puede vencer incluso si corrige el ACK. Un archivo de 1,1 MB supera el umbral de representación JSON normal del endpoint GitHub Contents, y además puede exceder límites internos del lector o del contexto del modelo.

**Prioridad recomendada:** instrumentar el camino `request → respuesta original → tool_calls → dispatcher → resultado → recibo`; corregir compatibilidad por proveedor; introducir fallback determinista **solo en los nodos que no ejecutaron nada**, con `deadline` global y tiempos por intento; mantener inalterados los nodos con PASS.

### Evidencia pública que cambia el diagnóstico

- **Alibaba Cloud (documentación oficial):** para Qwen, `tool_choice="required"` no garantiza llamadas en no-thinking y no está soportado en thinking. En cambio, seleccionar una función por nombre sí figura como opción. **No basta con cambiar `auto` a `required` para arreglar Qwen.** [S1][S2]
- **Qwen:** existe un issue con `tool_calls` vacío aun usando Hermes y otro en el que el modelo planea la llamada en el razonamiento pero no la emite. [S3][S4]
- **Qwen3.8:** hay fallos reportados de tool calling con prompts largos y `enable_thinking=false`, errores de plantilla al reinyectar argumentos JSON como texto y problemas con mensajes `system` intercalados. [S5][S6][S7]
- **DeepSeek oficial:** `tool_choice=required`/función nombrada no está admitido en determinadas combinaciones de *thinking mode* en Chat Completions; al reutilizar historial con herramientas hay que preservar `reasoning_content`. [S8][S9]
- **DeepSeek comunidad:** se ha reportado que `deepseek-v4-pro` emite invocaciones como texto en `content` sin `tool_calls`. [S10]
- **GLM:** también hay fallos de parseo; el PASS actual no prueba inmunidad global, pero indica que el camino empleado ahora por `glm52` sí funciona para ese lote. [S11][S12]
- **GitHub oficial:** el endpoint Contents admite archivos de 1–100 MB con tipos `raw` u `object`, pero en modo `object` el campo `content` queda vacío. [S13]

---

## 2. Hechos aportados y lo que significan

| Nodo | Observación reportada | Clasificación correcta | Próxima comprobación |
|---|---|---|---|
| `glm52` | PASS, `allowed_actions` con 8 acciones y líneas reales | Éxito **reportado**; aún conviene exigir recibos de despacho | Confirmar `tool_call_id`, handler ejecutado y SHA/fuente de evidencia |
| `qwen38max/motores` | Diagnóstico real de 2 fichas | Trabajo sustantivo; no equivale automáticamente a modificación de GitHub | Verificar alcance exigido por su DAG |
| `qwen36` | Investigación real parcial | `PARTIAL`, no `PASS` final | Continuación desde checkpoint/evidencia |
| `qwen38flash-auditor` | Usó GitHub API real; archivo de 1,1 MB truncado | Ejecución real + **lectura incompleta** | Registrar tamaño, SHA, bytes recibidos, representación `raw` y límite posterior |
| `dsv4flash` | Responde «Entendido. Estoy listo...»; fallback acaba en 150 s | `ACK_NO_TOOL` y luego `TIMEOUT_NODO` | Capturar respuesta cruda, modalidad de thinking y tiempo por intento |
| `dsv4pro` | Responde «Listo. Estoy a la espera...» | `ACK_NO_TOOL` | Validar `tools`, `tool_choice`, content, reasoning y formato API |
| `room-qwen38` | `HERRAMIENTA_NO_EJECUTADA` | Fallo **ambiguo**: puede ser generación, parser o dispatcher | Separar `NO_TOOL_EMITTED`, `TOOL_PARSE_LOST`, `TOOL_DISPATCH_FAILED` |

**No concluir**: «DeepSeek Flash no sirve», «Qwen no sabe ejecutar», «GitHub corta exactamente a 1 MB», «el fallback ya resolvió todo», ni «GLM pasa siempre».

### Por qué el layout B funcionó de forma parcial

El layout B cambió la forma en que la tarea llega al modelo. Esto puede aumentar la probabilidad de que el modelo interprete «ejecutar ahora» y no «esperar la siguiente orden». Pero cada combinación de **modelo + versión + endpoint + thinking + plantilla + parser** tiene un contrato distinto. Un prompt mejor **no arregla** un campo `tools` ausente, un parser que pierde `<tool_call>`, una sesión MCP cerrada ni una llamada HTTP sin permisos.

El layout D (solo tarea, menos contexto) es plausible como fallback por **reducir ambigüedad y tokens**, pero su eficacia debe medirse por nodo. No hay evidencia suficiente para asegurar que todo ACK de DeepSeek se resolverá con D. Un fallback **no puede recrear una llamada que ya generó un efecto lateral**, salvo que el ejecutor sea idempotente.

---

## 3. Diez pasadas de investigación en documentación china, proveedores e issues

Estas son **diez líneas de búsqueda y contraste distintas**, no diez ejecuciones de tests sobre tu Router.

| Pasada | Área / idioma y tipo | Hallazgo contrastable | Consecuencia |
|---:|---|---|---|
| 01 | Qwen/Alibaba, documentación oficial china e inglesa | `tool_choice` y semántica de Function Calling: la aplicación debe ejecutar; Qwen no garantiza `required` [S1][S2] | El modelo no es el ejecutor; usar selector de función soportado y evidencia externa |
| 02 | Qwen en vLLM, issues técnicos | Se han perdido llamadas por interacción parser de reasoning/streaming; también hay falsos tool calls [S14][S15][S16] | Comparar stream y non-stream; auditar parser, no solo prompt |
| 03 | GLM/Z.ai y vLLM | GLM-5.2 tiene reportes `stop` sin tool_calls y parseo de XML; no es infalible [S11][S12] | Preservar GLM PASS, mantener pruebas de regresión |
| 04 | Comunidad china Qwen-Agent/MCP | Fallos por argumentos JSON incompletos, dependencias o herramientas no registradas [S17][S18][S19] | Separar error del modelo, del registro y del canal MCP |
| 05 | Qwen3.8 y Qwen-Agent (2026) | Long prompts/no-thinking, historial JSON-string, streaming intercalado [S5][S6][S20] | Normalizar argumentos e identificar delta por índice |
| 06 | Comunidad DeepSeek / DeepSeek Harness | `content` sin `tool_calls`, respuestas solo de razonamiento y estados incompletos [S10][S21][S22] | No marcar `completed` si falta acción exigida |
| 07 | DeepSeek oficial + Alibaba | `reasoning_content` es parte del contrato en thinking; matrices de tool_choice distintas por endpoint [S8][S9] | Adaptador específico; nunca aplicar un campo a ciegas |
| 08 | GLM-5.2 + Alibaba | `tool_stream` tiene comportamiento dependiente de ruta y `stream`; vLLM reporta fallos con `required` [S23][S24] | Medir gateway efectivo, no copiar parámetros entre plataformas |
| 09 | Qwen3.8: contexto/latencia | Reportes de plantilla rechazando `system` intercalado y largas latencias de agentes en Token Plan [S7][S25] | Reducir re-prefill, historial, contextos enormes; no prometer 150 s para todos |
| 10 | GitHub REST + Python asyncio | Límite de representación Contents y semántica de cancelación/timeout [S13][S26] | Descargar raw, validar bytes y usar deadlines reales |

**Calidad de evidencia:** documentación oficial = contrato esperado; issues con reproducciones = indicios fuertes pero dependientes de versión/stack; observaciones de tu batch = hechos operativos sin traza adjunta. Los reportes públicos no demuestran que el mismo bug esté presente en tu despliegue.

---

## 4. Diagnóstico diferencial: matriz de causas posibles

| Causa | Síntoma típico | Confianza de pertinencia | Cómo confirmar/refutar |
|---|---|---|---|
| A. Prompt termina en «espera confirmación» o tiene muchas instrucciones de preparación | ACK corto, `stop`, sin `tool_calls` | **Alta** para ACK, no demostrada | Comparar B con D_solo_tarea con mismos `tools` y 20 pruebas |
| B. `tools` no adjunto realmente al request | Texto «puedo hacerlo», sin llamadas | **Alta** como causa técnica posible | Log del JSON **enviado** al proveedor; cantidad y nombres de herramientas |
| C. `tool_choice="auto"` permite no llamar | ACK o texto final | **Alta** como comportamiento permitido | Experimentar función nombrada en modelos/rutas que la soporten |
| D. `required` incompatibilidad Qwen/DeepSeek-thinking | `400`, `stop`, sin calls o restricciones inoperantes | **Alta** por documentación | Registrar parámetros y respuesta; probar fuera de thinking según soporte |
| E. Razonamiento largo / separación de canales | «planearé usar herramienta», sin invocación | **Media-alta** por issues | Log `reasoning_content`, `content`, `tool_calls`, límites de salida |
| F. Parser/chat template incompatible o desactualizado | Sintaxis de llamada en `content`, `tool_calls=null`, JSON truncado | **Alta** como clase de bug | Comparar contenido bruto vs API normalizada; versión/parser/hash template |
| G. Streaming SSE reconstruido mal | `tool_calls` incompletos, id/index mezclados | **Media-alta** en stream | Mismo test con `stream=false`; inspeccionar secuencia SSE |
| H. Historial de llamadas reinyectado incorrectamente | Primera llamada OK, turno posterior 400 o pérdida de continuidad | **Media** | Validar alternancia assistant tool_calls → tool results y razonamiento |
| I. Herramienta ausente/no autorizada | `HERRAMIENTA_NO_EJECUTADA`, incluso con call | **Media-alta** si existe tool call | Revisar `allowed_actions`, nombre exacto, ruta dispatcher, permisos |
| J. Handler falla sin dejar recibo | CALL generado, pero sin ejecución acreditada | **Media** | Log inicio/fin del handler, HTTP a GitHub, response code, request ID |
| K. Archivo de 1,1 MB enviado como JSON Contents normal | `content` vacío/`encoding=none` o lector lo limita | **Alta**, documentación GitHub | Medir `size`, `Content-Length`, bytes crudos y tipo `Accept` |
| L. Truncamiento por contexto/SDK/gateway | Archivo leído parcialmente a pesar de raw OK | **Media-alta** | Comparar descarga local completa, límite de caracteres y tokens del executor |
| M. Timeout global 150 s con 2 intentos | Segundo intento cortado | **Confirmada conceptualmente** por reporte | Trazas `queue_wait`, primer intento, reintento, llamada herramienta |
| N. Saturación de cola/rate limits | Latencia elevada, 429/503, retries internos | **Media** | Métricas p50/p95 por proveedor, cabeceras retry-after y concurrencia |
| O. Permisos/GitHub API rate limit | 401/403/404/429, no hay datos | **No demostrada** | Inspeccionar HTTP status, scope y límites; no modificar permisos a ciegas |
| P. Endpoint alias distinto del modelo supuesto | Misma etiqueta, otro contrato de API | **Alta** como riesgo de integración | Mapear `dsv4flash` → `base_url`, `model`, `provider` y protocolo reales |

**Regla de diagnóstico:** antes de retocar prompts, contestar tres preguntas por request: **¿se ofreció la herramienta? ¿el proveedor devolvió una llamada estructurada válida? ¿el handler realmente se ejecutó?**

---

## 5. Análisis específico por proveedor

### 5.1 Qwen (China): el contrato importa más que la palabra «ejecutar»

La documentación oficial de Alibaba describe un ciclo de dos llamadas al modelo: solicitud con lista de funciones → `tool_calls` → **aplicación externa ejecuta la función** → nueva entrada con el resultado. Si el modelo juzga que no debe usar una herramienta, puede responder con lenguaje natural. Por eso un ACK es **compatible** con el funcionamiento nominal de `tool_choice="auto"`, aunque viole la meta específica del nodo. [S1][S2]

**Hallazgos de comunidad con reproducción:**

- Qwen3 issue `#1817`: modelo que razona que debe llamar una herramienta, pero no emite `tool_calls`. [S3]
- Qwen3 issue `#1452`: `tool_calls` vacío con Hermes, pese al arranque de función de herramientas. [S4]
- Qwen3.8 issue `#236`: más fallos en prompts extensos con `enable_thinking=false`; un usuario informa mejoría con thinking activo. Esto no prueba una solución universal. [S5]
- Qwen3 issue `#1894`: plantilla Qwen3.8 que espera diccionario de argumentos en historial, pero recibe string JSON OpenAI. [S6]
- Qwen3.8 issue `#244`: rechaza mensajes `system` en mitad del historial; una transformación mal diseñada también puede arruinar reutilización de prefijo caché. [S7]
- Qwen-Agent issue `#992`: deltas de llamadas paralelas intercalados pueden mezclarse si se agregan a la llamada «más reciente», en vez de usar `index`. [S20]
- vLLM issue `#45439`: un `<tool_call>` completo que llega en un único delta puede no extraerse en determinado parser. [S14]
- vLLM issue `#58147`: hay reportes del error inverso, convertir ejemplos de tool-call en llamadas reales; **nunca ejecutar markup hallado en contenido sin validar el protocolo**. [S15]

**Soluciones específicas Qwen:**

1. Inspeccionar el endpoint concreto de `qwen38flash-auditor`, `room-qwen38`, `qwen38max`: API alojada vs vLLM/SGLang/llama.cpp; modelo concreto; `tool_call_parser`; `reasoning_parser`; `chat_template`.
2. Preferir `tools` nativos JSON Schema y `tool_choice` que soporte *esa* ruta. **No asumir `required` válido en Qwen.** Una función nombrada puede probarse solo cuando se conoce qué función necesita ese nodo.
3. Probar `enable_thinking=true/false` como variable de experimento, no como ajuste global.
4. Dar únicamente las herramientas autorizadas **para ese nodo**; no cargar 40 funciones cuando la tarea solo requiere `get_file_index`.
5. Para historial de Qwen local, normalizar `function.arguments` string JSON → objeto **solo en la frontera interna que exige esa plantilla**; conservar forma OpenAI en las rutas que la requieren.
6. Comparar `stream=false` vs `stream=true`. Si streaming falla, corregir el ensamblador por `index` y `id`; no unir fragmentos por orden de llegada.
7. Evitar `system` intercalados si la plantilla de ese checkpoint los rechaza; mantener sistema estable y pasar actualizaciones del task-state por canal compatible.

### 5.2 DeepSeek: llamadas perdidas y `reasoning_content`

Para `dsv4flash` y `dsv4pro` **hay que confirmar los modelos reales**: son identificadores del Router, no un contrato de proveedor por sí mismos. La documentación de DeepSeek incluye `deepseek-flash` y `deepseek-v4-pro`; una ruta a través de Alibaba u otro relay puede usar otros IDs o parámetros. [S8][S9][S27]

En Chat Completions, la guía oficial indica:

- `tool_choice="auto"` permite elegir texto sin herramientas; `required`/función específica pueden estar **no soportados en thinking** (error HTTP 400). No aplicar un «force tool» indiscriminado. [S8]
- Cuando `tools` está presente y thinking está habilitado, en turnos siguientes se debe conservar **`reasoning_content` completo** conforme al contrato del proveedor. Omitirlo puede dar 400. [S9]
- El modelo devuelve **instrucciones** de función; el cliente las ejecuta y añade los mensajes `role="tool"`. [S27]
- Existe reporte `DeepSeek-V3 #1244` de V4-Pro emitido como texto en lugar de `tool_calls`; y reportes del harness sobre sesiones con respuesta solo de razonamiento declaradas terminadas. [S10][S21]

**Soluciones específicas DeepSeek:**

1. Para trabajo con tool calls, construir request de formato `messages` + `tools` consistente con el endpoint; registrar `thinking`, `reasoning_effort`, `tool_choice` y modelo real.
2. Si falla la emisión en thinking, probar **non-thinking** en una cohorte controlada y función nombrada donde el proveedor la soporte; comparar tasa de ejecución y calidad. No borrar razonamiento si la API lo exige.
3. Preservar mensajes del asistente con campos `reasoning_content`, `content`, `tool_calls` y los correspondientes resultados `role="tool"` antes del siguiente request.
4. En Responses API, respetar el formato propio de `function_call` y `function_call_output`, distinto de Chat Completions; evitar interpolar mensajes entre llamada y salida si el gateway rechaza ese orden. [S22]
5. Clasificar un turno «solo razonamiento, sin herramienta ni respuesta» como `NO_ACTION`, **no como `COMPLETED`** cuando la tarea requiere ejecución.
6. Reducir herramientas ofertadas, longitud del historial, salida máxima de razonamiento, y probar tarea más corta; repetir solo si hay presupuesto y cero efectos realizados.

### 5.3 GLM-5.2: conservar lo que funciona, no asumir perfección

`glm52` pasó en tu lote. Se debe mantener su contrato actual como **baseline congelada**. En paralelo, hay reportes externos de GLM-5.2 en vLLM con `finish_reason="stop"` en lugar de tool call, un bug de toolcall forzado sin parsear y fugas de XML dentro de reasoning. [S11][S12][S28]

**Atención al parámetro `tool_stream`:** la guía general de Function Calling de Alibaba señala que, para GLM en esa integración, hay que configurar `extra_body={"tool_stream": True}` para recibir las llamadas. La guía específica de GLM de Alibaba precisa que el parámetro afecta el *streaming* de argumentos y solo tiene efecto con `stream=true`. Estas indicaciones se refieren a **rutas/modos determinados**, no a toda API GLM. Por tanto, probarlo únicamente en el gateway Alibaba implicado, sin cambiar el `glm52` que ya pasa ni concluir que es una solución universal. [S23][S24]

**Soluciones GLM:** aislar combinaciones modelo/endpoint/parser/streaming; mantener `glm52` estable; medir con y sin thinking, temperatura 0 donde corresponda, y comprobar que `tool_calls` y recibos coinciden. Evitar copiar configuraciones de vLLM a Z.ai Cloud o viceversa.

---

## 6. Soluciones priorizadas (impacto, costo, riesgo)

| Prioridad | Solución | Impacto esperado | Costo / riesgo | Criterio para aceptar |
|---|---|---|---|---|
| **P0** | Congelar camino PASS de `glm52`, `qwen38max/motores` | Evita regresión | Bajo | Sin cambios de ruta/config para esos nodos |
| **P0** | Log de request y respuesta estructural (sin secretos) | Encuentra capa defectuosa | Bajo | Captura `tools`, `tool_choice`, `finish_reason`, `tool_calls`, timings |
| **P0** | Puerta de ejecución con **recibo real** | Elimina falsos PASS | Medio | PASS solo si handler terminó y existe evidencia verificable |
| **P0** | Fallback B → D **por nodo y sin efectos anteriores** | Corrige ACK recuperables | Medio | Max 1 fallback, sin duplicar operaciones |
| **P0** | Deadline global + tiempo por intento | Evita `TIMEOUT_NODO` por diseño | Medio | Nunca inicia intento sin tiempo mínimo; estados diferenciados |
| **P0** | GitHub Contents `raw` + SHA/tamaño | Soluciona lectura parcial de 1,1 MB | Bajo | bytes completos o error explícito `INCOMPLETE_READ` |
| **P1** | Tabla `provider_capabilities` | Elimina flags incompatibles | Medio | Tests contractuales por endpoint |
| **P1** | Validación de `tool_calls`/schemas/allowlist | Evita tool-calls falsos y argumentos inválidos | Medio | Cero ejecuciones fuera de `allowed_actions` |
| **P1** | Normalización historial reasoning/tool-result | Evita 400 y pérdida de contexto | Medio | Reanudación multi-turn consistente |
| **P1** | Diagnóstico stream vs non-stream | Aísla bug SSE/parser | Medio | Deltas ensamblados por index, mismo resultado semántico |
| **P1** | Reducción de prompt y número de tools | Menos ACK, coste y latencia | Bajo | A/B con métricas de ejecución real |
| **P1** | Checkpoint/fichas pequeñas | Progreso recuperable | Medio | `qwen36` pasa de parcial a sub-tareas auditadas |
| **P2** | Circuit breaker/ruta alternativa | Contiene incidentes de proveedor | Medio/alto | Solo se activa por umbral medido, nunca ocultando FAIL |
| **P2** | Backoff con jitter para 429/503 | Reduce tormenta de reintentos | Bajo/medio | Respeta `Retry-After`, no reintenta errores deterministas |
| **P2** | Actualizar parser/runtime tras suite de tests | Arregla errores conocidos | Medio/alto | Cero regresiones sobre fixtures de tool calling |
| **P3** | Aumentar 150 → 240/300 s *solo por perfil* | Tolera modelos lentos | Bajo en código, medio en SLA | Métricas p95 lo justifican; cola no se bloquea |

**Evitar:** subir `TIMEOUT_NODO` globalmente a todos, reintentar una operación ya confirmada, «reparar» texto XML con regex y ejecutarlo directamente, inventar PASS cuando el modelo solo escribió un diagnóstico, y dar a la IA acceso a herramientas fuera de `allowed_actions`.

---

## 7. Diseño determinista de `run_with_fallback` y TIMEOUT_NODO

### 7.1 Contratos

- **Nodo requiere herramienta:** `requires_tool=true` significa que no puede cerrarse con texto, aunque ese texto sea bueno.
- **Primera ruta:** layout B con herramientas en JSON Schema y la política del proveedor.
- **Detección:** `ACK_NO_TOOL`, `TEXT_NO_TOOL`, `REASONING_ONLY`, `TOOL_EMITTED`, `TOOL_INVALID`, `TOOL_EXECUTED`, `TIMEOUT_ATTEMPT`, `TIMEOUT_TOTAL`.
- **Fallback:** solo si **ninguna operación tuvo efecto**; layout D_solo_tarea, sin «estoy listo», con objetivos de ejecución medibles.
- **Verificación:** dispatcher comprueba nombre/argumentos contra allowlist y schema; genera `receipt` del handler; la puerta valida evidencia.
- **Cierre:** `PASS` únicamente tras contrato de salida; `PARTIAL`, `FAILED`, `DEFERRED` permanecen distintos.

### 7.2 Microflujo horizontal transversal

```text
COLA → CLAIM_NODO → CARGAR_CONTRATO → CHECK_ALLOWLIST → REQUEST_LAYOUT_B
→ NORMALIZAR_RESPUESTA → ¿TOOL_CALL VÁLIDA? ─SÍ→ DISPATCH_AUTORIZADO
→ RECEIPT → VERIFY_EVIDENCE → PASS / PARTIAL / FAIL
                                  │
                                  NO
                                  ↓
          CLASIFICAR_ACK / NO_ACTION / PARSER_LOSS → ¿EFECTO_PREVIO?
          ├─ SÍ → STOP_DUPLICATE_RISK → ESCALATE
          └─ NO → ¿TIEMPO_DISPONIBLE? → REQUEST_LAYOUT_D_SOLO_TAREA
                    → NORMALIZAR → DISPATCH → RECEIPT → VERIFY → PASS / FAIL
          └─ SIN PRESUPUESTO → DEFERRED_TIMEOUT_BUDGET → REQUEUE_CHECKPOINT
```

### 7.3 Presupuestos por nodo: dos modalidades válidas

**Modalidad A — mantener tope duro de 150 segundos:** tiempo en cola **fuera o dentro del reloj según contrato**, pero declararlo. Ejemplo de valores iniciales para probar, **no mediciones reales**:

| Fase | Reserva orientativa |
|---|---:|
| Intento B, límite de espera | 50 s |
| Clasificación/cancelación | 5 s |
| Intento D, límite de espera | 65 s |
| Ejecución externa + validación | 20 s |
| Margen | 10 s |
| **Total** | **150 s** |

Problema: si el proveedor normalmente tarda 90–140 s en la primera respuesta, este presupuesto **no es realista**. La salida correcta es `DEFERRED`/escalamiento, no un PASS ficticio. Medir antes de fijarlo.

**Modalidad B — SLA distinto para nodos elegibles para fallback:** `timeout_total=240 s` o valor basado en p95 real solo en el perfil `retry_eligible`; `attempt_timeout` por ejecución; **watchdog total real** más un número máximo de intentos y reencolado sin repetir efectos. No ampliar `TIMEOUT_NODO` global. Esto puede elevar tiempo de ocupación, así que el scheduler debe limitar concurrencia y proteger al resto de la cola.

Regla matemática: `remaining = deadline_monotonic - now_monotonic`. Si `remaining < min_required_for_next_attempt + execution_reserve`, **no iniciar otro intento**.

### 7.4 Código de referencia adaptable (Python 3.11+, no acoplado a tu repo)

El siguiente es un **núcleo lógico de ejemplo**, no un parche probado sobre tus clases actuales. El adaptador `call_model` y el handler real deben implementar sus contratos. El código no ejecuta ninguna función por el solo hecho de encontrar XML/texto en `content`.

```python
import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

ACK = re.compile(
    r"^\s*(entendido|listo|estoy listo|estoy a la espera|recibido|"
    r"de acuerdo|ok(?:ay)?|understood|ready|acknowledged|"
    r"好的|收到|明白了|准备好了)[\s.,!¡。]*(?:\.{0,3})\s*$",
    re.I,
)

@dataclass(frozen=True)
class NodePolicy:
    node_id: str
    requires_tool: bool = True
    allow_fallback: bool = True
    total_timeout_s: float = 150.0
    first_attempt_s: float = 55.0
    fallback_attempt_s: float = 70.0
    tool_reserve_s: float = 15.0
    min_fallback_s: float = 25.0


def classify_response(response: dict[str, Any], requires_tool: bool) -> str:
    """response = objeto normalizado Chat Completions, no texto crudo."""
    msg = response.get("message") or {}
    calls = msg.get("tool_calls") or []
    if calls:
        return "TOOL_EMITTED"  # Aún NO equivale a ejecutado
    text = str(msg.get("content") or "").strip()
    reason = str(msg.get("reasoning_content") or "").strip()
    if requires_tool:
        if not text and reason:
            return "REASONING_ONLY"
        if ACK.fullmatch(text) or (len(text) < 150 and
                                   any(k in text.lower() for k in
                                       ("estoy listo", "a la espera", "ready to"))):
            return "ACK_NO_TOOL"
        return "TEXT_NO_TOOL"
    return "FINAL_TEXT" if text else "EMPTY"


async def run_with_fallback(
    policy: NodePolicy,
    call_model: Callable[[str, float], Awaitable[dict]],
    dispatch_and_receipt: Callable[[list[dict], float], Awaitable[list[dict]]],
    verify_receipts: Callable[[list[dict]], bool],
) -> dict:
    """No hace reintentos automáticos después de efectos externos.

    call_model(layout, timeout_s) envía tools, aplica configuración de
    proveedor y devuelve {message:{content,reasoning_content,tool_calls}}.
    dispatch_and_receipt valida allowlist/JSON schema y ejecuta handlers.
    Los handlers usan idempotency keys y escriben recibos durables.
    """
    deadline = time.monotonic() + policy.total_timeout_s
    layouts = ["B"] + (["D_SOLO_TAREA"] if policy.allow_fallback else [])
    history = []

    for idx, layout in enumerate(layouts):
        remaining = deadline - time.monotonic()
        reserve = policy.tool_reserve_s
        min_attempt = policy.min_fallback_s if idx else 1.0
        if remaining < min_attempt + reserve:
            return {"state": "DEFERRED_TIMEOUT_BUDGET", "history": history}

        requested = (policy.first_attempt_s if idx == 0
                     else policy.fallback_attempt_s)
        attempt_timeout = min(requested, remaining - reserve)
        try:
            async with asyncio.timeout(attempt_timeout):
                response = await call_model(layout, attempt_timeout)
        except TimeoutError:
            history.append({"layout": layout, "state": "TIMEOUT_ATTEMPT"})
            # NOTA: si proveedor/proxy pudo iniciar acciones por su cuenta,
            # verificar ledger externo ANTES de reintentar.
            continue
        except Exception as exc:
            # En producción: tipificar (429, 400, 401, 503, conexión...),
            # y no reintentar errores permanentes.
            return {"state": "PROVIDER_ERROR", "error_type": type(exc).__name__,
                    "history": history}

        state = classify_response(response, policy.requires_tool)
        history.append({"layout": layout, "state": state})
        if state == "TOOL_EMITTED":
            calls = response["message"]["tool_calls"]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"state": "DEFERRED_BEFORE_DISPATCH", "history": history}
            # dispatch SOLO invocaciones válidas y autorizadas.
            # Debe persistir el estado de cada llamada antes de actuar.
            try:
                async with asyncio.timeout(remaining):
                    receipts = await dispatch_and_receipt(calls, remaining)
            except TimeoutError:
                return {"state": "TOOL_UNKNOWN_OUTCOME_RECONCILE",
                        "history": history}
            except Exception as exc:
                return {"state": "TOOL_EXECUTION_FAILED",
                        "error_type": type(exc).__name__, "history": history}
            if verify_receipts(receipts):
                return {"state": "PASS", "receipts": receipts,
                        "history": history}
            return {"state": "FAILED_EVIDENCE", "receipts": receipts,
                    "history": history}
        if not policy.requires_tool and state == "FINAL_TEXT":
            return {"state": "PASS_TEXT", "history": history}
        # No hubo tool call. Solo aquí se permite otro layout, si hay tiempo.

    return {"state": "FAILED_NO_TOOL", "history": history}
```

**Limitaciones deliberadas del ejemplo:**

- `asyncio.timeout` cancela la corrutina cliente, pero **no garantiza** que una petición HTTP ya enviada haya dejado de procesarse en el proveedor. Si hubo efectos externos antes de la cancelación, la reconciliación es obligatoria. [S26]
- El código anterior recibe *tool calls ya normalizadas*. Un parser de SSE es otro módulo y debe someterse a tests de deltas.
- Un `TOOL_EMITTED` inválido debe devolver `TOOL_INVALID`, no pasar a ejecución. `dispatch_and_receipt` **debe** validar esquema, autorización, versión del contrato y bloqueos de objetivo.
- En operaciones de escritura, `idempotency_key = hash(node_id + goal_id + action + canonical_args + source_sha)`; guardar `PENDING → RUNNING → SUCCEEDED/FAILED/UNKNOWN` en ledger duradero antes de emitir la petición externa.
- Si se intentó escribir y el resultado es `UNKNOWN`, **nunca** iniciar una segunda escritura sin consultar si el efecto ocurrió.
- En streaming, se deben reconstruir deltas de llamadas **por `index`** y preservar su `id`; `finish_reason="tool_calls"` no suple argumentos ausentes.

### 7.5 Perfiles propuestos (ejemplo de configuración)

```yaml
executor:
  default:
    layout: B
    requires_tool: true
    timeout_total_s: 150
    retry_on_no_tool: false
  profiles:
    dsv4flash:
      retry_on_no_tool: true
      retry_layout: D_SOLO_TAREA
      max_model_attempts: 2
      timeout_total_s: 150       # modalidad A, confirmar con p95
      timeout_first_s: 55
      timeout_fallback_s: 70
      tool_reserve_s: 15
    dsv4pro:
      retry_on_no_tool: true
      retry_layout: D_SOLO_TAREA
      max_model_attempts: 2
      timeout_total_s: 150
    room-qwen38:
      retry_on_no_tool: false    # primero diagnosticar parser/dispatcher
    glm52:
      retry_on_no_tool: false    # congelar PASS
    qwen38max:
      retry_on_no_tool: false    # congelar PASS
```

Si hay evidencia de p95 superior al tope, mover **solo los nodos autorizados** a modalidad B en un cambio separado. Los tiempos YAML son presupuestos orientativos, no tiempos medidos.

---

## 8. Qué hacer con el archivo de GitHub de 1,1 MB

### Problema exacto

GitHub documenta que en **Get repository content**:

- Archivos `≤ 1 MB`: todas las representaciones compatibles.
- Archivos `> 1 MB y ≤ 100 MB`: solo medios `raw` u `object`; en `object`, `content` está vacío y `encoding="none"`.
- Archivos `> 100 MB`: ese endpoint no sirve. [S13]

Por tanto, **no puede afirmarse que GitHub trunca físicamente el archivo a 1 MB**. Puede ocurrir que el cliente use representación inadecuada o que un gateway/herramienta LLM corte el contenido por caracteres, tiempo o tokens. La única manera de saberlo es comparar bytes y SHA.

### Solución preferida, sin enviar 1,1 MB al modelo

```text
GITHUB_TREE/METADATA → PATH+SHA+SIZE → GET_RAW → VALIDAR_BYTES+SHA
→ PARSER_LOCAL → ÍNDICE_150_LÍNEAS → IDENTIFICAR_INPUTS
→ FRAGMENTOS_RELEVANTES → LLM → HALLAZGOS_CON_LINEAS+SHA
```

**Acciones:**

1. Leer metadatos: ruta, tamaño, SHA del blob, commit y última fecha de modificación.
2. Obtener bytes completos mediante `Accept: application/vnd.github.raw+json` en el endpoint Contents adecuado **o** endpoint Git Blobs. [S13][S29]
3. Comparar `len(bytes)` con tamaño anunciado cuando aplique; calcular SHA del contenido/commit para evitar mezclas de versiones. Si se recibió menos, lanzar `INCOMPLETE_READ`.
4. Guardar íntegro el archivo en almacenamiento controlado; **no** ponerlo completo en el contexto del modelo.
5. Extraer primeras ~150 líneas *con números de línea*; localizar encabezados `INPUT`, bloques, índices y offsets a través de un parser local determinista.
6. Enviar al auditor trozos **pertinentes**, con metadatos `path`, `sha`, `line_start`, `line_end`; no perder referencias al archivo original.
7. Limitar fragmentos por bytes/tokens y repetir hasta cubrir entradas requeridas; generar un mapa de cobertura (`total_chunks`, `processed`, `skipped`).
8. El auditor solo puede emitir `PASS` documental si la cobertura de todas las zonas obligatorias está completa. De otro modo `PARTIAL_READ`.

**Ejemplo de línea de comandos conceptual** (debe usarse la ruta exacta y credenciales mediante un mecanismo seguro, nunca insertar tokens en el informe):

```bash
# Ejemplo para repositorios y permisos ya autorizados.
curl -fsSL \
  -H 'Accept: application/vnd.github.raw+json' \
  'https://api.github.com/repos/OWNER/REPO/contents/RUTA/ARCHIVO.md?ref=main' \
  -o documento_completo.md
wc -c documento_completo.md
nl -ba documento_completo.md | sed -n '1,150p'
```

**Advertencia:** según endpoint/redirect, los headers y el comportamiento del cliente pueden variar. El test debe verificar que la salida sea Markdown real, no un JSON de error, HTML de autenticación ni una respuesta de gateway truncada.

---

## 9. Diseño de evidencias: PASS significa que algo ocurrió

### 9.1 Modelo mínimo del recibo

```json
{
  "goal_id": "G001",
  "node_id": "dsv4flash",
  "attempt": 2,
  "layout": "D_SOLO_TAREA",
  "provider": "deepseek-official-or-relay",
  "resolved_model": "MODEL_ID_REAL",
  "tool_call_id": "call_123",
  "tool_name": "read_file_index",
  "tool_args_sha256": "hash_de_argumentos_normalizados",
  "idempotency_key": "hash_objetivo_y_accion",
  "handler_started_at": "ISO8601",
  "handler_finished_at": "ISO8601",
  "handler_status": "SUCCEEDED",
  "evidence": {
    "source_path": "ruta-del-archivo",
    "source_sha": "sha-del-commit-o-blob",
    "lines": [1, 150],
    "bytes_read": 12000
  },
  "validation": "PASS"
}
```

El recibo debe proceder del **ejecutor**, no del texto generado por el modelo. Los hashes del ejemplo son marcadores de esquema, no valores reales. Omitir tokens y secretos de API en logs.

### 9.2 Taxonomía de errores que no deben mezclarse

| Código | Significado | Acción adecuada |
|---|---|---|
| `ACK_NO_TOOL` | Acuse sin herramienta | Fallback seguro según presupuesto |
| `TEXT_NO_TOOL` | Respuesta sustantiva pero faltó la acción exigida | No PASS; fallback o revisión de contrato |
| `REASONING_ONLY` | Solo razonamiento sin acción/resultado | No PASS; diagnóstico thinking/stop |
| `TOOL_PARSE_LOST` | Hay sintaxis raw de llamada pero no `tool_calls` estructurada | Corregir parser, **no** ejecutar XML a ciegas |
| `TOOL_INVALID` | Nombre no permitido, argumentos fuera de esquema | Rechazo, registro, posible reparación segura |
| `TOOL_DISPATCH_FAILED` | Llamada válida pero dispatcher falló | Revisar herramienta/permiso/sesión |
| `TOOL_UNKNOWN_OUTCOME_RECONCILE` | Timeout después de iniciar efecto | Verificar ledger/externo antes de otro intento |
| `INCOMPLETE_READ` | Bytes/documento incompletos | Releer raw/chunks; no análisis completo |
| `TIMEOUT_ATTEMPT` | Intento individual excedido | Evaluar tiempo global y side effects |
| `TIMEOUT_TOTAL` | Deadline absoluto agotado | `DEFERRED` o FAIL con checkpoint |
| `PROVIDER_400_CONTRACT` | Solicitud incompatible con endpoint | Corregir protocolo, no backoff ciego |
| `PROVIDER_429_RETRYABLE` | Límites de cuota/concurrencia | Respetar Retry-After, con límite |
| `PASS` | Handler + evidencia + validación | Cerrar el nodo |

---

## 10. Pruebas de regresión mínimas (antes de modificar producción)

**Montar una matriz 4 × 2 × 2 × 2:** al menos cuatro rutas de modelo/endpoint, layouts B/D, thinking ON/OFF si soportado y streaming ON/OFF si soportado; ejecutar varias repeticiones por celda. Usar la **misma tarea mínima** y una herramienta de lectura sin efectos.

| Test | Entrada | Resultado esperado |
|---|---|---|
| T01 | `glm52`, baseline B | Mismo PASS y mismos recibos de referencia |
| T02 | `qwen38max/motores`, baseline B | Sin regresión de contenido ni ejecución |
| T03 | `dsv4flash` devuelve «Entendido. Estoy listo.» | `ACK_NO_TOOL`, jamás PASS |
| T04 | `dsv4pro` devuelve «Listo. Estoy a la espera.» | `ACK_NO_TOOL`, fallback solo si hay tiempo |
| T05 | `room-qwen38` genera `tool_calls` pero handler falla | `TOOL_DISPATCH_FAILED`, no «model didn't call» |
| T06 | Texto con `<tool_call>` dentro de código Markdown | Ninguna ejecución, rechazo de llamada textual |
| T07 | Call estructurada válida, `arguments` JSON inválido | `TOOL_INVALID`, ninguna ejecución |
| T08 | Dos tool-calls intercaladas vía SSE | Reconstrucción por `index`/`id`, args no mezclados |
| T09 | Thinking DeepSeek y respuesta anterior con `reasoning_content` | Historial preservado, sin 400 por pérdida |
| T10 | DeepSeek thinking + `tool_choice=required` no admitido | Error contractual identificado, no reintento idéntico |
| T11 | Archivo de 1,1 MB leído sin raw | Detectar representación insuficiente si se produce |
| T12 | Archivo de 1,1 MB con raw y validación | Verificación completa o error explícito |
| T13 | Intento B=55 s sin call, quedan >70 s | Puede intentar D si reserva mínima garantizada |
| T14 | Intento B consume casi los 150 s | No inicia D; `DEFERRED_TIMEOUT_BUDGET` |
| T15 | Tool write ejecutada y timeout al recibir ACK de red | **No** se duplica; reconciliación con idempotencia |
| T16 | `allowed_actions` con 8 acciones, modelo llama novena | Rechazo por allowlist |
| T17 | Proveedor 429 con `Retry-After` | Espera limitada / checkpoint, no tormenta |
| T18 | `qwen36` obtiene media evidencia | `PARTIAL`, conserva progreso; nunca PASS definitivo |
| T19 | Contexto largo Qwen thinking=false | Medir frecuencia de `tool_calls` vs thinking=true |
| T20 | Middleware añade `system` a mitad de historial Qwen local | Rechazo preventivo/normalización compatible |

**Métricas a registrar por nodo:** `request_id`, `provider`, `resolved_model`, `endpoint_protocol`, `layout`, `attempt`, `stream`, `thinking`, `tool_choice`, `tools_count`, `input_tokens`, `reasoning_tokens`, `output_tokens`, `queue_ms`, `ttft_ms`, `model_latency_ms`, `tool_latency_ms`, `total_ms`, `finish_reason`, `tool_calls_count`, `valid_calls_count`, `executed_calls_count`, `receipts_count`, `fallback_trigger`, `error_code`, `bytes_requested`, `bytes_received`, `source_sha`.

Definir `execution_success_rate = nodos_con_recibo_verificado / nodos_que_requerían_herramienta`. No sustituir por «número de respuestas HTTP 200» ni «el modelo aseguró haber trabajado».

---

## 11. Instrucciones ejecutables para Claude / agente de código

> **Objetivo:** introducir un fallback determinista por nodo y timeouts seguros, sin romper el layout B que ya funciona. Esta es una especificación para adaptar a los nombres reales del repositorio, **no** una afirmación de que se hayan realizado cambios.

### INPUT BLOCK — CONTRATO

```text
[MODO]
AUDITORIA_ESTRICTA | BACKEND | EJECUTOR | VALIDACION | REGRESION

[ALCANCE]
Solo ensamblaje del prompt del nodo, interfaz con proveedor,
normalizador de tool_calls, dispatcher, ledger, watchdog y tests.

[NO TOCAR]
No cambiar despliegues ni infraestructura. No cambiar globalmente
TIMEOUT_NODO. No tocar la configuración funcional de glm52 y
qwen38max/motores. No eliminar allowed_actions. No alterar el resto
de la cola. No cerrar una tarea sin recibo verificable.

[FASE 1 — LECTURA]
Localizar archivos reales del executor, scheduler, modelos, adapters,
logs de watchdog y tests. Reportar rutas + líneas + commit SHA.
Si no están disponibles, devolver GAP_MISSING_SOURCE, sin inventar rutas.

[FASE 2 — CAPTURA]
Instrumentar request real (sin secretos), response raw y normalizada,
model/tool-call/dispatched/receipt, deadline y tiempos por intento.
Separar NO_TOOL_EMITTED de PARSE_LOST y DISPATCH_FAILED.

[FASE 3 — PARCHE AISLADO]
Agregar run_with_fallback() con allowlist por node_id.
Activarlo inicialmente solo en dsv4flash y dsv4pro.
Layout principal B → detectar ausencia de calls requeridas →
verificar ausencia de side-effects → comprobar tiempo →
layout D_SOLO_TAREA → validar → dispatch → receipt.
No hacer reintentos superiores a max_model_attempts=2.

[FASE 4 — TIMEOUT]
Introducir deadline monotónico total + intento individual +
reserva de ejecución. No crear intento si falta presupuesto.
Conservar default 150 s y preparar perfil individual extendido
solo tras medir p95 y aprobación técnica del cambio.

[FASE 5 — GITHUB]
Para qwen38flash-auditor usar lectura raw, SHA y bytes; entregar
índice (~150 líneas) + INPUTs por separado + mapa de cobertura.
Si archivo incompleto: INCOMPLETE_READ, nunca PASS documental.

[FASE 6 — PRUEBAS]
Implementar T01..T20. Ejecutar baseline antes/después.
Publicar resultados reales con comando, evidencia, logs y diff.

[PUERTA DE ACEPTACION]
PASS = tool handler ejecutado + recibo + validación del objetivo.
ACK, texto sustantivo sin acción, salida parcial o timeout != PASS.

[MICROFLUJO]
DISCOVER → SNAPSHOT → REQUEST_TRACE → HYPOTHESIS → MIN_PATCH
→ REGRESSION → REAL_TOOL_CALL → RECEIPT → VERDICT → HANDOFF

[ENTREGABLES]
1) rutas y líneas afectadas; 2) parche mínimo; 3) tests;
4) tabla antes/después; 5) rollback; 6) gaps no resueltos.
```

### Orden sugerido de implementación, sin alterar rutas que pasan

1. **Lectura/auditoría:** obtener baseline y trazas reales de un FAIL y un PASS.
2. **Normalizar estados:** distinguir `ACK_NO_TOOL` de `TOOL_DISPATCH_FAILED`.
3. **Agregar recibos y allowlist:** no modificar comportamiento de envío.
4. **Prueba en staging:** activar fallback solo en `dsv4flash`; comparar 20 casos controlados.
5. **Extender a `dsv4pro`:** únicamente si el patrón y tasa de mejora lo justifican.
6. **Investigar `room-qwen38`:** antes de introducir fallback comprobar si el parser pierde tool calls.
7. **Arreglar lector GitHub:** entrega por índice y chunks con SHA.
8. **Dimensionar deadline según p95 real**; considerar perfil ampliado por nodo.
9. **Correr T01–T20**, dejar evidencia y plan de rollback.
10. **Handoff:** un nodo, un estado, recibos, responsable y siguientes pasos.

---

## 12. Decisiones: qué haría primero y por qué

**Primera corrección:** impedir que una respuesta que no incluye herramienta y recibo cierre un nodo etiquetado «requiere ejecutar». Esta es una corrección de contrato que sirve para **todos** los modelos.

**Segunda corrección:** introducir `run_with_fallback` con deadline real, máximo dos intentos, comprobación de efectos previos y activación selectiva para DeepSeek. El error actual no es solo «150 s demasiado bajo»; es que el segundo intento se dispara sin presupuesto suficiente en determinados casos.

**Tercera corrección:** inspeccionar respuestas originales de `room-qwen38`. Si generó `<tool_call>` raw pero `tool_calls=[]`, el camino es parser/template; **no** repetir exclusivamente el prompt.

**Cuarta corrección:** lectura de GitHub raw y fragmentada para el auditor Qwen Flash; no volver a pedir al modelo el archivo completo de 1,1 MB.

**Quinta corrección:** aislar diferencias de proveedor: Qwen `required`, DeepSeek thinking y `reasoning_content`, GLM y `tool_stream` dependiendo del gateway.

**Resultado buscado:** pasar de «el modelo dijo que trabajó» a «el ejecutor demuestra qué hizo, dónde, cuándo y con qué resultado», manteniendo cola, permisos y estados íntegros.

---

## 13. Fuentes verificables y grado de aplicabilidad

Las referencias se consultaron en esta investigación, con fecha de corte indicada. **Un issue sin solución upstream no debe tratarse como bug confirmado en tu Router**; revisar los detalles de versión y endpoint antes de aplicar parches. Se listan URL directas para que el archivo `.md` sea autocontenido incluso fuera de ChatGPT.

### Documentación oficial (contratos)

- **[S1] Alibaba Cloud, Function Calling (chino):** https://help.aliyun.com/zh/model-studio/qwen-function-calling — flujo de ejecución, selección de herramientas y limitación de `required` en Qwen.
- **[S2] Alibaba Cloud, OpenAI-compatible Chat Completions:** https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/ — definición de `tools` y `tool_choice`.
- **[S8] DeepSeek, Chat Completions API:** https://api-docs.deepseek.com/api/create-chat-completion/ — parámetros y restricciones en thinking.
- **[S9] DeepSeek, Thinking Mode:** https://api-docs.deepseek.com/guides/thinking_mode/ — conservación de `reasoning_content` cuando existen tools.
- **[S13] GitHub REST, repository contents:** https://docs.github.com/en/rest/repos/contents — tratamiento por tamaño (≤1MB, 1–100MB, >100MB).
- **[S23] Alibaba Cloud, GLM por Model Studio:** https://help.aliyun.com/zh/model-studio/glm — `tool_stream` y streaming.
- **[S24] Alibaba Cloud, Function Calling GLM en gateway:** https://docs.bailian.console.aliyun.com/en/model-studio/qwen-function-calling — notas de integración por proveedor.
- **[S26] Python `asyncio.timeout` / `wait_for`:** https://docs.python.org/3/library/asyncio-task.html — deadline y cancelación.
- **[S27] DeepSeek Tool Calls:** https://api-docs.deepseek.com/guides/tool_calls/ — ciclo de herramienta ejecutada por cliente.
- **[S29] GitHub REST, Git blobs:** https://docs.github.com/en/rest/git/blobs — obtención de contenido por SHA.
- **Qwen oficial, guía de Function Calling:** https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md — plantilla Hermes, Qwen-Agent y vLLM.

### Comunidad Qwen / China / reproducibles

- **[S3] Qwen issue #1817:** https://github.com/QwenLM/Qwen3/issues/1817 — piensa llamar herramienta, no emite call.
- **[S4] Qwen issue #1452:** https://github.com/QwenLM/Qwen3/issues/1452 — `tool_calls` vacío con Hermes.
- **[S5] Qwen3.8 issue #236:** https://github.com/QwenLM/Qwen3.8/issues/236 — contexto largo y thinking off.
- **[S6] Qwen issue #1894:** https://github.com/QwenLM/Qwen3/issues/1894 — argumentos históricos string vs map en plantilla.
- **[S7] Qwen3.8 issue #244:** https://github.com/QwenLM/Qwen3.8/issues/244 — `system` fuera de la primera posición.
- **[S14] vLLM issue #45439:** https://github.com/vllm-project/vllm/issues/45439 — llamada completa en delta único no detectada.
- **[S15] vLLM issue #58147:** https://github.com/vllm-project/vllm/issues/58147 — invocaciones falsas por parsear ejemplos de markup.
- **[S16] vLLM issue #39056:** https://github.com/vllm-project/vllm/issues/39056 — llamadas dentro de `<think>` perdidas.
- **[S17] Qwen-Agent issue #504:** https://github.com/QwenLM/Qwen-Agent/issues/504 — reintento de argumentos MCP defectuosos.
- **[S18] Qwen-Agent issue #798:** https://github.com/QwenLM/Qwen-Agent/issues/798 — tool no registrado por dependencia.
- **[S19] Qwen-Agent issue #635:** https://github.com/QwenLM/Qwen-Agent/issues/635 — problemas de protocolos de tool calls con DeepSeek R1.
- **[S20] Qwen-Agent issue #992:** https://github.com/QwenLM/Qwen-Agent/issues/992 — interleaving de tool-calls en streaming.
- **[S25] Qwen issue #2335:** https://github.com/QwenLM/Qwen/issues/2335 — latencia elevada en uso agentic largo de Token Plan (caso reportado, no SLA).
- **vLLM issue #54808:** https://github.com/vllm-project/vllm/issues/54808 — `required` y parser Qwen; incluye referencia a solución de versión.

### Comunidad DeepSeek y GLM / reproducibles

- **[S10] DeepSeek-V3 issue #1244:** https://github.com/deepseek-ai/DeepSeek-V3/issues/1244 — llamada escrita como `content` sin `tool_calls`.
- **[S21] DeepSeek Harness discusión #6431:** https://github.com/deepseek-ai/deepseek-harness/discussions/6431 — turno solo de razonamiento marcado completo.
- **[S22] DeepSeek integrations issue #740:** https://github.com/deepseek-ai/awesome-deepseek-integration/issues/740 — restricciones de adyacencia en Responses API.
- **[S11] vLLM issue #47714:** https://github.com/vllm-project/vllm/issues/47714 — GLM-5.2, `stop` en lugar de tool call en algunos escenarios.
- **[S12] vLLM issue #48095:** https://github.com/vllm-project/vllm/issues/48095 — GLM-5.2, llamada forzada sin parsear.
- **[S28] vLLM issue #46040:** https://github.com/vllm-project/vllm/issues/46040 — GLM, XML de tool call dentro de reasoning.
- **DeepSeek Harness discusión #1850:** https://github.com/deepseek-ai/deepseek-harness/discussions/1850 — error de historial de reasoning en thinking.
- **vLLM issue #49981:** https://github.com/vllm-project/vllm/issues/49981 — `required` puede provocar fallo del backend GLM específico.

---

## 14. Límites de esta investigación

- **No se han ejecutado** llamadas a los endpoints privados de tu Router, ni se ha visto el JSON exacto de cada request/response.
- **No se ha aplicado** un parche, actualizado el timeout, ni desplegado software.
- Las «10 pasadas» son contrastes documentales por subtema; **no** certifican una auditoría experimental de diez ciclos del sistema real.
- Los tiempos de 55/70/150/240 s en ejemplos son **configuración propuesta**; el ajuste definitivo debe proceder de latencias observadas y reglas de cola.
- Las referencias no prueban que los alias `dsv4flash`, `dsv4pro` o `room-qwen38` apunten a una versión determinada: registrar `base_url`, proveedor, nombre real de modelo y protocolos.
- Los issues de comunidad pueden estar abiertos, cerrados o mitigados dependiendo de la versión; nunca aplicar soluciones de un issue sin reproducir primero el fallo.

**Conclusión final:** integrar fallback por nodo **sí** es una pieza relevante, pero no es suficiente por sí sola. La solución robusta consiste en **contrato de tools por proveedor + clasificador de no-ejecución + dispatcher autorizado + recibos verificables + control de plazos + lectura documental completa por chunks**. Ese diseño explica la mejora parcial del layout B y previene que nuevos retries generen falsos PASS o dobles acciones.
