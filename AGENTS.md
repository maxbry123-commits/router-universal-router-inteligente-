Organización del repo objetivo recuperación de el cableado y hacer un registro y luego una reorganización de la raíz 

Procesó durante 18s

Sí. La solución correcta es utilizar dos Hugging Face Jobs independientes:

JOB 1 — Historical Wiring Audit: reconstruye el cableado anterior, descubre el actual y compara ambos.

JOB 2 — Root Structure Audit: analiza los archivos de la raíz y propone dónde debe organizarse cada uno.


La recuperación se realiza después de comparar las evidencias, no automáticamente.

Una precisión importante: Git permite reconstruir conexiones que estuvieron definidas en el código y las configuraciones. Para recuperar conexiones que funcionaban realmente en ejecución se necesitan también logs, trazas o registros históricos. 

GUÍA DE IMPLEMENTACIÓN

1. Plan de investigación y recuperación

PASO 1 📌 HISTORIAL DEL CABLEADO

El primer Job debe:

1. Clonar GitHub conservando el historial.


2. Examinar todas las ramas disponibles.


3. Identificar commits que modificaron conexiones.


4. Recuperar referencias antiguas a HTTP, MCP, APIs y endpoints.


5. Identificar archivos eliminados y renombrados.


6. Registrar las conexiones que existían en cada versión.


7. Detectar conexiones que desaparecieron.


8. Conservar evidencias de cada hallazgo.



Resultado:

audit/
└── historical/
    ├── commits.json
    ├── connections.jsonl
    ├── deleted_files.json
    ├── renamed_files.json
    └── historical_topology.json

PASO 2 📌 CABLEADO ACTUAL Y COMPARACIÓN

El mismo Job analiza el HEAD actual y compara:

Cableado histórico.

Cableado actual.

Endpoints anteriores.

Endpoints actuales.

Agentes y motores.

Conexiones HTTP.

Conexiones MCP.

Referencias a archivos.

Dependencias.


Clasificación:

Estado	Significado

PRESERVED	Existía y continúa.
REMOVED	Existía y desapareció.
MODIFIED	Fue modificada.
NEW	Conexión nueva.
BROKEN_CANDIDATE	Posible conexión rota.
UNKNOWN	No hay evidencia suficiente.


Resultado:

audit/
└── comparison/
    ├── current_connections.json
    ├── historical_connections.json
    ├── comparison.json
    └── recovery_candidates.json

PASO 3 📌 RECONOCER Y RECABLEAR

No recuperar conexiones basándose únicamente en nombres.

Para cada conexión desaparecida:

1. Localizar el commit donde funcionaba o estaba declarada.


2. Recuperar la implementación anterior.


3. Identificar el cliente y el servidor.


4. Comprobar endpoint, protocolo y autenticación.


5. Identificar los archivos que cambiaron.


6. Determinar qué componente sustituyó al anterior, si existe.


7. Elaborar una propuesta de recuperación.


8. Aplicar el cambio aprobado.


9. Ejecutar pruebas HTTP, MCP o internas.


10. Actualizar el registro central.



Si existe una prueba que identifica una versión funcional y otra defectuosa, utilizar git bisect para localizar el commit que introdujo el fallo. 

No restaurar commits completos indiscriminadamente: recuperar solamente los cambios necesarios.


---

2. JOB 1 — HISTORIAL Y COMPARACIÓN DEL CABLEADO

Guardar como:

ops/historical_wiring_audit.py

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import HfApi, upload_folder

REPO = os.environ["GH_REPO"]
BRANCH = os.getenv("GH_BRANCH", "main")
REPORT_REPO = os.environ["HF_REPORT_REPO"]

