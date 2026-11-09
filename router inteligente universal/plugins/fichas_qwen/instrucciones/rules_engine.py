"""Motor de reglas de instrucciones (prompt_rules.yaml -> prompts ejecutables).

Carga las reglas generadas desde las instrucciones verbatim y arma bloques de
sistema para las fichas del Router. Fail-closed: YAML invalido, ids duplicados
o ids pedidos inexistentes -> RulesError.

Uso:
    from rules_engine import load_rules, build_system
    reglas = load_rules('prompt_rules.yaml')              # lista ordenada
    bloque = build_system(reglas)                          # todas, en orden doc
    bloque = build_system(reglas, ids=['deep-reasoning'])  # subconjunto
"""
import re

import yaml


class RulesError(Exception):
    """Reglas invalidas o pedido imposible (fail-closed)."""


_KINDS = {'patch', 'meta_patch', 'prompt_block', 'seccion'}


def _parse_reglas(doc):
    reglas = doc.get('reglas')
    if not isinstance(reglas, list) or not reglas:
        raise RulesError('sin reglas')
    vistos = set()
    out = []
    for i, r in enumerate(reglas):
        if not isinstance(r, dict):
            raise RulesError(f'regla {i} no es objeto')
        rid = str(r.get('id') or '')
        kind = str(r.get('kind') or '')
        contenido = str(r.get('contenido') or '').strip()
        if not rid or rid in vistos:
            raise RulesError(f'id duplicado o vacio: {rid!r}')
        if kind not in _KINDS:
            raise RulesError(f'kind desconocido en {rid}: {kind!r}')
        if not contenido:
            raise RulesError(f'contenido vacio en {rid}')
        vistos.add(rid)
        out.append({'id': rid, 'kind': kind, 'orden': int(r.get('orden', i)), 'contenido': contenido})
    out.sort(key=lambda r: r['orden'])
    return out


def load_rules(path):
    """Lee prompt_rules.yaml -> lista de reglas ordenadas. Fail-closed."""
    try:
        doc = yaml.safe_load(open(path, encoding='utf-8').read())
    except Exception as e:
        raise RulesError(f'YAML invalido: {e}')
    if not isinstance(doc, dict):
        raise RulesError('documento no es mapping')
    return _parse_reglas(doc)


def build_system(reglas, ids=None, con_ids=True):
    """Concatena reglas en un bloque de sistema. ids=None -> todas en orden doc."""
    elegidas = reglas
    if ids is not None:
        por_id = {r['id']: r for r in reglas}
        faltan = [i for i in ids if i not in por_id]
        if faltan:
            raise RulesError('ids inexistentes: ' + ', '.join(faltan))
        elegidas = [por_id[i] for i in ids]
    partes = []
    for r in elegidas:
        cabeza = f'<patch id="{r["id"]}">' if con_ids else ''
        partes.append((cabeza + '\n' if cabeza else '') + r['contenido'] + ('\n</patch>' if cabeza else ''))
    return '\n\n'.join(partes)


def listar_ids(reglas, kind=None):
    return [r['id'] for r in reglas if kind is None or r['kind'] == kind]
