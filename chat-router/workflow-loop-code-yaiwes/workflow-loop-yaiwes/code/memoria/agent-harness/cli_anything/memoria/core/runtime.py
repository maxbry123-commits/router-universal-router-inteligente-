'''Runtime determinista del orquestador de memoria y almacenamiento. 0% LLM: reglas fijas, orden fijo, puntaje por coincidencia de palabras.'''
from __future__ import annotations

import json
import re

from ..utils import backend as B
from . import fusion


def _tokens(s: str) -> set:
    return set(re.findall('[a-z0-9]+', s.lower()))


class Orquestador:
    def estado(self) -> list:
        return [B.estado(m) for m in B.ORDEN]

    def conectados(self) -> list:
        return [e for e in self.estado() if e['estado'] == 'CONNECTED']

    def guardar(self, scope: str, key: str, data) -> dict:
        guardado, fallos, omitidos = [], {}, {}
        for e in self.estado():
            m = e['motor']
            if e['estado'] != 'CONNECTED':
                omitidos[m] = e['detalle']
            elif e['solo_lectura']:
                omitidos[m] = 'solo lectura'
            else:
                try:
                    B.http(m, 'POST', '/save', {'scope': scope, 'key': key, 'data': data})
                    guardado.append(m)
                except Exception as exc:  # noqa: BLE001
                    fallos[m] = type(exc).__name__
        return {'ok': bool(guardado), 'guardado_en': guardado, 'fallos': fallos, 'omitidos': omitidos}

    def cargar(self, scope: str, key: str) -> dict:
        for e in self.conectados():
            try:
                r = B.http(e['motor'], 'GET', '/load', params={'scope': scope, 'key': key})
            except Exception:  # noqa: BLE001
                continue
            recs = r.get('records', []) if isinstance(r, dict) else (r or [])
            if recs:
                return {'motor': e['motor'], 'records': recs}
        return {'motor': None, 'records': []}

    def buscar(self, scope: str, query: str, k: int = 10) -> dict:
        q = _tokens(query)
        vistos: dict = {}
        for orden, e in enumerate(self.conectados()):
            try:
                r = B.http(e['motor'], 'GET', '/search', params={'scope': scope, 'query': query, 'k': k})
            except Exception:  # noqa: BLE001
                continue
            for rec in (r.get('records', []) if isinstance(r, dict) else (r or [])):
                dato = json.dumps(rec.get('data'), ensure_ascii=False, sort_keys=True)
                clave = (rec.get('scope'), rec.get('key'), dato)
                if clave in vistos:
                    vistos[clave]['motores'].append(e['motor'])
                    continue
                vistos[clave] = {'scope': rec.get('scope'), 'key': rec.get('key'), 'data': rec.get('data'),
                                 'puntaje': len(q & _tokens(str(rec.get('key', '')) + ' ' + dato)), 'motores': [e['motor']], 'orden': orden}
        res, metodo = fusion.ordenar(query, list(vistos.values()))
        res = res[:k]
        for x in res:
            x.pop('orden')
        return {'consulta': query, 'metodo': metodo, 'resultados': res}
