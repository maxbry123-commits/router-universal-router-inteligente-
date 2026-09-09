# 🧠🧩 ROUTER INTELIGENTE UNIVERSAL — ARQUITECTURA MAESTRA v6.0
**Base:** Router MAXBRY v5.5 (98 funciones · 5 paneles) + `RedUniversal` (repo `router-red`) + Ask Council de conectores 2026
**Objetivo de este documento:** dejar TODO listo para programar — módulos, contratos, catálogo de conectores y flujo de datos — sin ambigüedad.

---

## 0. Qué es y qué resuelve

El Router es el **único punto** por el que pasa cualquier mensaje entre: el usuario, los agentes/IA, y **cualquier sistema externo** (repos, bases de datos, dispositivos, servidores, otros agentes). No distingue el tipo de destino — todo entra a la red como un `Conector` con el mismo contrato (`enviar()` / `sondear()`). Añadir un sistema nuevo nunca toca el core: se declara un `Conector` nuevo y una `Ruta`.

```
USUARIO ⇄ [Panel 1 Chat] ⇄ [RedUniversal / RouterCore] ⇄ N Conectores ⇄ Destinos reales
                                    ↑
                        [Enchufe Gate] valida TODO antes de conectar
```

---

## 1. Principios de diseño (no negociables)

1. **Todo es un Conector.** MCP, API REST, GitHub, HuggingFace, una base de datos, un celular, una PC, un VPS, un servidor web, otro agente IA (A2A) — mismo `Protocol`: `async enviar(payload) -> dict`, `async sondear() -> bool`.
2. **Enchufe Gate obligatorio.** Ningún nodo se registra en la red sin pasar `validar_contrato_conexion()` (contrato v1.5: `kind`, `transport`, `sandbox`, `timeout_ms`, `rol` source/sink/transform).
3. **Namespaces + rutas declarativas.** Cada nodo vive en un namespace (`ai.llm.openrouter`, `repo.github.jarvis`, `db.postgres.main`, `device.smartphone.max`, `infra.vps.railway`, `agent.a2a.researcher`). Las rutas usan `fnmatch` (`ai.*`, `device.*`) — escala a miles de nodos sin tocar código.
4. **Secretos siempre por entorno**, nunca en código ni en el JSON del nodo.
5. **3 modos de envío:** `primero` (failover), `todos` (broadcast), `espejo` (paralelo, gana el más rápido).
6. **Salud por nodo, no global.** Circuit breaker individual: 5 fallos → `sano=False` → medio-abierto en el sondeo cada 30s.
7. **Trazabilidad total.** Todo mensaje lleva `task_id` + `trace_id`; todo evento pasa por el Audit Logger (hash-chain).

---

## 2. Capas de la arquitectura

| Capa | Qué es | Componentes |
|---|---|---|
| **UI** | Paneles donde el humano opera el Router | Panel 1 (chat+lista), Panel 2 (editor de ficha), Panel 3 (extras/monitor), Panel 4 (billetera de conectores), Panel 5 (config del agente IA) |
| **Core** | Cerebro que rutea, selecciona modelo y protege el sistema | `RouterCore` = R1–R10 + R2.5 (Selector por Especialidad) + `enchufe_gate` |
| **Red** | Grafo de nodos y reglas de ruteo | `RedUniversal`, `NodoRed`, `Ruta`, `Mensaje` |
| **Conectores** | Adaptadores concretos a cada mundo externo | Catálogo ampliado — sección 4 |
| **Destinos** | Sistemas reales | GitHub, HF, DBs, dispositivos, VPS, otros agentes, humanos (Telegram, etc.) |

---

## 3. Paneles (resumen operativo — detalle completo de las 98 funciones ya vive en `__router-funciones.md`, se mantiene sin cambios de fondo)