GH_TOKEN = os.environ["GH_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

MAX_COMMITS = int(os.getenv("MAX_COMMITS", "500"))

WORK = Path("/tmp/wiring-audit")
SRC = WORK / "source"
OUT = WORK / "output"

OUT.mkdir(parents=True, exist_ok=True)


def git(args, check=True):
    return subprocess.run(
        ["git"] + args,
        cwd=SRC,
        text=True,
        capture_output=True,
        check=check
    ).stdout


def redact(text):
    text = re.sub(
        r"(?i)(token|password|secret|api_key)"
        r"(\s*[:=]\s*)['\"]?[^'\"\s,]+",
        r"\1\2[REDACTED]",
        text
    )
    text = re.sub(
        r"(https?://)[^/@\s]+@",
        r"\1[REDACTED]@",
        text
    )
    return text[:400]


def save(name, data):
    (OUT / name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )


# 1. Clonar historial completo disponible
url = (
    f"https://x-access-token:{GH_TOKEN}"
    f"@github.com/{REPO}.git"
)

subprocess.run(
    ["git", "clone", "--no-single-branch", url, str(SRC)],
    check=True
)

git(["remote", "set-url", "origin",
     f"https://github.com/{REPO}.git"])

git(["fetch", "--all", "--tags", "--prune"])

head = git(["rev-parse", f"origin/{BRANCH}"]).strip()

# 2. Obtener commits de todas las referencias
commits = git([
    "rev-list", "--all", f"--max-count={MAX_COMMITS}"
]).splitlines()

historical = []
current = []

patterns = {
    "http": r"https?://|fetch\(|axios|requests\.|httpx|aiohttp",
    "mcp": r"\bMCP\b|tools/list|tools/call|streamable|stdio",
    "endpoints": r"BASE_URL|API_URL|ENDPOINT|SERVICE_URL|/api/",
    "agents": r"agent|orchestrator|specialist|handoff",
    "engines": r"hermes|deepseek|engine|provider",
    "imports": r"^\s*(import |from |require\()"
}

# 3. Examinar referencias en cada versión
for index, commit in enumerate(commits):

    metadata = git([
        "show", "-s",
        "--format=%H%x1f%ad%x1f%s",
        "--date=iso-strict", commit
    ]).strip().split("\x1f")

    record = {
        "commit": commit,
        "date": metadata[1] if len(metadata) > 1 else "",
        "message": metadata[2] if len(metadata) > 2 else "",
        "references": []
    }

    for category, pattern in patterns.items():

        result = subprocess.run(
            ["git", "grep", "-n", "-I", "-E",
             pattern, commit, "--",
             ".", ":!*.lock", ":!*.map"],
            cwd=SRC,
            text=True,
            capture_output=True
        )

        for line in result.stdout.splitlines():
            record["references"].append({
                "category": category,
                "reference": redact(line)
            })

    historical.append(record)

    if commit == head:
        current = record["references"]

# 4. Comparar referencias históricas y actuales
current_set = {
    x["category"] + "|" + x["reference"].split(":", 1)[-1]
    for x in current
}

historical_set = {}

for record in historical:
    for ref in record["references"]:
        key = (
            ref["category"] + "|" +
            ref["reference"].split(":", 1)[-1]
        )
        historical_set.setdefault(key, []).append(
            record["commit"]
        )

removed = [
    {
        "reference": key,
        "commits": commits
    }
    for key, commits in historical_set.items()
    if key not in current_set
]

# 5. Historial de archivos eliminados y renombrados
changes = git([
    "log", "--all", "--name-status",
    "--format=%H|%ad|%s", "--date=iso"
])

(OUT / "file_history.txt").write_text(changes)

# 6. Generar informes
save("historical_connections.json", historical)
save("current_connections.json", current)
save("removed_candidates.json", removed)

save("summary.json", {
    "repository": REPO,
    "branch": BRANCH,
    "head": head,
    "commits_examined": len(commits),
    "historical_references": len(historical_set),
    "current_references": len(current),
    "removed_candidates": len(removed),
    "generated_at": datetime.now(timezone.utc).isoformat()
})

# 7. Persistir en Hugging Face
api = HfApi(token=HF_TOKEN)

upload_folder(
    folder_path=str(OUT),
    repo_id=REPORT_REPO,
    repo_type="dataset",
    path_in_repo=f"wiring/{head}"
)

print("HISTORICAL WIRING AUDIT COMPLETED")
print("Commits:", len(commits))
print("Candidates:", len(removed))
print("HEAD:", head)

Importante: removed_candidates.json contiene candidatos, no conexiones rotas confirmadas. La comparación textual no reconstruye por sí sola llamadas dinámicas ni prueba que una conexión funcionara.


---

3. JOB 2 — AUDITORÍA Y ORGANIZACIÓN DE LA RAÍZ

Guardar como:

ops/root_structure_audit.py

Este Job no mueve archivos. Examina la raíz, identifica archivos dispersos y propone su ubicación.

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import upload_folder

REPO = os.environ["GH_REPO"]
BRANCH = os.getenv("GH_BRANCH", "main")
REPORT_REPO = os.environ["HF_REPORT_REPO"]

GH_TOKEN = os.environ["GH_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

WORK = Path("/tmp/root-audit")
SRC = WORK / "source"
OUT = WORK / "output"

OUT.mkdir(parents=True, exist_ok=True)

url = (
    f"https://x-access-token:{GH_TOKEN}"
    f"@github.com/{REPO}.git"
)

subprocess.run(
    ["git", "clone", "--branch", BRANCH,
     "--single-branch", url, str(SRC)],
    check=True
)

subprocess.run(
    ["git", "remote", "set-url", "origin",
     f"https://github.com/{REPO}.git"],
    cwd=SRC,
    check=True
)

KEEP = {
    "README.md",
    "AGENTS.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "vercel.json",
    ".gitignore",
    ".editorconfig",
    "Makefile"
}

RULES = {
    ".py": "backend/ o services/",
    ".js": "frontend/ o backend/",
    ".ts": "frontend/ o backend/",
    ".tsx": "frontend/",
    ".jsx": "frontend/",
    ".md": "docs/",
    ".yaml": "config/ o connections/",
    ".yml": "config/ o connections/",
    ".json": "config/ o schemas/",
    ".sh": "scripts/",
    ".sql": "database/",
    ".test.py": "tests/",
}

files = []
root_items = []

for path in SRC.iterdir():

    if path.name == ".git":
        continue

    root_items.append(path.name)

    if path.is_file():

        name = path.name
        suffix = path.suffix.lower()

        if name in KEEP:
            destination = "ROOT_KEEP"
            reason = "Archivo principal o configuración raíz"

        elif name.endswith(".test.py"):
            destination = "tests/"
            reason = "Archivo de prueba"

        elif suffix in RULES:
            destination = RULES[suffix]
            reason = "Clasificación por extensión; requiere validar contenido"

        else:
            destination = "MANUAL_REVIEW"
            reason = "No se puede determinar su responsabilidad"

        files.append({
            "file": name,
            "size": path.stat().st_size,
            "suggested_location": destination,
            "reason": reason
        })

    else:
        files.append({
            "file": path.name + "/",
            "type": "directory",
            "suggested_location": "EXISTING_DIRECTORY",
            "reason": "Revisar responsabilidad y contenido"
        })

report = {
    "repository": REPO,
    "branch": BRANCH,
    "commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=SRC, text=True
    ).strip(),
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "root": root_items,
    "inventory": files,
    "automatic_moves": False
}

(OUT / "root_structure.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False)
)

api_report = upload_folder(
    folder_path=str(OUT),
    repo_id=REPORT_REPO,
    repo_type="dataset",
    path_in_repo=f"root-audit/{report['commit']}",
    token=HF_TOKEN
)

print("ROOT AUDIT COMPLETED")
print("Files:", len(files))
print("Automatic moves: DISABLED")

Resultado:

root-audit/
└── root_structure.json

La clasificación por extensión es orientativa. Antes de mover un archivo hay que inspeccionar su contenido, sus imports y sus consumidores.


---

4. Configuración de los dos Jobs

Crear estos secretos:

GH_TOKEN
HF_TOKEN

Variables:

GH_REPO=USUARIO/REPOSITORIO
GH_BRANCH=main
HF_REPORT_REPO=USUARIO/REPOSITORIO-AUDITORIA

El repositorio de informes debe existir como Dataset privado de Hugging Face y el token debe tener permiso de escritura.

Ejecutar JOB 1

hf jobs run \
  --secrets GH_TOKEN,HF_TOKEN \
  --env GH_REPO=USUARIO/REPOSITORIO \
  --env GH_BRANCH=main \
  --env HF_REPORT_REPO=USUARIO/REPOSITORIO-AUDITORIA \
  python:3.12 bash -lc \
  "pip install huggingface_hub && git clone https://github.com/USUARIO/REPOSITORIO.git /tmp/code && cd /tmp/code && git fetch --all --tags && python ops/historical_wiring_audit.py"

Nota: si el repositorio es privado, el comando de clonación debe autenticarse con GH_TOKEN. El script también debe recibir ese secreto.

Ejecutar JOB 2

hf jobs run \
  --secrets GH_TOKEN,HF_TOKEN \
  --env GH_REPO=USUARIO/REPOSITORIO \
  --env GH_BRANCH=main \
  --env HF_REPORT_REPO=USUARIO/REPOSITORIO-AUDITORIA \
  python:3.12 bash -lc \
  "pip install huggingface_hub && git clone https://github.com/USUARIO/REPOSITORIO.git /tmp/code && cd /tmp/code && python ops/root_structure_audit.py"

Los Jobs tienen un sistema de archivos temporal. Los informes se suben al Dataset para conservarlos. Hugging Face documenta la ejecución, los secretos y la persistencia de resultados. 


---

5. Orden definitivo de ejecución

Orden	Trabajo	Resultado

1	JOB histórico	Cableado anterior.
2	JOB actual/comparación	Cableado presente y diferencias.
3	JOB raíz	Inventario y ubicación recomendada.
4	Análisis manual	Causas y conexiones rotas confirmadas.
5	Plan de recuperación	Archivos y conexiones que deben corregirse.
6	Reorganización aprobada	Archivos ubicados correctamente.
7	Recableado	HTTP, MCP, agentes, motores y sistemas restaurados.
8	Pruebas	Conectividad verificada.
9	Auditoría final	Registro actualizado.


Mi recomendación: ejecuta primero los tres análisis sin modificar el repositorio. Con esos resultados podrás distinguir qué conexiones se perdieron, cuáles siguen funcionando y qué archivos deben reorganizarse antes de comenzar la recuperación.

Guía mínima

1. Crear un Hugging Face Job.


2. Conectarlo al repositorio principal de GitHub.


3. Configurar los secretos.


4. Ejecutar el análisis histórico y actual.


5. Generar el registro de conexiones.


6. Sincronizar la réplica de Hugging Face.


7. Detener la sincronización si detecta divergencias.



Secretos necesarios:

GH_TOKEN: lectura del repositorio GitHub.

HF_TOKEN: escritura en Hugging Face.


Variables:

GH_REPO: usuario/repositorio.

GH_BRANCH: main.

HF_REPO: usuario/repositorio-replica.


Código del Job: connectivity_job.py

Este Job analiza el código, conserva evidencias históricas, genera un inventario y prepara la sincronización. No mueve archivos ni repara conexiones automáticamente.

import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import HfApi, upload_folder

GH_REPO = os.environ["GH_REPO"]
GH_BRANCH = os.getenv("GH_BRANCH", "main")
HF_REPO = os.environ["HF_REPO"]

GH_TOKEN = os.environ["GH_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

WORK = Path("/tmp/router-audit")
SOURCE = WORK / "source"
REPORT = WORK / "report"

WORK.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True
    ).stdout


# 1. Clonar GitHub conservando historial
url = f"https://x-access-token:{GH_TOKEN}@github.com/{GH_REPO}.git"

run([
    "git", "clone", "--no-single-branch",
    url, str(SOURCE)
])

run(["git", "fetch", "--all", "--tags"], cwd=SOURCE)

# 2. Estado actual
commit = run(
    ["git", "rev-parse", "HEAD"], cwd=SOURCE
).strip()

tree = run(
    ["git", "ls-files"], cwd=SOURCE
).splitlines()

# 3. Historial
history = run(
    ["git", "log", "--all", "--date=iso",
     "--name-status", "--format=%H|%ad|%s"],
    cwd=SOURCE
)

(REPORT / "git_history.txt").write_text(history)

# 4. Detectar referencias de conectividad
patterns = {
    "http": r"https?://[^\s\"'<>]+",
    "environment": r"\b[A-Z][A-Z0-9_]*(?:URL|URI|HOST|ENDPOINT|TOKEN)\b",
    "mcp": r"\bMCP\b|tools/list|tools/call|stdio|streamable",
    "imports": r"^\s*(?:import |from |require\()",
    "network": r"fetch\(|axios\.|requests\.|httpx\.|aiohttp"
}

findings = []

for path in SOURCE.rglob("*"):
    if not path.is_file():
        continue

    if any(x in path.parts for x in [
        ".git", "node_modules", ".venv", "__pycache__"
    ]):
        continue

    try:
        content = path.read_text(errors="ignore")
    except Exception:
        continue

    for category, pattern in patterns.items():
        for number, line in enumerate(content.splitlines(), 1):
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "file": str(path.relative_to(SOURCE)),
                    "line": number,
                    "category": category,
                    "reference": line.strip()[:500]
                })

