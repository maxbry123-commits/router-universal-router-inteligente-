"""Descarga SOLO textos SKILL.md de ECC bajo solicitud explícita del usuario.

No importa scripts ni instala extensiones del repositorio. Ref fijable para
reproducibilidad. Requiere internet en el entorno del usuario al ejecutar.
"""
from __future__ import annotations
import io
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path

# Descargar/compilar automáticamente SOLO skills técnicas del flujo de ingeniería.
# Los documentos de otro dominio no se incluyen en la distribución compilada.
CODING_SKILLS = set("""
accessibility agent-architecture-audit agent-eval agent-harness-construction
agent-introspection-debugging agent-runtime-gateway-smoke-test
agent-security-hardening agent-self-evaluation agentic-engineering
ai-first-engineering ai-regression-testing api-connector-builder api-design
architecture-decision-records automation-audit-ops autonomous-agent-harness
autonomous-loops backend-patterns benchmark benchmark-methodology
benchmark-optimization-loop blueprint browser-qa brownfield-retrospective
bun-runtime change-impact click-path-audit code-tour codebase-onboarding
codehealth-mcp coding-standards config-gc configure-ecc
content-hash-cache-pattern context-and-decisions context-budget
continuous-agent-loop continuous-learning continuous-learning-v2
contract-first conventional-commit-review cost-aware-llm-pipeline
cost-tracking cpp-coding-standards cpp-testing csharp-testing
data-throughput-accelerator database-migrations delivery-gate
deployment-patterns design-system dev-team django-celery django-patterns
django-security django-tdd django-verification dmux-workflows
docker-patterns docs-governance documentation-lookup dotnet-patterns
dynamic-workflow-mode e2e-testing ecc-guide ecc-recipes
ecc-tools-cost-audit enterprise-agent-ops error-handling eval-harness
fastapi-patterns flox-environments flutter-dart-code-review
frontend-a11y frontend-design-direction frontend-patterns
gateguard generating-python-installer git-workflow github-ops
golang-patterns golang-testing hexagonal-architecture hookify-rules
intent-driven-development iterative-retrieval java-coding-standards
kotlin-patterns kotlin-testing kubernetes-patterns laravel-patterns
laravel-security laravel-tdd laravel-verification latency-critical-systems
living-docs-governance loop-design-check mcp-dependency-review
mcp-server-patterns mle-workflow module-regression mysql-patterns
nestjs-patterns nextjs-turbopack nodejs-keccak256 nuxt4-patterns
openclaw-persona-forge operator-approval-loop orch-add-feature
orch-build-mvp orch-change-feature orch-fix-defect orch-pipeline
orch-refine-code parallel-execution-optimizer perl-patterns perl-testing
plan-canvas plan-orchestrate plankton-code-quality postgres-patterns
production-audit prompt-caching-strategy prompt-optimizer python-patterns
python-testing pytorch-patterns quarkus-patterns quarkus-security
quarkus-tdd quarkus-verification rails-patterns ralphinho-rfc-pipeline
react-native-patterns react-patterns react-performance react-testing
recursive-decision-ledger redis-patterns repo-scan research-ops
rules-distill rust-patterns rust-testing safety-guard search-first
security-review security-scan skill-comply skill-host-compat
skill-scout skill-stocktake springboot-patterns springboot-security
springboot-tdd springboot-verification strategic-compact swift-concurrency-6-2
swift-protocol-di-testing swiftui-patterns tdd-workflow team-agent-orchestration
team-builder test-collaboration token-budget-advisor token-card
verification-loop vite-patterns vue-patterns windows-desktop-e2e
workspace-surface-audit
""".split())

class SourceSyncError(RuntimeError):pass


def fetch_ecc_skills(dest:Path,ref:str,*,max_skills:int=1000) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',ref):
        raise SourceSyncError('Referencia Git insegura')
    url='https://codeload.github.com/affaan-m/ECC/zip/'+ref
    req=urllib.request.Request(url,headers={'User-Agent':'NCT-ECC-source-compiler/1.0'})
    with urllib.request.urlopen(req,timeout=40) as response:
        raw=response.read(65*1024*1024+1)
    if len(raw)>65*1024*1024:raise SourceSyncError('Archive demasiado grande')
    root=Path(dest).resolve();root.mkdir(parents=True,exist_ok=True)
    count=0;total=0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            # Paths vienen prefijados ECC-<ref>/
            parts=Path(info.filename).parts
            if len(parts)!=4 or parts[1]!='skills' or parts[3]!='SKILL.md':continue
            slug=parts[2]
            if not re.fullmatch(r'[a-z][a-z0-9-]{1,95}',slug):continue
            if slug not in CODING_SKILLS:continue
            if info.file_size>512*1024:raise SourceSyncError('Skill sobredimensionada')
            if (info.external_attr>>16)&0o170000 == 0o120000:raise SourceSyncError('Symlink prohibido')
            total+=info.file_size
            if total>30*1024*1024:raise SourceSyncError('Total fuera de límite')
            target=root/'skills'/slug/'SKILL.md'
            if target.exists():raise SourceSyncError('Archivo ya existe: no sobrescribir fuente')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.read(info))
            count+=1
            if count>max_skills:raise SourceSyncError('Demasiadas skills')
    if not count:raise SourceSyncError('Sin SKILL.md en archive')
    return {'source':'affaan-m/ECC','ref':ref,'downloaded_skills':count,'root':str(root)}