- **Panel 1 — Lista + Chat AI:** ver/editar/probar conexiones; chat interpreta lenguaje natural y arma fichas.
- **Panel 2 — Editor de ficha:** 4 secciones (Entrada / Anclaje / Salida / Otras), cada slot elige un conector del catálogo del Panel 4.
- **Panel 3 — Extras (12 sub-paneles):** Providers, Modelos, Marketplace, Mapa de red, Live Graph, Trazabilidad, Costes, Vault, Scheduler, Cola, Recovery/Circuit Breaker.
- **Panel 4 — Billetera de conectores:** pre-cargas credenciales UNA vez; alimenta selectores del Panel 2. **Se amplía en esta versión** con las categorías nuevas de la sección 4.
- **Panel 5 — Config del agente/IA del chat:** qué modelo controla el chat, system prompt, temperatura, etc. **Se extiende** con el Selector por Especialidad (sección 5): en vez de un único agente fijo, el chat puede delegar por categoría de tarea.

### Nuevo — Panel 4B: sub-pestañas por familia de conector
```
Panel 4
 ├─ 🤖 IA / LLM Gateways        (OpenRouter, Anthropic, OpenAI, xAI, Google...)
 ├─ 🔌 MCP                       (servidores MCP, MCP Apps, BYO-MCP, MCP Tunnels)
 ├─ 🤝 Agentes (A2A/ACP)         (agentes externos como pares, no como herramientas)
 ├─ 💻 Repos / Código            (GitHub, GitLab, HuggingFace Hub)
 ├─ 🗄️ Bases de datos            (Postgres, MySQL, MongoDB, Redis, Supabase)
 ├─ 📱 Dispositivos               (Smartphone, PC/Desktop)
 ├─ 🖥️ Infraestructura            (VPS, servidor web genérico, contenedores)
 ├─ 💬 Mensajería/Webhooks        (Telegram, Slack, Discord, email, webhook genérico)
 ├─ 💰 Pagos entre agentes        (AP2, x402)
 └─ 🧠 Memoria/Estado             (memoria interna del sistema)
```

---

## 4. Catálogo de Conectores — completo (existentes + nuevos)

Todos implementan `Conector` (`conector_id`, `async enviar(payload)->dict`, `async sondear()->bool`). Los que ya existen en `red/conectores.py` se listan como **[existente]**; los nuevos como **[nuevo]** con su diseño.

### 4.1 IA / LLM
- **[existente] `ConectorHTTP`** — base de casi todo gateway REST (OpenRouter, OpenAI, etc.)

### 4.2 MCP y agentes
- **[existente] `ConectorMCP`** — JSON-RPC sobre HTTP/SSE, `tools/list` y `tools/call`.
- **[nuevo] `ConectorMCPApp`** — extiende `ConectorMCP`; además de `enviar()`, expone `renderizar_ui(payload) -> dict` (HTML/JSON de UI embebida) para que el Panel 1 pinte tarjetas inline en el chat, igual que MCP Apps de Claude/ChatGPT.
- **[nuevo] `ConectorMCPTunnel`** — variante de `ConectorMCP` que en vez de `endpoint` público usa un túnel saliente hacia una red privada (VPS interno, LAN de casa); no requiere IP allowlisting ni puerto expuesto.
- **[nuevo] `ConectorA2A`** — implementa el ciclo de vida de tarea A2A de 8 estados (`submitted→working→input_required→auth_required→completed→failed→canceled→rejected`). Descubre al agente remoto leyendo su `AgentCard` en `/.well-known/agent-card.json` (skills, auth, endpoint). `enviar()` = crea tarea vía JSON-RPC 2.0 y hace polling/streaming del estado.
- **[nuevo] `ConectorACP`** — alternativa REST-nativa a A2A (IBM/AGNTCY), mismo `Protocol`, transporte HTTP simple sin JSON-RPC.
- **[nuevo] `SkillPackImporter`** — no es un conector de red sino un tipo de **artefacto portable**: lee `.skill`/`.md` (formato Claude Code Skills / Grok Skills, compatibles) y los registra como Anclaje disponible en el Panel 2, sección Anclaje.
- **[nuevo] `ConectorBotPersistente`** — para agentes tipo "Grok Bot": cómputo 24/7, no por sesión. `enviar()` encola una instrucción; el bot corre en su propio ciclo y notifica por webhook cuando tiene resultado o necesita aprobación.