# 5. Generar registro
registry = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "repository": GH_REPO,
    "branch": GH_BRANCH,
    "commit": commit,
    "files": tree,
    "findings": findings,
    "status": "discovered_not_runtime_verified"
}

(REPORT / "registry.json").write_text(
    json.dumps(registry, indent=2, ensure_ascii=False)
)

# 6. Inventario de ramas y commits
branches = run(
    ["git", "branch", "-a"], cwd=SOURCE
)

(REPORT / "branches.txt").write_text(branches)

# 7. Subir auditoría a Hugging Face
api = HfApi(token=HF_TOKEN)

upload_folder(
    folder_path=str(REPORT),
    repo_id=HF_REPO,
    repo_type="dataset",
    path_in_repo=f"audits/{commit}"
)

print("AUDITORÍA COMPLETADA")
print("Commit:", commit)
print("Archivos:", len(tree))
print("Referencias:", len(findings))
print("Informe:", f"audits/{commit}")

Configuración

Instalar dependencias:

pip install huggingface_hub

Ejecutar como Hugging Face Job:

hf jobs run python:3.12 \
  --secrets GH_TOKEN,HF_TOKEN \
  --env GH_REPO=USUARIO/REPOSITORIO \
  --env GH_BRANCH=main \
  --env HF_REPO=USUARIO/REPOSITORIO-AUDITORIA \
  python -c "import subprocess; subprocess.run(['pip','install','huggingface_hub'],check=True); exec(open('connectivity_job.py').read())"

