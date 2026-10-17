'''Fusion determinista de resultados: BM25 de Haystack (sin LLM ni embeddings) si esta instalado; si no, coincidencia de palabras.'''
from __future__ import annotations

import json
import re


def _tokens(s: str) -> set:
    return set(re.findall('[a-z0-9]+', s.lower()))


def _texto(c: dict) -> str:
    return str(c.get('key', '')) + ' ' + json.dumps(c.get('data'), ensure_ascii=False, sort_keys=True)


def ordenar(query: str, candidatos: list) -> tuple:
    if not candidatos:
        return [], 'vacio'
    try:
        from haystack import Document
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
        from haystack.document_stores.in_memory import InMemoryDocumentStore
    except Exception:  # noqa: BLE001
        q = _tokens(query)
        for c in candidatos:
            c['puntaje'] = len(q & _tokens(_texto(c)))
        return sorted(candidatos, key=lambda c: (-c['puntaje'], c['orden'], str(c['key']))), 'palabras'
    store = InMemoryDocumentStore()
    store.write_documents([Document(id=str(i), content=_texto(c)) for i, c in enumerate(candidatos)])
    hits = InMemoryBM25Retriever(document_store=store, top_k=len(candidatos)).run(query=query)['documents']
    score = {int(d.id): round(float(d.score or 0), 6) for d in hits}
    for i, c in enumerate(candidatos):
        c['puntaje'] = score.get(i, 0.0)
    return sorted(candidatos, key=lambda c: (-c['puntaje'], c['orden'], str(c['key']))), 'haystack-bm25'
