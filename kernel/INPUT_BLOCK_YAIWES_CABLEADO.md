# INPUT BLOCK ADJUNTO — OBJETIVOS YAIWES: AUDITORÍA Y RECONSTRUCCIÓN DEL CABLEADO

**run_id:** `20261104-kernel01` · **creado:** 2026-11-06 · **origen:** orden literal del owner
**modo:** `VERBATIM, READ_ONLY` — este fichero NO se edita: se deriva del texto del owner.
**hash de referencia del adjunto del owner (guía de organización):**
`organización de la raíz del repo.md` → sha256 `5c77e0051a4e8caaee123b5e199980d98c9cd7b144ff246dbb2cccf415048943`, 35537 B.
**Ese contenido YA vive en el repo como `AGENTS.md` (mismo sha256, mismo tamaño): no se duplica ni se copia.**

---

## 0. SEPARACIÓN DE RAÍCES (regla de organización, texto del owner + guía adjunta)

El owner ordena usar **la raíz de organización de la guía adjunta** + **la separación de raíces adicional de su texto**.

Raíces canónicas (guía adjunta §2, `ESTRUCTURA OFICIAL DEL REPOSITORIO`), que se respetan y **no** se crean de oficio:

```text
ROUTER-INTELIGENTE-UNIVERSAL/
├── README/                    ├── AGENTS.md            (guía de organización, FROZEN)
├── ARQUITECTURA 1/            ├── AGENTES/             (Claude core, Codex, otros agentes)
├── ARQUITECTURA 2/            ├── frontend/src/        (ui, components, pages, features)
├── ARCHIVOS PROYECTOS/        ├── COMPONENTES OPEN SOURCE/
│   └── archivos adjuntos/     ├── backend/             (api, router, controllers, services)
│       ├── bitácora/          ├── systems/             (system_1, system_2)
│       ├── stated JSON/       ├── agents/              (orchestrator, specialists, registry)
│       └── Craxy wall/        ├── engines/             (hermes, adapters)
├── models harnes/             ├── integrations/        (vercel, huggingface, http, mcp)
│   ├── deepseek/              ├── handoff/             (contracts, schemas, workflows)
│   └── providers/             ├── connections/         (registry, topology, endpoints, healthchecks)
├── shared/                    ├── config/              ├── tests/  ├── docs/  └── scripts/
```

Separación de raíces ADICIONAL por el texto del owner (cada elemento queda en SU raíz, sin mezclas):

| Raíz | Contenido que debe vivir ahí | Regla |
|---|---|---|
| `connections/` | **Archivo central único de distribución de cableado**: Vercel, HuggingFace, MCP, HTTP, servidor de cómputo, almacenamiento. Es el centro de distribución; no puede ser un "barrio chino de cables". | Una conexión = un registro con consumidor, proveedor, protocolo, endpoint, healthcheck y evidencia. |
| `kernel/` | Handoff del sistema completo de cableado y comunicación + `INPUT_BLOCK` Frozen + estado. | El estado solo aquí y en el Dataset. |
| `frontend/` | Chat YAIWES, selectores, botones ON/OFF de agentes y de **encendido/reinicio de servidores**, configuración de la UI. | La UI no contiene motores ni lógica de ejecución. |
| `backend/` | Router, controladores, servicios, orquestación de cola y despertar. | Sin dependencias ocultas. |
| `engines/` | Hermes + adaptadores de motores (intocables salvo autorización expresa). | Los motores ejecutan, no rediseñan. |
| `models harnes/` | DeepSeek y proveedores; adaptadores; **1 modelo local por servidor**. | Proveedores desacoplados. |
| `integrations/` | Vercel (frontend + trigger de watchdog), HuggingFace (espejo/auto-pull mínimo), HTTP, MCP. | Una responsabilidad por integración. |
| `handoff/` | Contratos, esquemas y workflows de transferencia. | Toda transferencia con origen, destino, estado y resultado. |
| `docs/` | Arquitectura, conectividad y operaciones (lo mínimo; lo que no aporte se borra). | Sin código en documentación. |
| `tests/` | Pruebas del Job Test integral (J01..J13). | Sin notas ni documentos. |

**Raíces adicionales decididas por el owner (nuevas, con justificación):**