Importante: este primer Job descubre y registra; todavía no mueve archivos ni sincroniza el código de la réplica. Primero hay que revisar el registro para evitar sobrescribir o romper conexiones existentes.

Esta guía está diseñada para colocarla en la raíz del repositorio como AGENTS.md. Su objetivo es que las IA y los agentes mantengan la organización, respeten la arquitectura, documenten el cableado y auditen las comunicaciones entre los componentes.

# REPOSITORY ENGINEERING GOVERNANCE
## Guía de organización, arquitectura, conectividad y mantenimiento

**Proyecto:** Router Inteligente Universal  
**Versión:** 1.0  
**Tipo:** SaaS modular con sistemas multiagente  
**Objetivo:** Mantener una arquitectura organizada, verificable, documentada y fácil de auditar.

---

# 1. OBJETIVO PRINCIPAL

Todo agente, asistente de programación o desarrollador que trabaje en este repositorio debe respetar la estructura, arquitectura, responsabilidades y conexiones existentes.

El repositorio debe mantenerse:

- Organizado por responsabilidades.
- Modular y escalable.
- Sin archivos dispersos.
- Sin duplicación innecesaria.
- Con separación entre frontend, backend, sistemas, agentes y motores.
- Con integraciones independientes.
- Con contratos de comunicación definidos.
- Con un registro centralizado de conectividad.
- Con documentación actualizada.
- Con pruebas de funcionamiento.

