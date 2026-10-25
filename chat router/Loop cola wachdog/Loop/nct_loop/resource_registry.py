"""Fase 2.5: investigación SOLO de catálogo local precargado, sin instalar nada."""
import json
from pathlib import Path

def suggestions(catalog: Path, project_type: str, requirement: str) -> list[dict]:
    data=json.loads(catalog.read_text(encoding='utf8'))
    if not isinstance(data,dict): raise ValueError('catálogo inválido')
    result=[]
    for item in data.get('resources',[]):
        if not isinstance(item,dict):continue
        if project_type not in item.get('tags',[]) and 'general' not in item.get('tags',[]):continue
        if not any(keyword in requirement.lower() for keyword in item.get('keywords',[])):continue
        result.append({'name':item['name'],'type':item['type'],'url':item.get('url'),
                       'license_claim':item.get('license_claim','NO_VERIFICADA'),
                       'coverage_estimate_pct':item.get('coverage_estimate_pct'),
                       'estimated_minutes_saved':item.get('estimated_minutes_saved'),
                       'note':'Candidato, requiere confirmar licencia/compatibilidad antes de usar.'})
    return result[:10]