| Raíz nueva | Por qué | Qué contiene |
|---|---|---|
| `connections/wiring_registry.yaml` | El owner pide **un solo archivo centralizado** con toda la conexión, con el formato de centro de distribución que describe su texto (servicio, consumidor, proveedor, endpoint, contrato, healthcheck, fallback, estado). `connections/registry.yaml` es el inventario de pares; este es el **centro de distribución** con contrato y política. | Un registro por servicio (nvidia, memoria, storage, mcp, vercel, huggingface, servidores de cómputo, cola, watchdog). Estados: DISCOVERED → CONFIGURED → TESTING → ACTIVE; alternativos FAILED / BLOCKED / DEPRECATED / ORPHANED. |
| `integrations/servers/` | Política de cola/servidores (85 %, 15 min, 1 modelo por servidor, hasta 3 en cola). | Registro de servidores, cola, reglas de failover y contrato de despertar. |
| `ops/job_test.py` + `audit/` | El owner pide un **Job Test integral** (J01..J13) y una auditoría con salidas separables. | El ejecutor de pruebas y sus informes (sin credenciales). |

---

## 1. DIRECTIVA DEL OWNER (VERBATIM)

```
1. todo el code vive en Github huggueface solo espejo auto pull de todo el repo huggueface lo mínimo
posible necesario su función es solo servir de servidor y actualizar al UI aunque vercel no lo haga

todos Servidores pagos de 32 ram cpu

1. servicios de servidores en cola al 85% salta al salta a siguiente servidor 15 minutos sin actividad
el servidor duerme + colocar sistema de encendido y reinicio en la configuración del chat UI + botón
de encendido permanente on off para mantener activo encendidos y evitar caídas de trabajo

2. servidor 2 modelos locales 1 modelo por servidor Salta a el siguiente si sale una llamada hasta 3
servidores en cola al estar lleno espera 1 servidor por modelo termina 15 minutos y abandona el
servidor y duerme

el repo debe tener un solo archivo centralizado con toda la conexión de cómo un centro de distribución
de cableo vercel huggueface MCP HTTP cableo completo servidor de cómputo almacenamiento todo para por
ese servicio investiga como se hace revisa la guía o investiga todo centralizado
handoff de todo el sistema de cableo y comunicación y cableo de readme y arquitectura acrulizado

archivos de code no cableados que no pertenece a el sistema necesario de funcionamiento de code
borrado archivo de notas pruebas o documentos borrados

repo limpio

debes revisar que estaba en los job de historial para detectar que se dañó y desconecto todo el chat
los modelos luego cableas y actulizas archivos readme bitácora handoff

el wachdog lo aplica vercel al encender dispara un tigger para despertar el servidor

2. No autorizar: el motor permanece intacto y el problema sigue pendiente.
Mi recomendación: autorizar únicamente después de comprobar el error, el contexto de la línea y las
pruebas de regresión. Conservar el código anterior para revertirlo.

ningúna clave quedo exoueta no se tocan

Umbral para ACTIVA:
Autenticación válida.
Conexión real con el proveedor.
Solicitud de inferencia ejecutada.
Respuesta válida del modelo.
Tiempo de respuesta registrado.
Sin errores críticos.
Una conexión no debe activarse únicamente por superar una prueba superficial.
```

---

## 2. LOS 10 OBJETIVOS PRINCIPALES (VERBATIM — auditoría y reconstrucción del cableado YAIWES)

```
1. Auditoría histórica y Job Test
   Utilizar el historial antiguo de Auditoría para recuperar los cableados anteriores.
   Comparar cableados históricos con los actuales.
   Ejecutar Job Test para identificar conexiones funcionales, rotas, duplicadas y desaparecidas.
   Utilizar el historial como referencia para recuperar conexiones válidas.

2. Centro único de distribución del cableado
   Crear un registro centralizado de todas las conexiones.
   Identificar cada servicio, archivo, consumidor, proveedor y endpoint.
   Centralizar la identificación y gestión del cableado.
   Evitar conexiones duplicadas y referencias dispersas.

3. Archivos guardianes
   Identificar todos los archivos guardianes.
   Comprobar si existe código que permita conectarlos a servicios que ya están funcionando.
   Conservar y conectar los que tengan utilidad real.
   Eliminar los que no tengan consumidores ni función demostrable.
   Unificar los criterios de conservación.

4. Chat YAIWES y OpenClaw
   Conservar el cableado funcional de la UI Chat YAIWES.
   Mantener su conexión y sincronización con OpenClaw.
   Preservar el mirror de OpenClaw.
   Evitar romper las conexiones actuales.

5. OpenClaw independiente
   Independizar OpenClaw del cómputo del Router.
   Permitir que OpenClaw llame directamente a proveedores o servidores.
   Crear un MVP mínimo de cómputo independiente.
   Garantizar funcionamiento de respaldo si el Router de GitHub cae o sufre modificaciones defectuosas.

6. System Prompt y motores
   Localizar el archivo raíz del System Prompt.
   Reconstruir su recorrido completo.
   Identificar todos los motores que lo reciben y ejecutan.
   Verificar su transmisión a modelos, agentes y herramientas.
   Comprobar persistencia durante Loop y reanudaciones.

7. Componentes y Skills
   Localizar y revisar los componentes existentes.
   Identificar sus dependencias y consumidores.
   Organizar los componentes y Skills según su función.
   Mantener como archivos raíz independientes:
   Chatbot. Loop. Cola. Watchdog. ECC. Skills.

8. Cableado del frontend
   Revisar el recorrido completo de la UI Chat YAIWES.
   Verificar frontend → backend → Harness → Router → modelos.
   Comprobar selectores, botones y estados.
   Preservar el funcionamiento de OpenClaw.

9. Cableado de agentes
   Identificar todos los agentes.
   Verificar su conexión con Harness DeepSeek.
   Revisar selectores y botones ON/OFF.
   Comprobar ejecución agéntica y herramientas.
   Verificar acceso a almacenamiento y memoria.

10. Modelos, API y servicios centrales
    Comprobar API NVIDIA.
    Comprobar modelos locales.
    Verificar respuesta real desde los selectores.
    Comprobar recepción del System Prompt.
    Verificar ejecución mediante los motores.
    Comprobar memoria y almacenamiento.
    Centralizar las comunicaciones mediante los plugins de Harness DeepSeek.
```