La prioridad es preservar la arquitectura existente y evitar modificaciones estructurales innecesarias.

# 2. ESTRUCTURA OFICIAL DEL REPOSITORIO

La estructura de referencia es:

```text
ROUTER-INTELIGENTE-UNIVERSAL/
│
├──  README/
│   └── README     
│ ├── ARQUITECTURA 1 /
│       ├── README 
│ ├── ARQUITECTURA 2 /
│      
├──  ARCHIVOS PROYECTOS/
│   └──  archivos adjuntos/
│       ├── bitácora  /
│       ├── stated JSON /
│       ├── Craxy wall  /
├── AGENTS.md 
├── AGENTES /
│   └── PLUGINS CONECCION.    AGENTES /
│       ├── Claude core /
│       ├── Codex / 
 │       ├── otros agentes /
├── frontend/
│   └── src/
│       ├── ui/
│       ├── components/
│       ├── pages/
│       └── features/
├── COMPONENTES OPEN 
│.    SOURE PARA INTEGRACIÓN/
├── backend/
│   ├── api/
│   ├── router/
│   ├── controllers/
│   └── services/
│
├── systems/
│   ├── system_1/
│   └── system_2/
│
├── agents/
│   ├── orchestrator/
│   ├── specialists/
│   └── registry/
│
├── engines/
│   ├── hermes/
│   └── adapters/
│
├── models harnes/
│   ├── deepseek/
│   └── providers/
│
├── integrations/
│   ├── vercel/
│   ├── huggingface/
│   ├── http/
│   └── mcp/
│
├── handoff/
│   ├── contracts/
│   ├── schemas/
│   └── workflows/
│
├── connections/
│   ├── registry.yaml
│   ├── topology.yaml
│   ├── endpoints.yaml
│   └── healthchecks.yaml
│
├── shared/
│   ├── schemas/
│   ├── contracts/
│   └── utilities/
│
├── config/
│
├── tests/
│
├── docs/
│   ├── architecture/
│   ├── connectivity/
│   └── operations/
│
└── scripts/

IMPORTANTE:

Esta estructura es una referencia organizativa.

No se deben crear todos los directorios automáticamente ni trasladar código sin analizar previamente el repositorio.

La estructura real debe respetar los componentes que ya existen.

3. RESPONSABILIDADES DE LOS DIRECTORIOS

frontend/

Contiene exclusivamente la interfaz de usuario.

Incluye:

UI.

Chat.

Paneles.

Componentes visuales.

Páginas.

Configuración visual.

Experiencia de usuario.


No debe contener motores de agentes ni lógica interna de ejecución.

backend/

Contiene la lógica de comunicación y coordinación del servidor.

Incluye:

API.

Router central.

Controladores.

Servicios.

Gestión de solicitudes.

Comunicación con sistemas y motores.


systems/

Contiene los sistemas principales del proyecto.

Cada sistema debe conservar:

Su responsabilidad.

Sus módulos.

Sus interfaces.

Sus dependencias.

Sus contratos de comunicación.


Los sistemas deben permanecer separados cuando tengan responsabilidades diferentes.

agents/

Contiene los agentes del proyecto.

Organización:

orchestrator/: coordinación principal.

specialists/: agentes especializados.

registry/: registro y configuración de agentes.


Todo agente debe tener una responsabilidad definida y una interfaz de comunicación conocida.

engines/

Contiene los motores de ejecución.

Hermes es el motor central de referencia.

Los adaptadores permiten conectar motores adicionales sin mezclar sus implementaciones.

Los motores ejecutan las instrucciones autorizadas; no deben modificar unilateralmente la arquitectura.

models/

Contiene las integraciones y configuraciones relacionadas con modelos de IA.

DeepSeek es el modelo central de referencia.

Los proveedores adicionales deben mantenerse desacoplados.

integrations/

Contiene las conexiones con servicios externos.

Incluye:

Vercel.

Hugging Face.

HTTP.

MCP.


Cada integración debe tener una responsabilidad y una interfaz identificables.

handoff/

Gestiona la transferencia de tareas entre sistemas, agentes y motores.

Incluye:

Contratos.

Esquemas.

Estados.

Entrega de resultados.

Recepción de tareas.

Transferencias entre agentes.


Toda transferencia debe permitir identificar origen, destino, tarea, estado y resultado.

connections/

Es el registro oficial del cableado del proyecto.

Ninguna conexión nueva debe considerarse documentada hasta registrarse aquí.

shared/

Contiene componentes reutilizables por varios módulos.

No debe utilizarse como depósito de archivos sin clasificación.

config/

Contiene configuraciones generales.

No guardar tokens, contraseñas ni credenciales directamente en archivos versionados.

tests/

Contiene las pruebas de los componentes y de sus comunicaciones.

docs/

Contiene la documentación técnica esencial.

scripts/

Contiene automatizaciones de mantenimiento, validación y despliegue.

4. REGLAS DE ORGANIZACIÓN DEL REPOSITORIO

Son obligatorias para todos los agentes.

1. No crear archivos directamente en la raíz sin autorización.


2. No crear directorios nuevos sin justificar su necesidad.


3. No duplicar carpetas que ya tengan una responsabilidad definida.


4. No colocar código fuente en directorios de documentación.


5. No mezclar frontend, backend y motores.


6. No mezclar implementaciones de proveedores diferentes.


7. No duplicar contratos ni esquemas.


8. No guardar archivos temporales en la raíz.


9. No guardar copias de seguridad dentro de los módulos.


10. No cambiar nombres o ubicaciones sin analizar las dependencias.


11. No eliminar archivos sin comprobar sus referencias.


12. No reorganizar el repositorio por preferencias personales.


13. No introducir dependencias circulares.


14. No modificar interfaces compartidas sin analizar sus consumidores.


15. Todo archivo nuevo debe tener una ubicación justificada.



REGLA CENTRAL:

La IA puede desarrollar dentro de la arquitectura autorizada, pero no puede rediseñar la organización del repositorio por iniciativa propia.

5. REGISTRO CENTRAL DE CONECTIVIDAD

El archivo:

connections/registry.yaml

Es el inventario oficial de las conexiones.

Cada conexión debe registrar:

Identificador único.

Nombre.

Origen.

Destino.

Protocolo.

Dirección.

Endpoint o referencia.

Estado.

Dependencias.

Verificación.

Observaciones.


Ejemplo:

connections:

  - id: CON-001
    name: frontend_to_backend
    source: frontend
    target: backend
    protocol: HTTP
    direction: outbound
    endpoint: API_BASE_URL
    status: active
    healthcheck: required

  - id: CON-002
    name: backend_to_hermes
    source: backend
    target: engines/hermes
    protocol: HTTP
    direction: outbound
    endpoint: HERMES_BASE_URL
    status: active
    healthcheck: required

  - id: CON-003
    name: hermes_to_deepseek
    source: engines/hermes
    target: models/deepseek
    protocol: API
    direction: outbound
    endpoint: DEEPSEEK_API_URL
    status: active
    healthcheck: required

  - id: CON-004
    name: backend_to_mcp
    source: backend
    target: integrations/mcp
    protocol: MCP
    direction: bidirectional
    endpoint: MCP_SERVER_URL
    status: active
    healthcheck: required

  - id: CON-005
    name: github_to_huggingface
    source: github
    target: integrations/huggingface
    protocol: HTTP
    direction: outbound
    endpoint: HF_REPOSITORY
    status: pending_audit
    healthcheck: required

  - id: CON-006
    name: frontend_to_vercel
    source: frontend
    target: integrations/vercel
    protocol: deployment
    direction: outbound
    endpoint: VERCEL_PROJECT
    status: active
    healthcheck: required

Los valores anteriores son ilustrativos. Cada agente debe verificar las conexiones reales antes de declararlas activas.

ESTADOS PERMITIDOS:

active

inactive

pending

pending_audit

failed

deprecated


No declarar una conexión activa sin evidencia de su funcionamiento.

6. TOPOLOGÍA DEL SISTEMA

El archivo:

connections/topology.yaml

Debe representar las relaciones entre los componentes.

Ejemplo:

topology:

  entrypoint:
    component: frontend

  backend:
    component: backend

  central_engine:
    component: engines/hermes

  central_model:
    component: models/deepseek

  systems:
    - system_1
    - system_2

  communication:
    - HTTP
    - MCP
    - API

  external_services:
    - vercel
    - huggingface

La topología debe actualizarse cuando cambie la arquitectura o el cableado.

7. REGISTRO DE ENDPOINTS

El archivo:

connections/endpoints.yaml

Debe identificar los endpoints utilizados.

Cada registro debe incluir:

Identificador.

Servicio propietario.

Ruta o variable de entorno.

Método HTTP cuando corresponda.

Protocolo.

Consumidores autorizados.

Estado.


No inventar endpoints.

No introducir URLs ficticias como si fueran funcionales.

Los secretos deben permanecer fuera del repositorio.

8. REGISTRO DE HEALTHCHECKS

El archivo:

connections/healthchecks.yaml

Debe establecer cómo verificar cada conexión.

Ejemplo:

healthchecks:

  - connection_id: CON-001
    check_type: http
    expected_status: 200
    required: true

  - connection_id: CON-002
    check_type: service
    required: true

  - connection_id: CON-004
    check_type: mcp
    required: true

Cada verificación debe adaptarse al protocolo real.

Un servicio no debe considerarse operativo únicamente porque su archivo de configuración exista.

9. REGLAS DE COMUNICACIÓN

Las comunicaciones entre módulos deben seguir estas reglas:

1. Utilizar interfaces explícitas.


2. Definir contratos de entrada y salida.


3. Validar los datos recibidos.


4. Identificar origen y destino.


5. Controlar errores y tiempos de espera.


6. Registrar las conexiones utilizadas.


7. Evitar llamadas directas no documentadas.


8. No introducir dependencias ocultas.


9. Respetar los protocolos HTTP y MCP establecidos.


10. Mantener compatibilidad con los consumidores existentes.



Toda conexión nueva debe registrarse antes de integrarse definitivamente.

10. REGLAS PARA HANDOFF

Toda transferencia de tareas debe identificar:

task_id

source

destination

agent_id

engine_id

input

output

status

timestamp

error


Estados recomendados:

pending

accepted

running

completed

failed

rejected


No considerar una tarea completada si no existe un resultado verificable.

Las transferencias deben utilizar los contratos definidos en:

handoff/contracts/

Y los esquemas definidos en:

handoff/schemas/

11. PROTOCOLO OBLIGATORIO ANTES DE MODIFICAR CÓDIGO

Antes de realizar cualquier cambio, el agente debe:

1. Identificar el archivo y módulo afectado.


2. Leer su código y configuración.


3. Identificar su responsabilidad.


4. Consultar sus dependencias.


5. Consultar connections/registry.yaml.


6. Identificar quién consume ese componente.


7. Revisar los contratos afectados.


8. Evaluar el impacto sobre los dos sistemas.


9. Identificar las pruebas necesarias.


10. Proponer el cambio antes de ejecutarlo cuando implique modificaciones arquitectónicas.



No modificar componentes basándose únicamente en sus nombres o ubicaciones.

12. PROTOCOLO DE MANTENIMIENTO

Después de cada modificación:

1. Verificar que el archivo esté en el directorio correcto.


2. Verificar que no se hayan creado archivos innecesarios.


3. Comprobar las dependencias.


4. Comprobar los contratos.


5. Actualizar el registro de conexiones si corresponde.


6. Ejecutar las pruebas pertinentes.


7. Verificar que no se hayan roto conexiones existentes.


8. Actualizar la documentación afectada.


9. Revisar los cambios realizados.


10. Entregar un informe de verificación.



13. AUDITORÍA DEL CABLEADO

La auditoría debe poder responder:

¿Qué componentes existen?

¿Qué componente llama a cuál?

¿Qué protocolo utiliza cada conexión?

¿Qué endpoints están configurados?

¿Qué agentes utilizan cada motor?

¿Qué sistemas dependen de Hermes?

¿Qué componentes utilizan DeepSeek?

¿Qué conexiones utilizan HTTP?

¿Qué conexiones utilizan MCP?

¿Qué comunicación existe con Vercel?

¿Qué comunicación existe con Hugging Face?

¿Qué conexiones están activas?

¿Qué conexiones están pendientes?

¿Qué conexiones fallaron?

¿Qué conexiones no están registradas?


La auditoría debe contrastar el registro documental con el código y las configuraciones reales.

No asumir que el registro está actualizado sin verificarlo.

14. PROTECCIÓN DE LOS DOS SISTEMAS

Los dos sistemas principales deben conservar sus límites funcionales.

Ningún agente puede:

Fusionarlos sin autorización.

Duplicar sus responsabilidades.

Crear dependencias circulares.

Modificar sus interfaces unilateralmente.

Introducir comunicaciones no registradas.

Cambiar su arquitectura sin análisis de impacto.


Las conexiones entre ambos deben estar documentadas y verificadas.

15. GITHUB, VERCEL Y HUGGING FACE

Mantener claramente diferenciadas sus responsabilidades.

GITHUB:

Código fuente principal.

Versionado.

Historial de cambios.

Workflows.

Control de versiones.


VERCEL:

Despliegue de frontend.

Integración continua del frontend.

Publicación de la interfaz.


HUGGING FACE:

Servidor réplica del código cuando corresponda.

Recursos externos.

Modelos, datasets y adaptadores cuando estén contemplados.

Procesamiento y servicios alojados.


La sincronización entre GitHub y Hugging Face debe tener un procedimiento identificable.

No asumir que ambos repositorios contienen exactamente la misma versión.

Registrar:

Repositorio de origen.

Repositorio de destino.

Rama.

Método de sincronización.

Última versión sincronizada.

Resultado de la verificación.


16. CONTROL DE CAMBIOS ARQUITECTÓNICOS

Se consideran cambios arquitectónicos:

Crear un módulo principal.

Eliminar un módulo principal.

Mover directorios.

Cambiar el motor central.

Modificar la comunicación entre sistemas.

Cambiar contratos compartidos.

Incorporar un protocolo nuevo.

Modificar el cableado principal.


Estos cambios requieren:

1. Análisis de impacto.


2. Justificación técnica.


3. Identificación de dependencias.


4. Propuesta de modificación.


5. Aprobación antes de ejecutarlos.


6. Actualización de documentación y registros.


7. Verificación posterior.



17. FORMATO OBLIGATORIO DE ENTREGA DE LOS AGENTES

Al terminar una tarea de programación, entregar:

A. Archivos modificados

Lista de archivos creados, modificados o eliminados.

B. Ubicación

Justificación de la ubicación de cada archivo nuevo.

C. Arquitectura

Explicación de los módulos afectados.

D. Conectividad

Conexiones nuevas, modificadas o eliminadas.

E. Dependencias

Dependencias nuevas o modificadas.

F. Handoff

Transferencias entre agentes o sistemas realizadas.

G. Pruebas

Pruebas ejecutadas y sus resultados.

H. Auditoría

Confirmación de que se respetó la estructura.

I. Pendientes

Problemas no resueltos o verificaciones pendientes.

No declarar éxito si existen verificaciones obligatorias sin ejecutar.

18. REGLA FINAL

La arquitectura, los contratos y el registro de conectividad son la referencia oficial del proyecto.

Ningún agente puede inventar estructuras, conexiones, endpoints, dependencias o capacidades.

Cuando encuentre una inconsistencia:

1. Detener la modificación afectada.


2. Identificar la inconsistencia.


3. Documentar la evidencia.


4. Proponer una solución.


5. Esperar autorización cuando implique cambiar la arquitectura.



PRINCIPIO FUNDAMENTAL:

MANTENER EL ORDEN. PRESERVAR LA ARQUITECTURA. DOCUMENTAR EL CABLEADO. VERIFICAR LAS COMUNICACIONES. CONTROLAR LOS CAMBIOS. EVITAR DUPLICACIONES. NO INVENTAR COMPONENTES. NO MODIFICAR SIN COMPRENDER.

**Ubicación recomendada:** `AGENTS.md` en la raíz del repositorio. Esta guía establece las reglas de trabajo; el registro real de conexiones debe mantenerse en `connections/registry.yaml` y actualizarse conforme se verifique el cableado existente.



