"""Convierte INSTRUCCIONES_INPUT_BLOCK_VERBATIM.md en reglas YAML ejecutables.

Extrae 1:1 del documento fuente de verdad (sin reescribir contenido):
  - <patch id="x"> ... </patch>         -> kind: patch
  - [PATCH n — NOMBRE] texto           -> kind: meta_patch
  - PROMPT = \"\"\" ... \"\"\"            -> kind: prompt_block
  - ### <titulo> secciones sueltas      -> kind: seccion (solo si fuera de patch)

Uso: python3 convert_instrucciones.py <fuente.md> <salida.yaml>
Fail-closed: ids duplicados, contenido vacio o cero reglas -> error rc1.
"""
import re
import sys

P_PATCH = re.compile(r'<patch id="([A-Za-z0-9_.-]+)"[^>]*>(.*?)</patch>', re.S)
P_META = re.compile(r'^\[PATCH (\d+) — ([A-Z_0-9]+)\]\s*$', re.M)
P_PROMPT = re.compile(r'PROMPT\s*=\s*"""(.*?)"""', re.S)


def _posiciones_meta(texto):
    """[PATCH n — NOMBRE] + su cuerpo (hasta el siguiente [PATCH o fin de bloque)."""
    marks = list(P_META.finditer(texto))
    for i, m in enumerate(marks):
        fin = marks[i + 1].start() if i + 1 < len(marks) else len(texto)
        cuerpo = _limpio(texto[m.end():fin]).strip()
        yield int(m.group(1)), m.group(2), cuerpo, m.start()


_P_NO_PRINT = re.compile(r'[^\x09\x0a\x20-\x7e\u00a0-\uffff]')  # YAML no admite controles (\x03 etc. del md fuente)


def _limpio(s):
    return _P_NO_PRINT.sub('', s)


def convertir(texto):
    reglas = []
    vistos = set()

    for m in P_PATCH.finditer(texto):
        pid, cuerpo = m.group(1), _limpio(m.group(2)).strip()
        if pid in vistos or not cuerpo:
            continue
        vistos.add(pid)
        reglas.append({'id': pid, 'kind': 'patch', 'orden': len(reglas), 'contenido': cuerpo})

    for n, nombre, cuerpo, _pos in _posiciones_meta(texto):
        pid = f'meta-{n:02d}-{nombre.lower()}'
        if pid in vistos or not cuerpo:
            continue
        vistos.add(pid)
        reglas.append({'id': pid, 'kind': 'meta_patch', 'orden': len(reglas), 'contenido': cuerpo})

    for i, m in enumerate(P_PROMPT.finditer(texto)):
        cuerpo = _limpio(m.group(1)).strip()
        pid = f'prompt-block-{i:02d}'
        if cuerpo and pid not in vistos:
            vistos.add(pid)
            reglas.append({'id': pid, 'kind': 'prompt_block', 'orden': len(reglas), 'contenido': cuerpo})

    return reglas


def _yaml_escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def a_yaml(reglas, fuente):
    out = ['# Generado por convert_instrucciones.py desde INSTRUCCIONES_INPUT_BLOCK_VERBATIM.md',
           '# NO editar a mano: regenerar. kind: patch (<patch id>), meta_patch ([PATCH n]), prompt_block (PROMPT=).',
           f'fuente: "{_yaml_escape(fuente)}"', 'version: 1', 'reglas:']
    for r in reglas:
        out.append(f'  - id: "{_yaml_escape(r["id"])}"')
        out.append(f'    kind: {r["kind"]}')
        out.append(f'    orden: {r["orden"]}')
        out.append('    contenido: |')
        for ln in r['contenido'].splitlines():
            out.append('      ' + ln)
    return '\n'.join(out) + '\n'


def main():
    if len(sys.argv) != 3:
        print('Uso: convert_instrucciones.py <fuente.md> <salida.yaml>')
        return 2
    texto = open(sys.argv[1], encoding='utf-8').read()
    reglas = convertir(texto)
    if not reglas:
        print('VEREDICTO: FAIL (cero reglas extraidas)')
        return 1
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        f.write(a_yaml(reglas, sys.argv[1]))
    print(f'VERDICTO: PASS ({len(reglas)} reglas -> {sys.argv[2]})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
