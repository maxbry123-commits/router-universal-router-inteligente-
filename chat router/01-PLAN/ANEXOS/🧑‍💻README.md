# YAIWES — Rowboat + Ruflo + Hermes + OpenClaw

Esta versión NO usa Orca.

## Roles

```text
USUARIO.
  ↓
ROWBOAT
Director / contexto / entrada humana
  ↓
YAIWES CONTROL PLANE (MCP)
  ↓
HERMES PLAN A ←→ OPENCLAW PLAN B
       debate + crítica cruzada
             ↓
      PLAN DE CONSENSO
             ↓.
          SHERIFF
   reglas deterministas
             ↓
           RUFLO
 orquestación operativa de swarm
             ↓
 ┌────────┬────────┬────────┐
coder   tester   reviewer  otros agentes
 └────────┴────────┴────────┘
             ↓
    evidencia / receipts
             ↓
HERMES REVIEW ←→ OPENCLAW REVIEW
             ↓
           JUDGE
   reglas deterministas
       ↓       ↓       ↓
      PASS   REVISE   BLOCK
```

### Qué hace cada uno

**Rowboat**
- interfaz superior contigo;
- conserva contexto y memoria;
- llama al MCP de YAIWES;
- consulta estado y presenta resultados;
- no puede saltarse Sheriff/Judge.

**Ruflo**
- crea el swarm;
- enruta las tareas;
- crea agentes especializados;
- coordina el trabajo de la colmena;
- mantiene memoria/estado operativo;
- no declara el PASS final.

**Hermes + OpenClaw**
- ambos hacen un plan;
- ambos critican;
- ambos supervisan;
- ambos revisan evidencia;
- debaten cuando discrepan.

**Sheriff**
- código, no LLM;
- valida DAG, dependencias, scopes, criterios de aceptación y límites.

**Judge**
- código, no LLM;
- exige evidencia y verificaciones;
- si falta una prueba: FAIL_CLOSED.

## Instalar dependencias del Control Plane

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Probar sin Ruflo/Hermes/OpenClaw

```bash
export YAIWES_MODE=mock

yaiwes-hive run \
  --goal "Audita el proyecto, corrige el fallo y demuestra la solución" \
  --repo .
```

La prueba debe acabar en `PASS`.

## Preparar Ruflo real

La documentación actual de Ruflo usa:

```bash
npx ruflo@latest init
npx ruflo@latest doctor --fix
npx ruflo@latest daemon start
```

El Control Plane inicializa el swarm con:

```bash
npx ruflo@latest swarm init \
  --topology hierarchical \
  --max-agents 8 \
  --strategy specialized
```

Antes de crear una tarea consulta el router:

```bash
npx ruflo@latest hooks route --task "..."
```

Y registra tareas mediante:

```bash
npx ruflo@latest task create \
  --type implementation \
  --description "..."
```

## Modo real

```bash
export YAIWES_MODE=real
export RUFLO_CMD="npx ruflo@latest"
export HERMES_BIN=hermes
export OPENCLAW_BIN=openclaw
export OPENCLAW_AGENT_ID=guardian

yaiwes-hive run \
  --goal "Implementa X con pruebas verificables" \
  --repo /ruta/al/repo
```

El run queda normalmente en `DISPATCHED` mientras Ruflo/los agentes trabajan.

Cuando tengas recibos/evidencia:

```json
{
  "task-01": {
    "status": "PASS",
    "summary": "Implementado",
    "tests": ["pytest -q: PASS"],
    "artifacts": ["src/x.py", "tests/test_x.py"]
  }
}
```

Finaliza:

```bash
yaiwes-hive finalize \
  --run-id RUN_ID \
  --evidence evidence.json
```

## Conectar Rowboat

Arranca el MCP:

```bash
yaiwes-hive-mcp
```

URL local:

```text
http://127.0.0.1:8000/mcp
```

En Rowboat:
`Settings → MCP Servers`

Añade el servidor YAIWES.

Tools:

- `submit_goal`
- `get_run`
- `finalize_run`
- `validate_plan`
- `health`

Rowboat se convierte así en el Director humano/contextual y Ruflo en el orquestador operativo de la colmena.

## Regla de autoridad

```text
LLM propone.
Ruflo coordina.
Workers ejecutan.
Sheriff autoriza.
Judge cierra.
```

Ni Hermes, ni OpenClaw, ni Ruflo pueden declararse `PASS` a sí mismos.
