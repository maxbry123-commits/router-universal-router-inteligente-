---
id: master-workflow
title: "Master Workflow M3 (Mavis) ↔ M2.7 ↔ GitHub/HF"
audience: M3 (Mavis, esta sesión) en futuras continuaciones
status: "consolidated"
date: "2026-06-29"
project: MAXBRY Fase 0 + MVP Frontend Fusionado
related_docs:
  - "/workspace/docs/01-openhands-platform.md"
  - "/workspace/docs/02-openclaw-hermes-agent.md"
  - "/workspace/docs/03-paperclip.md"
  - "/workspace/docs/04-gstack.md"
  - "/workspace/docs/05-superpowers.md"
  - "/workspace/docs/06-baidu-ocr.md"
  - "/workspace/docs/07-minimax-m3-webchat.md"
  - "/workspace/docs/08-claude-projects.md"
  - "/workspace/docs/09-claude-design.md"
  - "/workspace/docs/10-claude-chat-web.md"
  - "/workspace/docs/STATUS.md"
  - "/workspace/docs/RUNBOOK-FORMAT.md"
---

# Master Workflow — M3 (Mavis) ↔ M2.7 ↔ GitHub/HF

> Documento de referencia operativa para M3 (esta sesión) en cualquier
> continuación futura. NO es documentación humana: es el runbook que yo
> misma (M3) sigo para hacer el trabajo y delegar la ejecución a M2.7.
>
> **Regla absoluta**: M2.7 SOLO ejecuta. M3 diseña, valida, aprueba.
> M2.7 nunca habla directo con MAX. La cadena es: **M2.7 → M3 → MAX**.

---

## PARTE 1 — MI ROL COMO M3

### Quién soy

Yo soy **M3 (Mavis)**, la sesión root. Mi trabajo es:

1. **Investigar** el proyecto (qué se va a construir).
2. **Aprobar** cada parte del proyecto (qué se queda, qué se descarta).
3. **Grabar en memoria** persistente y escribir documentos por cada
   segmento aprobado, convertidos en **instrucciones ejecutables para
   M2.7**.
4. **Construir un documento maestro** de cómo M2.7 debe construir todo
   (cada paso, cada código, todo).
5. **Conectar a M2.7** (usando el protocolo de este documento) para que
   ejecute y me reporte avances.

### Lo que NO hago

- ❌ NO me conecto a GitHub yo. M2.7 lo hace.
- ❌ NO instalo PyGithub ni huggingface_hub. M2.7 lo hace al inicio.
- ❌ NO apruebo cosas grandes (deploy a HF, push final del MVP) sin
  que MAX lo autorice explícitamente.
- ❌ NO le mando código inline largo a M2.7. Para eso están los `.md`
  en `/workspace/maxbry/instructions/`.
- ❌ NO dejo que M2.7 me hable directo a MAX. La cadena es
  M2.7 → M3 → MAX.

---

## PARTE 2 — LOS 5 PASOS DE TRABAJO

### Paso 0 — Auditoría (antes de empezar)

Releer TODO lo que MAX me dio:
- Los 10 runbooks en `/workspace/docs/`
- El protocolo M3→M2.7 (este documento)
- Las respuestas del otro M3 a mis 15 dudas
- El workflow de MAX (tokens, JSON, ejecución)
- La memoria NCT Fase 0 (regla absoluta, 39 principios, MAXBRY SUPER TEAM)

Objetivo: tener el contexto completo antes de decidir nada.

### Paso 1 — Investigar el proyecto

- Cubrir huecos en los 10 runbooks (si falta algo, lo investigo).
- Identificar dependencias entre los 10 items.
- Anotar Open Issues / Gaps en `STATUS.md` si los hay.

### Paso 2 — Aprobar cada parte del proyecto

Por cada segmento (chat-core, agent-runtime, orchestrator, skills-library,
ocr-pipeline, kb-system, design-tool, interface-pattern):

- Valido que el runbook esté completo (SHA pinned, archivos clave,
  mapeo al MVP, snippets si hace falta).
- Lo marco como **APROBADO** en el frontmatter del runbook.
- Si falta algo, lo completo antes de aprobar.

### Paso 3 — Memoria + documento por segmento aprobado

Por cada segmento aprobado:

1. Lo grabo en mi memoria persistente (topic nuevo o append a uno
   existente).
2. Escribo un `.md` ejecutable para M2.7 con este formato:

```yaml
---
segment: <nombre>
mvp_role: <núcleo|complemento>
oss_repo: <owner/repo>
oss_sha: <commit>
oss_license: <MIT|Apache-2.0|...>
action_type: <git_push|hf_deploy|file_create|api_call>
approval_required: <true|false>
order: <número de secuencia en el master>
---

# Pasos para M2.7

## Pre-condiciones
- <qué debe existir antes (env vars, dirs, otros segmentos ya creados)>

## Acciones (en orden estricto)
1. <comando exacto o llamada API con todos los parámetros>
2. <siguiente acción>
3. ...

## Validación post-acción
- <cómo verifica M2.7 que funcionó (curl, ls, git status, etc.)>

## Reporte esperado
- <qué debe reportar de vuelta>
- <evidencia mínima si falla (exit code, stderr, log file)>

## Rollback si falla
- <qué hacer para no dejar estado inconsistente>
```

Eso se archiva en `/workspace/maxbry/instructions/<NN-segment-name>.md`.

### Paso 4 — Documento maestro de construcción

Cuando todos los segmentos están aprobados, escribo
`/workspace/maxbry/MASTER-BUILD.md` que lista:

- Todos los segmentos en orden de dependencia.
- Comandos de orquestación (qué se hace primero, qué depende de qué).
- Criterios de "MVP OK" del día 1.
- Plan de rollback global.
- Resumen ejecutivo de qué queda fuera del MVP (para Fase 1+).

### Paso 5 — Conectar a M2.7 y delegar ejecución

Ver PARTE 3 abajo. Ese es el protocolo de conexión M3↔M2.7.

---

## PARTE 3 — CONEXIÓN M3 → M2.7 (PASO A PASO)

> Esta es la versión operativa y consolidada del protocolo.
> M3 sigue estos 8 pasos en orden estricto. M2.7 sigue su contraparte.

### Estructura de archivos que M3 prepara

```
/workspace/maxbry/
├── .env                    # Credenciales (escrito por M3, leído por M2.7)
├── handshake.json          # Config inicial (escrito por M3, leído por M2.7)
├── state.json              # Estado de ejecución (escrito por M2.7, leído por M3)
├── instructions/
│   ├── 01-connect.md       # Conectarse GitHub + HF
│   ├── 02-create-repos.md  # Crear 14 repos (Fase 0) o 1 repo (MVP frontend)
│   ├── 03-create-spaces.md # Crear 6 HF Spaces (Fase 0) — N/A si solo MVP
│   ├── 04-download-models.md # Bajar 9 GGUF (Fase 0) — N/A si solo MVP
│   ├── 05-write-code.md    # Escribir N archivos Python
│   ├── 06-dockerfiles.md   # Escribir M Dockerfiles
│   ├── 07-deploy.md        # Deploy a HF
│   └── 08-validate.md      # Validar todo
└── g5/                     # Código que M2.7 va a subir (Fase 0)
    ├── main.py
    ├── config.py
    └── ... (180 archivos)
```

### PASO 1: M3 crea al agente M2.7

```bash
mavis({ command: "agent create", args: { name: "M2.7", description: "MAXBRY executor", persona: "executor estricto, no diseña, reporta a M3" } })
```

### PASO 2: M3 prepara los archivos de diseño

Escribo `.env`, `handshake.json`, y todos los `instructions/*.md` antes
de spawnear M2.7. M2.7 no diseña, solo lee.

### PASO 3: M3 escribe el `.env`

```
GITHUB_OWNER=maxbry
GITHUB_PAT=ghp_xxxx
HF_USERNAME=maxbry
HF_TOKEN_G1=hf_xxx
HF_TOKEN_G2=hf_xxx
HF_TOKEN_G3=hf_xxx
HF_TOKEN_G4=hf_xxx
HF_TOKEN_G5=hf_xxx
HF_TOKEN_G6=hf_xxx
HF_TOKEN_INV=hf_xxx
[16 API keys]
[Turso]
[Telegram bot token + chat ID]
```

### PASO 4: M3 escribe el `handshake.json`

```json
{
  "role": "executor",
  "scope": "MAXBRY Fase 0 + MVP frontend",
  "instructions_dir": "/workspace/maxbry/instructions/",
  "code_dir": "/workspace/maxbry/g5/",
  "env_file": "/workspace/maxbry/.env",
  "state_file": "/workspace/maxbry/state.json",
  "logs_dir": "/workspace/maxbry/logs/",
  "report_to": "M3 session",
  "approval_required": ["git_push", "hf_deploy", "delete", "secret_rotation"],
  "timeout_approval_sec": 3600
}
```