### 4.3 Repos / código
- **[existente] `ConectorGitHub`** — commits, PRs, issues, contents, dispatch de Actions.
- **[nuevo] `ConectorHuggingFace`** — API de HF Hub: subir/bajar modelos y datasets, correr Inference Endpoints, gestionar Spaces.
  ```python
  @dataclass
  class ConectorHuggingFace:
      conector_id: str
      token_env: str = "HF_TOKEN"

      def _api(self) -> ConectorHTTP:
          return ConectorHTTP(self.conector_id, "https://huggingface.co/api",
                               headers_env={"Authorization": self.token_env})

      async def enviar(self, payload: dict) -> dict:
          accion = payload.get("_accion", "model_info")
          rutas = {
              "model_info": ("GET", f"/models/{payload.get('repo_id','')}"),
              "dataset_info": ("GET", f"/datasets/{payload.get('repo_id','')}"),
              "inference": ("POST", f"/models/{payload.get('repo_id','')}"),
              "list_spaces": ("GET", "/spaces"),
          }
          metodo, ruta = rutas.get(accion, rutas["model_info"])
          body = {k: v for k, v in payload.items() if not k.startswith("_")}
          return await self._api().enviar({"_ruta": ruta, "_metodo": metodo, **body})

      async def sondear(self) -> bool:
          return await self._api().sondear()
  ```
- **[nuevo] `ConectorGitLab`** — igual patrón que GitHub, distinto `base_url`/rutas.

### 4.4 Bases de datos
- **[nuevo] `ConectorDB`** — genérico para SQL (Postgres/MySQL) vía driver async (`asyncpg`/`aiomysql`); acciones: `query`, `execute`, `migrate`, `healthcheck`.
  ```python
  @dataclass
  class ConectorDB:
      conector_id: str
      dsn_env: str                      # nombre de env var con el connection string
      motor: str = "postgres"           # postgres|mysql|mongo|redis

      async def enviar(self, payload: dict) -> dict:
          accion = payload.get("_accion", "query")
          sql = payload.get("sql", "")
          params = payload.get("params", [])
          dsn = os.environ[self.dsn_env]
          # despacha según self.motor al driver correspondiente
          # (asyncpg.connect / aiomysql.connect / motor.AsyncIOMotorClient / redis.asyncio)
          ...
          return {"status": "DONE", "output": resultado}

      async def sondear(self) -> bool:
          try:
              # SELECT 1 / PING según motor
              return True
          except Exception:
              return False
  ```
- **[nuevo] `ConectorSupabase`** — capa fina sobre `ConectorHTTP` apuntando a la REST/Realtime API de Supabase (útil cuando ya usan Supabase como backend).

### 4.5 Dispositivos (Smartphones y PC)
- **[nuevo] `ConectorSmartphone`** — dos modos:
  - *Push*: envía notificación/acción vía **FCM** (Android) o **APNs** (iOS) — usado para aprobaciones, alertas, "el Router te pregunta algo".
  - *Agente local*: si el teléfono corre una app/daemon propio (o Termux+SSH), `enviar()` llama a un endpoint local expuesto por esa app (foto, ubicación, ejecutar automatización).
  ```python
  @dataclass
  class ConectorSmartphone:
      conector_id: str
      modo: str = "push"                # push|agente_local
      push_token_env: str = ""          # token FCM/APNs del dispositivo
      endpoint_local: str = ""          # si modo=agente_local

      async def enviar(self, payload: dict) -> dict:
          if self.modo == "push":
              # llama a FCM/APNs con push_token
              return {"status": "DONE", "canal": "push"}
          return await ConectorHTTP(self.conector_id, self.endpoint_local).enviar(payload)

      async def sondear(self) -> bool:
          return self.modo == "push" or await ConectorHTTP(
              self.conector_id, self.endpoint_local).sondear()
  ```
- **[nuevo] `ConectorPC`** — PC/Desktop como nodo: agente local (daemon propio, tipo el mismo patrón que Claude Code/Claude Cowork) que expone un endpoint HTTP local o se conecta por SSH para ejecutar comandos, leer/escribir archivos, o correr scripts. Reutiliza `ConectorHTTP` o un nuevo `ConectorSSH` (ver 4.6) según transporte.