---

## 3. CRITERIO FINAL DE ACEPTACIÓN (VERBATIM)

```
Cada conexión debe demostrar:
1. Ubicación del código responsable.
2. Consumidor y proveedor identificados.
3. Cableado real.
4. Prueba funcional satisfactoria.
5. Evidencia de ejecución.

No declarar una conexión activa por estar configurada. Debe responder realmente.
```

---

## 4. POLÍTICA DE SERVIDORES (decisiones del owner, normativas)

### 4.1 Perfil de cómputo
- Todos los servidores son **de pago, 32 GB de RAM y CPU** (nunca `cpu-basic`; en HF: `cpu-upgrade` = 32 GB + 8 vCPU).
- **GitHub** es el único sitio donde vive el código. **HuggingFace** es **espejo + auto-pull**, y su contenido debe ser **lo mínimo posible**: solo lo que necesita para **servir de servidor y actualizar la UI** (aunque Vercel no lo haga).
- El trigger del **watchdog lo aplica Vercel al encender**: al encender, dispara el trigger que despierta el servidor.

### 4.2 Cola de servidores (servicio 1)
- Al **85 %** de ocupación → **salta al siguiente servidor**.
- **15 minutos sin actividad** → el servidor **duerme**.
- La UI de Chat YAIWES tiene, en su configuración, el **sistema de encendido y reinicio** y un **botón ON/OFF permanente** para mantenerlo activo y evitar caídas de trabajo.

### 4.3 Modelos locales (servicio 2)
- **1 modelo local por servidor**.
- Si una llamada falla → **salta al siguiente**; hasta **3 servidores en cola**.
- Al estar lleno → **espera 1 servidor por modelo**.
- **15 minutos** → **abandona el servidor y duerme**.

### 4.4 Umbral para `ACTIVE` (obligatorio, 7 condiciones, todas)
1. Autenticación válida. 2. Conexión real con el proveedor. 3. Solicitud de inferencia ejecutada.
4. Respuesta válida del modelo. 5. Tiempo de respuesta registrado. 6. Sin errores críticos.
7. **Una conexión NO se activa únicamente por superar una prueba superficial.**

---

## 5. PLAN TÉCNICO DE EJECUCIÓN (12 fases, del texto del owner)