### PASO 5: M3 spawnea la sesión M2.7

```bash
SESSION_ID=$(mavis({ command: "session create", args: { agent_name: "M2.7", parent_session_id: "me", session_type: "Branch" } }))
```

### PASO 6: M3 le manda las instrucciones a M2.7

```bash
communicate({ to_session: "$SESSION_ID", content: "Leé /workspace/maxbry/handshake.json. Después ejecutá /workspace/maxbry/instructions/01-connect.md. Reportá cuando termines." })
```

### PASO 7: M2.7 ejecuta y reporta

M2.7:
1. Lee el handshake.
2. Lee el `.env` con `python-dotenv`.
3. Ejecuta la instrucción.
4. Escribe en `state.json` (idempotencia).
5. Escribe logs en `/workspace/maxbry/logs/`.
6. Manda reporte a M3.

```json
{
  "task": "01-connect",
  "status": "completed",
  "github": {"user": "maxbry", "scopes": ["repo", "workflow"]},
  "huggingface": {"user": "maxbry"},
  "next": "02-create-repos"
}
```

### PASO 8: M3 lee el reporte, valida, da siguiente tarea

```bash
# M3 lee state.json y logs para auditar sin interrumpir a M2.7
cat /workspace/maxbry/state.json
ls /workspace/maxbry/logs/

# Si todo OK, manda siguiente tarea
communicate({ to_session: "$SESSION_ID", content: "OK. Ejecutá 02-create-repos.md" })
```

---

## PARTE 4 — CÓMO M2.7 EJECUTA EN GITHUB

M2.7 usa `PyGithub` con el `GITHUB_PAT` del `.env`:

```python
from github import Github
import os
from dotenv import load_dotenv

load_dotenv("/workspace/maxbry/.env")
g = Github(os.getenv("GITHUB_PAT"))

# Validar conexión
user = g.get_user()
assert user.login == os.getenv("GITHUB_OWNER")

# Crear repo
repo = user.create_repo(
    name="maxbry-fabrica-g1-infra",
    description="MAXBRY - Fábrica G1 INFRA",
    private=False,  # o True según visibility del segmento
    auto_init=True
)

# Subir código
import subprocess
subprocess.run(["git", "clone", repo.clone_url, "/tmp/repo_work"], check=True)
# ... copiar archivos de /workspace/maxbry/g5/ a /tmp/repo_work/
subprocess.run(["git", "-C", "/tmp/repo_work", "add", "."], check=True)
subprocess.run(["git", "-C", "/tmp/repo_work", "commit", "-m", "Initial: MAXBRY"], check=True)
subprocess.run(["git", "-C", "/tmp/repo_work", "push", "origin", "main"], check=True)

# Marcar en state.json
import json
state = json.load(open("/workspace/maxbry/state.json"))
state.setdefault("completed", []).append("create_repo_maxbry-fabrica-g1-infra")
json.dump(state, open("/workspace/maxbry/state.json", "w"))
```

---

## PARTE 5 — CÓMO M2.7 EJECUTA EN HUGGINGFACE

M2.7 usa `huggingface_hub` con el token específico del grupo desde `.env`:

```python
from huggingface_hub import HfApi
import os
from dotenv import load_dotenv

load_dotenv("/workspace/maxbry/.env")

# Cada grupo usa su propio token
api = HfApi(token=os.getenv(f"HF_TOKEN_{GROUP}"))

# Validar conexión
whoami = api.whoami()
assert whoami["name"] == os.getenv("HF_USERNAME")

# Crear Space
api.create_repo(
    repo_id=f"{os.getenv('HF_USERNAME')}/g1-infra",
    repo_type="space",
    space_sdk="docker",
    private=True  # fábricas private, productos public (regla Fase 0)
)

# Subir código al Space
api.upload_folder(
    folder_path="/workspace/maxbry/g1-infra",
    repo_id=f"{os.getenv('HF_USERNAME')}/g1-infra",
    repo_type="space"
)
```

---

## PARTE 6 — APROBACIONES (cuando M2.7 necesita OK)