### 4.6 Infraestructura (VPS / servidor web / contenedores)
- **[existente, se generaliza] `ConectorVPS`** — ya cubre Railway; se generaliza a cualquier VPS/servidor web con API propia (deploy, logs, restart).
- **[nuevo] `ConectorSSH`** — genérico para cualquier máquina (VPS, PC, servidor on-prem) accesible por SSH: `enviar()` ejecuta comando remoto vía `asyncssh`, `sondear()` hace `echo ok`.
  ```python
  @dataclass
  class ConectorSSH:
      conector_id: str
      host: str
      user_env: str
      key_env: str                      # ruta a la clave privada, vía env
      port: int = 22

      async def enviar(self, payload: dict) -> dict:
          cmd = payload.get("cmd", "")
          # asyncssh.connect(host, username=os.environ[user_env], client_keys=[os.environ[key_env]])
          # result = await conn.run(cmd)
          return {"status": "DONE", "output": "..."}

      async def sondear(self) -> bool:
          try:
              await self.enviar({"cmd": "echo ok"})
              return True
          except Exception:
              return False
  ```
- **[nuevo] `ConectorDocker`** — administra contenedores en un host (start/stop/logs/deploy) vía Docker API remoto o local socket.

### 4.7 Mensajería / Webhooks
- **[existente] `ConectorWebhook`** — Telegram y genérico HTTP saliente.
- **[nuevo] `ConectorSlack` / `ConectorDiscord` / `ConectorEmail`** — mismo patrón `ConectorHTTP` con rutas específicas de cada API.

### 4.8 Pagos entre agentes
- **[nuevo] `ConectorAP2` / `ConectorX402`** — para cuando el Router paga por un servicio de terceros (modelo de pago por uso vía marketplace). `enviar()` firma y envía la intención de pago; `sondear()` verifica estado de la pasarela. Se activa solo si el nodo destino declara `requiere_pago: true` en su contrato.

### 4.9 Memoria/Estado
- **[existente] `ConectorMemoria`** — estado interno del sistema, sin cambios.

---

## 5. Sistema de Asignación de IA por Especialidad (nuevo sub-módulo **R2.5**, extiende R2 Model Selector)

Objetivo: que el Router elija automáticamente **qué modelo/agente** conviene para cada tarea entrante, no solo "el chat usa siempre el mismo modelo".

```python
@dataclass
class EntradaRegistry:
    categoria: str          # "code_review" | "research_web" | "long_context_docs" | ...
    modelo_id: str
    score: float             # 0-1, qué tan bueno es en esa categoría
    costo_tier: str          # "bajo" | "medio" | "alto"
    latencia_tier: str       # "rapido" | "medio" | "lento"

class SpecialtyRegistry:
    """Tabla (categoria, modelo_id, score, costo, latencia). Re-scoreable por benchmark periódico."""
    def __init__(self) -> None:
        self.entradas: list[EntradaRegistry] = []

    def mejor_para(self, categoria: str, disponibles: set[str]) -> list[EntradaRegistry]:
        cands = [e for e in self.entradas if e.categoria == categoria and e.modelo_id in disponibles]
        return sorted(cands, key=lambda e: e.score, reverse=True)


class ClasificadorTarea:
    """90% código (keywords/embeddings baratos) + 10% LLM solo si es ambiguo."""
    def clasificar(self, texto: str) -> str:
        # 1. match rápido por keywords/regex contra categorías conocidas
        # 2. si no hay match claro, llamar a un modelo barato con prompt de clasificación
        ...


class SelectorEngine:
    """categoria + SpecialtyRegistry + AVAILABLE (Resource Brain) -> modelo elegido + fallback chain."""
    def __init__(self, registry: SpecialtyRegistry, health: "R4HealthCheck") -> None:
        self.registry = registry
        self.health = health

    def elegir(self, categoria: str) -> list[str]:
        disponibles = self.health.disponibles()
        candidatos = self.registry.mejor_para(categoria, disponibles)
        return [c.modelo_id for c in candidatos]  # orden = cadena de fallback
```

**Categorías iniciales:** código (generación/revisión/seguridad) · investigación web · escritura creativa · análisis de datos · visión/imagen · voz · matemática/lógica · traducción · documentos largos · orquestación multi-agente · negociación/consenso · legal/compliance.

**Flujo:** `Panel 5` deja de fijar "un agente fijo" y pasa a modo *auto*: `ClasificadorTarea` etiqueta el mensaje entrante → `SelectorEngine` devuelve la cadena de modelos → `R3 Cola` los intenta en orden (o en modo "comité": 3 compiten, gana el mejor voto).

