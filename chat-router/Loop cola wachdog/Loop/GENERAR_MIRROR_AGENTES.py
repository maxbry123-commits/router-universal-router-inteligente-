#!/usr/bin/env python3
"""Genera config/agentes.json: espejo (mirror) de modelos y agentes que el LOOP puede llamar.
Se lee del repo real (mvp/modelos.json y chat-router/agentes/*); nada se inventa.
Uso: python GENERAR_MIRROR_AGENTES.py [--repo RAIZ]"""
import argparse, json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GRUPOS = {  # carpeta de chat-router/agentes -> (tipo, como se llama hoy)
    'agentes-listos': ('agente_listo', 'catalogo'),
    'frameworks': ('framework', 'catalogo'),
    'investigacion': ('investigacion', 'catalogo'),
    'orquestacion': ('orquestacion', 'catalogo'),
    'agentes-yaiwes': ('agente_yaiwes', 'plugin:agentes'),
}


def generar(repo: Path) -> dict:
    modelos = json.loads((repo / 'mvp' / 'modelos.json').read_text(encoding='utf8'))['texto']
    out = [{'id': m['id'], 'tipo': 'modelo', 'ruta': None, 'llamada': {'via': 'puente_chat', 'modelo': m['id']},
            'estado': 'llamable' if m.get('p') else 'sin_plan'} for m in modelos]
    base = repo / 'chat-router' / 'agentes'
    for grupo, (tipo, via) in GRUPOS.items():
        for d in sorted((base / grupo).iterdir()) if (base / grupo).is_dir() else []:
            if d.is_dir() and not d.name.startswith('.'):
                out.append({'id': d.name, 'tipo': tipo, 'ruta': str(d.relative_to(repo)),
                            'llamada': {'via': via}, 'estado': 'catalogado_sin_puente'
                            if via == 'catalogo' else 'plugin_cargable'})
    cc = base / 'claude-code'
    if cc.is_dir():
        out.append({'id': 'claude-code', 'tipo': 'pasarela', 'ruta': str(cc.relative_to(repo)),
                    'llamada': {'via': 'pasarela_local', 'puerto': 8082, 'requiere': 'NVIDIA_API_KEY'},
                    'estado': 'requiere_proceso_local'})
    for a in out:  # todo agente lleva su lista de espejos; el local es el primero
        a['mirrors'] = [{'id': 'local', 'tipo': 'local', 'ruta': a['ruta']}] if a.get('ruta') else []
    fuentes = AQUI / 'config' / 'mirrors_fuentes.json'
    if fuentes.is_file():
        por_id = {a['id']: a for a in out}
        for f in json.loads(fuentes.read_text(encoding='utf8'))['agentes']:
            a = por_id.get(f['id'])
            if a is None:
                a = {'id': f['id'], 'tipo': f.get('tipo', 'agente_externo'), 'ruta': None,
                     'descripcion': f.get('descripcion', ''), 'llamada': {'via': 'catalogo'},
                     'estado': 'espejado_sin_puente', 'mirrors': []}
                out.append(a)
                por_id[a['id']] = a
            for i, m in enumerate(f.get('mirrors', [])):
                a['mirrors'].append({'id': '%s-%d' % (m.get('tipo', 'extra'), i), **m})
    return {'version': 2, 'total': len(out), 'agentes': out}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=str(AQUI.parents[2]))
    ns = ap.parse_args()
    doc = generar(Path(ns.repo))
    (AQUI / 'config' / 'agentes.json').write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf8')
    print('agentes.json:', doc['total'], 'entradas')