> **Adaptación obligatoria al contrato del repo:** el texto original propone GitHub Actions; aquí
> **queda PROHIBIDO** (`INPUT_BLOCK` congelado: "No Github acción", "NO LFS GITHUB", "no usar vercel o
> huggueface sin autorización"). Los mismos tests se ejecutan **en local o como Job de HF
> `cpu-upgrade`**, nunca como Action. Los jobs pesados se trocean por el techo real de 1800 s.

| # | Fase | Entregable | Dónde vive |
|---|---|---|---|
| 1 | Recuperación forense del cableado histórico (git log/grep/show, AST, HTTP/MCP) | `audit/historical_connections.json` con ARCHIVO · COMMIT · FUNCIÓN · CONSUMIDOR · PROVEEDOR · ENDPOINT · ESTADO | `ops/historical_wiring_audit.py` (ampliar, no reemplazar) |
| 2 | Auditoría del cableado actual (Git + AST + HTTP + MCP + Plugins + Frontend + Runtime) | `audit/current_connections.json`, `dependency_graph.json`, `missing_connections.json`, `duplicate_connections.json`, `orphan_files.json` | `ops/` |
| 3 | Registro central (centro de distribución, una entrada por servicio con contrato y fallback) | `connections/wiring_registry.yaml` (+ `registry.yaml`, `topology.yaml`, `endpoints.yaml`, `healthchecks.yaml`) | `connections/` |
| 4 | Contratos del Harness DeepSeek (plugin: id, entry point, acciones, entrada, salida, auth, timeout, errores) | contratos en `handoff/contracts/` + plugin dispatcher | `handoff/`, `models harnes/` |
| 5 | System Prompt y motores (fuente raíz → ficha → motor → harness → adaptador → modelo; persistencia en Loop/reanudación) | recorrido trazado + identificador de prueba inyectado en test + SHA del prompt | `kernel/`, `docs/architecture/` |
| 6 | Chat YAIWES + OpenClaw (preservar UI; OpenClaw autónomo con `models.providers` y failover) | MVP de cómputo independiente del Router | `frontend/`, `integrations/` |
| 7 | Archivos guardianes y código huérfano (imports, entry points, HTTP, eventos, jobs, git, runtime) | inventario + propuesta de eliminación + commit reversible | `audit/`, `_quarantine/` |
| 8 | Frontend y agentes (selectores, ON/OFF, streaming, errores, PID, historial; agéntico vs herramientas) | pruebas del recorrido UI→backend→harness→router→modelo | `frontend/`, `tests/` |
| 9 | NVIDIA, modelos locales, memoria y storage (3 niveles: conexión, inferencia, integración; ACK de escritura) | evidencia de inferencia real + latencia | `tests/`, `connections/healthchecks.yaml` |
| 10 | Job Test integral (J01..J13, sin modificar código ni credenciales) | `audit/runtime_results.json` + `audit/final_report.json` | `ops/job_test.py` |
| 11 | Automatización de las pruebas (**sin GitHub Actions**: local o Job HF `cpu-upgrade`; 3 capas: static-audit, contract-tests con servicios simulados, integration-tests con secretos autorizados) | runner + informes | `ops/launch.sh`, `ops/launch_hf.py` |
| 12 | Cierre: README, bitácora, handoff, arquitectura, repo limpio (borrar no cableados, notas, pruebas y documentos no necesarios) | registro actualizado + criterios de cierre cumplidos | raíz + `docs/` + `kernel/` |

**Orden exacto:** auditoría histórica → auditoría actual → grafo AST → registro central → contratos
Harness → System Prompt → motores → Chat YAIWES → OpenClaw → Loop/ECC/Skills → agentes →
NVIDIA/locales → memoria/storage → guardianes → Job Test integral.

**Criterio de cierre:** 100 % de conexiones críticas inventariadas · 100 % con consumidor y
proveedor · ningún servicio `ACTIVE` sin sonda real · System Prompt trazable hasta el modelo ·
Chat YAIWES funcional · OpenClaw independiente · agentes conectados · NVIDIA y modelos locales
respondiendo · memoria y storage comprobados · ningún archivo eliminado sin análisis de
dependencias · jobs con evidencia y SHA.

---

## 6. LO QUE ESTÁ EXCLUIDO O PENDIENTE POR DECISIÓN DEL OWNER

- **Motor de búsqueda `research_prepass.py` (línea 89): NO autorizado.** El motor **permanece
  intacto** y el problema **sigue pendiente**. Solo se autoriza tras comprobar el error, el
  contexto de la línea y las pruebas de regresión, conservando el código anterior para revertir.
  El motor es **intocable** por contrato.
- **Claves/secretos: ninguna quedó expuesta y no se tocan.** Solo por entorno; nunca en ficheros,
  logs, Dataset, argv ni URLs.
- **Vercel y HuggingFace**: sin despliegue nuevo sin autorización expresa. HF queda como
  espejo/auto-pull mínimo; Vercel publica la UI y dispara el trigger del watchdog al encender.
- **GitHub Actions y LFS**: prohibidos.

---

## 7. CÓMO SE USA ESTE FICHERO

1. Es **INPUT BLOCK VERBATIM**: no se edita ni se reescribe; cualquier cambio del owner genera una
   versión nueva con su sha256.
2. La guía de organización (el adjunto) sigue siendo `AGENTS.md`, congelado, sha256
   `5c77e005…8943`.
3. Este fichero se **adjunta a la guía** desde `kernel/GUIDE_tail.md` (y por tanto en
   `kernel/GUIDE.md`, que se regenera con `ops/make_guide.py`).
4. La ejecución queda ordenada en `kernel/KERNEL.yaml` (`plan_cableado`) y su estado en el Dataset
   (`20261104-kernel01`).