---

## 6. Núcleo — Módulos R1–R10 (completos, con lo que faltaba resuelto)

| # | Módulo | Estado previo | Diseño final en esta versión |
|---|---|---|---|
| R1 | Auth & API Key Manager | Parcial | Vault AES-256 en reposo (Panel 3 `panelSecretVault`) + rotación automática con alerta 7 días antes de expirar + soporte BYOK por conector |
| R2 | Model Selector | Parcial | Reglas movidas a `capability.json` editable desde Panel 4, sin tocar código; se apoya en R2.5 |
| R2.5 | **Selector por Especialidad** | No existía | Sección 5 completa |
| R3 | Scheduler + Load Balancer | Parcial | Agrupación en lotes (`batch_size=20`, `overlap=5`) para ráfagas de 200+ tareas; cola persistente en disco/DB |
| R4 | Health Check | Parcial | Sondeo cada 30s (ya en `sondeo_loop`) + métricas p95/p99 de latencia + alerta de costo/hora en Panel 3 |
| R5 | **Retry** | No construido | Wrapper alrededor de `_enviar_a`: reintentos con backoff exponencial (`intentos=3`, `base_ms=500`), configurable por nodo vía `configReintentos(n)` |
| R6 | **Circuit Breaker** | No construido | Ya existe la mitad en `NodoRed.fallos`/`MAX_FALLOS_NODO`; falta el estado explícito `CLOSED→OPEN→HALF_OPEN` con ventana de tiempo, no solo contador |
| R7 | Provider Pool | Cubierto | `providers.yaml` + catálogo del Panel 4 |
| R8 | **Semantic Cache** | No construido | Cache de embeddings de la petición → si similitud > umbral con una respuesta reciente, la devuelve sin recalcular (Redis + vector similarity) |
| R9 | Audit Logger | Cubierto | `ledger` hash-chain, sin cambios |
| R10 | Monitoring | Parcial | Panel de métricas tipo OTel: traces distribuidos por `trace_id` a través de todos los conectores, no solo duración |
| + | **Cost Optimizer** | No construido | Corre después de R2.5: si dos modelos tienen score similar, prioriza el más barato; presupuesto por categoría (no solo por proveedor); proyección de costo antes de ejecutar tareas grandes |

### Circuit Breaker (R6) — diseño explícito
```python
class EstadoBreaker(str, Enum):
    CLOSED = "closed"        # todo normal
    OPEN = "open"             # cortado, no se intenta
    HALF_OPEN = "half_open"   # probando si ya sanó

@dataclass
class CircuitBreaker:
    umbral_fallos: int = 5
    ventana_s: int = 60
    enfriamiento_s: int = 30
    estado: EstadoBreaker = EstadoBreaker.CLOSED
    fallos_recientes: list[float] = field(default_factory=list)
    abierto_desde: float = 0.0

    def registrar_fallo(self, ahora: float) -> None:
        self.fallos_recientes = [t for t in self.fallos_recientes if ahora - t < self.ventana_s]
        self.fallos_recientes.append(ahora)
        if len(self.fallos_recientes) >= self.umbral_fallos:
            self.estado, self.abierto_desde = EstadoBreaker.OPEN, ahora

    def puede_intentar(self, ahora: float) -> bool:
        if self.estado == EstadoBreaker.CLOSED:
            return True
        if self.estado == EstadoBreaker.OPEN and ahora - self.abierto_desde > self.enfriamiento_s:
            self.estado = EstadoBreaker.HALF_OPEN
            return True
        return self.estado == EstadoBreaker.HALF_OPEN

    def registrar_exito(self) -> None:
        self.estado, self.fallos_recientes = EstadoBreaker.CLOSED, []
```

---

## 7. Flujo completo de una petición (end-to-end)

