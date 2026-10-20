'''Cliente LOCAL para memanto, sin nube ni Docker: misma forma que el cliente de Moorcheh
(namespaces, documents, similarity_search, answer, files), guardado en SQLite y busqueda determinista por palabras.
answer.generate usa el mini kernel LLM (5%) si esta configurado; si no, arma la respuesta con los fragmentos encontrados.'''
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_kernel  # noqa: E402


try:
    from moorcheh_sdk.exceptions import NamespaceNotFound  # el sustituto local: memanto ya sabe manejar este error
except Exception:  # noqa: BLE001
    class NamespaceNotFound(Exception):
        pass


def _tok(s) -> list:
    return re.findall('[a-z0-9]+', str(s).lower())


class _Store:
    def __init__(self, path: str) -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.q('CREATE TABLE IF NOT EXISTS ns (name TEXT PRIMARY KEY, type TEXT)')
        self.q('CREATE TABLE IF NOT EXISTS doc (ns TEXT, id TEXT, data TEXT, PRIMARY KEY (ns, id))')

    def q(self, sql: str, args=()) -> list:
        with self.lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur.fetchall()


class _Namespaces:
    def __init__(self, s: _Store) -> None:
        self.s = s

    def create(self, namespace_name: str, type: str = 'text', **kw) -> dict:
        self.s.q('INSERT OR IGNORE INTO ns VALUES (?, ?)', (namespace_name, type))
        return {'status': 'success', 'namespace_name': namespace_name}

    def list(self, **kw) -> dict:
        return {'namespaces': [{'namespace_name': n, 'type': t} for n, t in self.s.q('SELECT name, type FROM ns ORDER BY name')]}

    def delete(self, namespace_name: str, **kw) -> dict:
        self.s.q('DELETE FROM doc WHERE ns = ?', (namespace_name,))
        self.s.q('DELETE FROM ns WHERE name = ?', (namespace_name,))
        return {'status': 'success'}


class _Documents:
    def __init__(self, s: _Store) -> None:
        self.s = s

    def upload(self, namespace_name: str, documents: list, **kw) -> dict:
        self.s.q('INSERT OR IGNORE INTO ns VALUES (?, ?)', (namespace_name, 'text'))
        for d in documents:
            self.s.q('INSERT OR REPLACE INTO doc VALUES (?, ?, ?)', (namespace_name, str(d.get('id')), json.dumps(d, ensure_ascii=False, default=str)))
        return {'status': 'success', 'submitted_ids': [str(d.get('id')) for d in documents]}

    def get(self, namespace_name: str, ids: list, **kw) -> dict:
        if not self.s.q('SELECT 1 FROM ns WHERE name = ?', (namespace_name,)):
            raise NamespaceNotFound(namespace_name)
        items = []
        for i in ids:
            r = self.s.q('SELECT data FROM doc WHERE ns = ? AND id = ?', (namespace_name, str(i)))
            if r:
                items.append(json.loads(r[0][0]))
        return {'items': items}

    def delete(self, namespace_name: str, ids: list, **kw) -> dict:
        for i in ids:
            self.s.q('DELETE FROM doc WHERE ns = ? AND id = ?', (namespace_name, str(i)))
        return {'status': 'success'}

    def fetch_text_data(self, namespace_name: str, **kw) -> dict:
        return {'items': [json.loads(r[0]) for r in self.s.q('SELECT data FROM doc WHERE ns = ? ORDER BY id', (namespace_name,))]}

    def upload_file(self, namespace_name: str, file_path: str, **kw) -> dict:
        p = Path(file_path)
        return self.upload(namespace_name, [{'id': p.name, 'text': p.read_text(errors='ignore'), 'source': 'file'}])


class _Files:
    def __init__(self, docs: _Documents) -> None:
        self.docs = docs

    def upload(self, namespace_name: str, files: list, **kw) -> dict:
        for f in files:
            self.docs.upload_file(namespace_name, f.get('path') if isinstance(f, dict) else f)
        return {'status': 'success'}


class _Search:
    def __init__(self, s: _Store) -> None:
        self.s = s

    def query(self, query: str, namespaces: list, top_k: int = 10, threshold=None, **kw) -> dict:
        q = set(_tok(query))
        res = []
        for ns in namespaces or []:
            for (data,) in self.s.q('SELECT data FROM doc WHERE ns = ?', (ns,)):
                d = json.loads(data)
                t = set(_tok(d.get('text', '')))
                hit = len(q & t)
                if not q or not hit:
                    continue
                score = round(hit / len(q), 6)
                if threshold and score < threshold:
                    continue
                res.append({'id': d.get('id'), 'score': score, 'text': d.get('text', ''), 'namespace': ns,
                            'metadata': {k: v for k, v in d.items() if k != 'text'}})
        res.sort(key=lambda r: (-r['score'], str(r['id'])))
        return {'results': res[:int(top_k or 10)]}


class _Answer:
    def __init__(self, s: _Store, search: _Search) -> None:
        self.s, self.search = s, search

    def generate(self, namespace=None, query: str = '', top_k: int = 5, **kw) -> dict:
        nss = [namespace] if namespace else [r[0] for r in self.s.q('SELECT name FROM ns')]
        ctx = self.search.query(query, nss, top_k=top_k)['results'] if query else []
        fragmentos = [c['text'] for c in ctx]
        texto = None
        if llm_kernel.disponible():
            texto = llm_kernel.pedir(str(kw.get('header_prompt') or '') + chr(10) + chr(10).join(fragmentos) + chr(10) + str(query) + chr(10) + str(kw.get('footer_prompt') or ''))
        if texto is None:
            texto = chr(10).join(fragmentos)
        return {'answer': texto, 'modo': 'llm' if llm_kernel.disponible() and texto else 'extractivo', 'sources': [c['id'] for c in ctx]}


class LocalClient:
    def __init__(self, path: str | None = None) -> None:
        path = path or os.environ.get('MEMANTO_LOCAL_DB', '/tmp/riu-motores/memanto.sqlite')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        s = _Store(path)
        self.namespaces = _Namespaces(s)
        self.documents = _Documents(s)
        self.files = _Files(self.documents)
        self.similarity_search = _Search(s)
        self.answer = _Answer(s, self.similarity_search)