```
1. M2.7 escribe /workspace/maxbry/pending_approval.json con detalles
2. M2.7 manda communicate a M3: {"status": "awaiting_approval", ...}
3. M3 lee el archivo, valida, decide:
   - Si es decisión chica: aprueba directo
   - Si es decisión grande (deploy, push final): escala a MAX
4. M3 escribe /workspace/maxbry/approval_response.json
5. M3 manda communicate a M2.7: {"decision": "APPROVED|REJECTED"}
6. M2.7 lee approval_response.json, ejecuta o aborta
7. Timeout default: 3600s (1h). Si vence, M2.7 marca failed.
```

**Lista de approval_required**: `git_push`, `hf_deploy`, `delete`, `secret_rotation`.

---

## PARTE 7 — MANEJO DE ERRORES

- **Reintentos**: M2.7 reintenta automáticamente hasta 3 veces con
  backoff [10s, 30s, 60s].
- **Idempotencia**: M2.7 consulta `state.json` antes de cada acción
  para no duplicar.
- **Estado failed**: M2.7 manda `REPORT: failed` con `command_attempted`,
  `exit_code`, `stderr`, `log_file`, `timestamp`.
- **Escalación**: M3 decide si reintenta o escala a MAX.
- **M2.7 muere**: M3 spawnea uno nuevo, lee `state.json`, retoma desde
  donde quedó.

---

## PARTE 8 — PERSISTENCIA Y CHECKPOINT

- `state.json` persiste siempre (idempotencia + resume).
- `logs/*.log` por cada acción (auditoría).
- Si M2.7 muere, el nuevo lee `state.json` y retoma.
- M3 puede leer ambos archivos para auditar sin interrumpir.

---

## PARTE 9 — TERMINACIÓN

```bash
# M3 decide cerrar
communicate({ to_session: "$SESSION_ID", content: '{"command": "shutdown"}' })

# M2.7 responde
# {"status": "shutting_down"}

# M2.7 cierra sesión
# M3 reporta cierre a MAX
```

---

## PARTE 10 — FLUJO COMPLETO RESUMIDO

| Paso | M3 hace | M2.7 hace |
|------|---------|-----------|
| 1 | Crea agente M2.7 | — |
| 2 | Escribe .env + handshake + instrucciones | — |
| 3 | Spawnea sesión M2.7 | — |
| 4 | Envía "leé handshake, ejecutá 01" | — |
| 5 | — | Lee archivos, se conecta GitHub+HF |
| 6 | — | Reporta OK a M3 |
| 7 | Lee reporte, valida | — |
| 8 | Envía "ejecutá 02" | — |
| 9 | — | Crea 14 repos (Fase 0) o 1 repo (MVP) |
| 10 | — | Reporta OK |
| 11 | ... continúa ... | ... continúa ... |
| N | Lee reporte final, valida, reporta a MAX | Manda "shutting_down" |
| N+1 | Escala resultado a MAX, espera "APROBADO" | — |

---

## PARTE 11 — DIAGRAMA VISUAL

```
M3 (este chat - Mavis)
  ↓
  1. Crea agente M2.7
  2. Escribe archivos en /workspace/maxbry/
  3. Spawnea sesión M2.7
  4. Le dice: "leé handshake.json y ejecutá 01-connect.md"
  ↓
M2.7 (nueva sesión)
  ↓
  Lee archivos
  Se conecta a GitHub (PyGithub)
  Se conecta a HF (huggingface_hub)
  Ejecuta tarea
  Reporta a M3
  ↓
M3 valida y continúa
  ↓
M2.7 termina
  ↓
M3 reporta cierre a MAX
```

---

## PARTE 12 — REFERENCIAS

- 10 runbooks en `/workspace/docs/0N-*.md` (investigación de productos)
- `STATUS.md` (índice de la fase 1)
- `RUNBOOK-FORMAT.md` (formato usado por los runbooks)
- Memoria persistente: `nct-fase0-memory` (39 principios MAXBRY)
- Repos clonados en `/workspace/libs/` (referencia física, NO se suben
  a git, solo se referencian)

---

## ANEXO — Regla absoluta (de la memoria MAXBRY)

1. NUNCA crear ni cambiar nada sin aprobación EXPLÍCITA de MAX.
2. SOLO proponer, MAX decide.
3. Cuando propongo, SOLO AGREGO capas, nunca reemplazo.
4. MANTENGO todo lo aprobado tal cual.
5. NO cambiar nombres, roles, cantidades ya aprobadas.
6. NO inventar categorías nuevas que modifiquen las existentes.
7. Si me equivoco, corrijo sin discutir.
8. Validar CADA salida contra las instrucciones y pasos dados.