```
1. Usuario escribe en Panel 1 (o llega webhook/API externa)
2. ClasificadorTarea → categoría de la tarea
3. SelectorEngine (R2.5) → cadena de modelos/agentes candidatos, filtrados por R4 (solo AVAILABLE)
4. Cost Optimizer → reordena candidatos si hay empate de score priorizando costo
5. R8 Semantic Cache → ¿ya respondí algo muy parecido? si sí, devuelve y termina
6. RedUniversal.enviar(Mensaje) → _resolver() aplica Rutas (fnmatch origen/tipo) → lista de NodoRed sanos
7. Por cada intento: R5 Retry (backoff) + R6 Circuit Breaker (si el nodo está OPEN, salta al siguiente)
8. Conector.enviar(payload) → ejecuta contra el destino real (GitHub/HF/DB/dispositivo/VPS/agente A2A/...)
9. R9 Audit Logger registra el evento en el hash-chain
10. R10 Monitoring cierra el trace_id con latencia total
11. Resultado vuelve al Panel 1 (y opcionalmente notifica por Panel 3 / Telegram si escaló)
```

---

## 8. Estructura de repos/archivos para programar

```
router-core/
├── core/
│   ├── router_core.py          # orquesta R1-R10 + R2.5
│   ├── especialidad.py         # SpecialtyRegistry, ClasificadorTarea, SelectorEngine
│   ├── retry.py                # R5
│   ├── circuit_breaker.py      # R6
│   ├── semantic_cache.py       # R8
│   ├── cost_optimizer.py       # Cost Optimizer
│   └── capability.json         # reglas de R2, editable sin tocar código
├── red/
│   ├── enchufe_gate.py         # [existente]
│   ├── conectores.py           # [existente + todos los nuevos de la sección 4]
│   └── red_universal.py        # [existente]
├── vault/
│   └── secret_vault.py         # AES-256, rotación (R1)
├── api/
│   └── routes.py               # REST usado por los Paneles 1-5 (ver __router-funciones.md)
├── ws/
│   └── events.py                # connection.update, chat.token, cb.open, cost.update...
└── tests/
    ├── test_conectores_nuevos.py
    ├── test_especialidad.py
    ├── test_circuit_breaker.py
    └── test_flujo_end_to_end.py
```

---

## 9. Roadmap de implementación sugerido

1. **Fase 0 — Cerrar gaps del core:** R5 Retry, R6 Circuit Breaker completo, R8 Semantic Cache, Cost Optimizer. (Nada de esto rompe lo ya construido.)
2. **Fase 1 — Conectores nuevos de mayor valor inmediato:** `ConectorHuggingFace`, `ConectorDB`, `ConectorSSH` (cubre VPS/PC/servidor genérico de una), `ConectorA2A`.
3. **Fase 2 — Selector por Especialidad (R2.5):** `SpecialtyRegistry` con las 12 categorías iniciales + `ClasificadorTarea` básico por keywords.
4. **Fase 3 — Dispositivos:** `ConectorSmartphone` (empezar por modo push, es lo más simple) y `ConectorPC`.
5. **Fase 4 — MCP avanzado:** `ConectorMCPApp` (UI embebida en Panel 1), `ConectorMCPTunnel`, BYO-MCP en 1 clic desde Panel 4.
6. **Fase 5 — Multi-agente y pagos:** `ConectorACP`, `SkillPackImporter`, `ConectorBotPersistente`, `ConectorAP2`/`ConectorX402` (solo si ya hay un caso real de pago entre agentes).

---

## 10. Checklist de tests (agregar a los ya existentes)

```
test_conector_huggingface_model_info · test_conector_db_query_postgres
test_conector_ssh_ejecuta_comando · test_conector_a2a_ciclo_8_estados
test_conector_smartphone_push · test_circuit_breaker_open_a_half_open
test_semantic_cache_hit_y_miss · test_cost_optimizer_prioriza_barato_en_empate
test_selector_especialidad_elige_top_score · test_selector_especialidad_fallback_si_degraded
test_mcp_app_renderiza_ui · test_bot_persistente_encola_y_notifica
```

---

## Notas finales

- Todo conector nuevo sigue siendo **solo una dataclass** que cumple `Conector` — el core (`RedUniversal`, R1-R10) nunca se toca al agregar un sistema.
- El Enchufe Gate y los namespaces siguen siendo la única puerta de entrada: cualquier dispositivo, DB o agente que no pase el contrato v1.5 simplemente no se conecta.
- Este documento reemplaza como referencia de arquitectura a `GAP_01_ROUTER.md` (gaps ya incorporados aquí) y complementa sin sobreescribir `__router-funciones.md` (los 98 números de función siguen siendo válidos tal cual).
