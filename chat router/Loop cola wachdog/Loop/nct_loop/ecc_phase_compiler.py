"""Compila SKILL.md ECC a artefactos ejecutables Python sin eval/exec.

La conversión estructural registra TODAS las fases del documento fuente como
estados Python; las acciones con efectos reales quedan BLOQUEADAS hasta ser
asignadas a handlers Python revisados. Nunca convierte prosa en shell.
"""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

class ECCCompilationError(ValueError):
    pass

# Documentos ECC son instrucciones no confiables. No ejecutar código extraído.
HEADER = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
STEP = re.compile(r"^\s*(?:Step\s+|Phase\s+|Fase\s+)(\d+)[\s:.-]+(.+)$", re.I)
SAFE_NAME = re.compile(r"^[a-z][a-z0-9-]{1,95}$")

@dataclass(frozen=True)
class CompiledPhase:
    phase_id: str
    title: str
    source_line: int
    action_id: str
    mode: str = "REQUIRES_APPROVED_HANDLER"

@dataclass(frozen=True)
class CompiledSkill:
    skill_id: str
    source_sha256: str
    source_path: str
    phases: tuple[CompiledPhase, ...]
    version: str = "ECC-STRUCTURED-1"

    def asdict(self):
        return {**asdict(self), 'phases': [asdict(x) for x in self.phases]}


def _content(markdown:str) -> str:
    if markdown.startswith('---\n'):
        _, _, remain=markdown.partition('---\n')
        _, sep, rest=remain.partition('\n---\n')
        if sep:
            return rest
    return markdown


def compile_skill(skill_id:str, markdown:str, source_path:str='') -> CompiledSkill:
    if not isinstance(skill_id,str) or not SAFE_NAME.fullmatch(skill_id):
        raise ECCCompilationError('skill_id no válido')
    if not isinstance(markdown,str) or not markdown.strip():
        raise ECCCompilationError('fuente SKILL.md vacía')
    phases=[]
    body=_content(markdown)
    lines=body.splitlines()
    in_code=False
    for lineno,line in enumerate(lines, 1):
        if line.lstrip().startswith(("```","~~~")):
            in_code=not in_code
            continue
        if in_code:continue
        match=HEADER.match(line)
        if not match: continue
        depth,title=len(match.group(1)),match.group(2).strip()
        # Cada sección sustantiva se registra como etapa verificable. No se
        # interpreta texto arbitrario como acción autorizada.
        if depth not in (2,3):continue
        if len(title)>160: title=title[:160]
        seq=len(phases)+1
        phases.append(CompiledPhase(phase_id=f's{seq:03d}',title=title,
                                    source_line=lineno,action_id=f'{skill_id}.s{seq:03d}'))
        if len(phases)>300:raise ECCCompilationError('SKILL.md demasiado grande')
    if not phases:
        phases=[CompiledPhase(phase_id='s001',title='Verify source guidance',
                              source_line=1,action_id=f'{skill_id}.s001')]
    return CompiledSkill(skill_id=skill_id,
                         source_sha256=hashlib.sha256(markdown.encode('utf-8')).hexdigest(),
                         source_path=source_path,phases=tuple(phases))


def compile_directory(ecc_root:Path) -> dict:
    """Indexa todos los SKILL.md accesibles; no afirma ejecución de acciones.

    Debe ejecutarse sobre un checkout ECC REAL en ruta local proporcionada.
    El contrato de salida informa cuántos documentos se procesaron.
    """
    root=Path(ecc_root).resolve()
    if not root.is_dir():raise ECCCompilationError(f'No existe checkout ECC: {root}')
    skill_files=sorted(root.glob('skills/*/SKILL.md'))
    if not skill_files:raise ECCCompilationError('Faltan skills/*/SKILL.md')
    result={}
    for f in skill_files:
        if f.is_symlink() or f.stat().st_size>512*1024:raise ECCCompilationError(f'Skill inválida: {f}')
        key=f.parent.name
        if key in result:raise ECCCompilationError(f'Skill duplicada: {key}')
        result[key]=compile_skill(key,f.read_text(encoding='utf-8'),str(f.relative_to(root))).asdict()
    return result


def write_compiled_catalog(registry:dict,target:Path) -> Path:
    p=Path(target)
    p.parent.mkdir(parents=True,exist_ok=True)
    payload={'format':'ECC-PY-STRUCTURED-1','total_source_documents':len(registry),
             'execution_status':'NO_ACTIONS_AUTOMATICALLY_TRUSTED',
             'skills':registry}
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
    tmp.replace(p)
    return p


def make_python_wrappers(registry:dict, output_dir:Path) -> int:
    """Genera 1 módulo .py real por documento; solo delega acciones al gate.

    No genera ni ejecuta Python desde texto Markdown ni funciones arbitrarias.
    El intérprete de políticas recibe source_sha y verifica handler autorizado.
    """
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    for slug in sorted(registry):
        if not SAFE_NAME.fullmatch(slug):raise ECCCompilationError('slug inválido')
        mod='ecc_'+slug.replace('-','_')
        if not mod.isidentifier():raise ECCCompilationError('slug no es módulo Python')
        lines=[
            '"""Generated ECC phase adapter, no untrusted code execution."""',
            'from nct_loop.ecc_compiled_executor import execute_compiled_skill',
            f'SKILL_ID = {slug!r}',
            f'SOURCE_SHA256 = {registry[slug]["source_sha256"]!r}',
            '',
            'async def run(*, catalog, event, task_id, context, approved_handlers, receipt_callback):',
            '    return await execute_compiled_skill(',
            '        catalog=catalog, skill_id=SKILL_ID, source_sha256=SOURCE_SHA256,',
            '        event=event, task_id=task_id, context=context,',
            '        approved_handlers=approved_handlers, receipt_callback=receipt_callback)',
            '',
        ]
        (out/(mod+'.py')).write_text('\n'.join(lines),encoding='utf-8')
    return len(registry)
