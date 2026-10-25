#!/usr/bin/env python3
"""Referencia ORIGINAL de motor JSON declarativo + DAG (NO es código de Ricardo)."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


class MotorError(Exception):
    pass


class Motor:
    def __init__(self, root, policy):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.ops_allowed = set(policy['allowed_ops'])
        self.max_ops = int(policy.get('max_ops', 32))
        self.max_chars = int(policy.get('max_text_chars', 10000))
        self.receipts = []
        self.handlers = {
            'inspect_workspace': self.inspect,
            'create_directory': self.mkdir,
            'write_text': self.write,
            'read_text': self.read,
            'verify_exists': self.exists,
            'verify_contains': self.contains,
            'finish': self.finish,
        }
        self.errors = []

    def path(self, value):
        if not isinstance(value, str) or not value.strip():
            raise MotorError('ruta vacía o inválida')
        incoming = Path(value)
        if incoming.is_absolute():
            raise MotorError('ruta absoluta prohibida')
        target = (self.root / incoming).resolve()
        if not target.is_relative_to(self.root):
            raise MotorError('ruta fuera del workspace')
        return target

    def inspect(self, cmd):
        return {'files': sorted(p.name for p in self.root.iterdir())[:100]}

    def mkdir(self, cmd):
        dest = self.path(cmd['path'])
        dest.mkdir(parents=True, exist_ok=True)
        return {'path': str(dest.relative_to(self.root)), 'exists': dest.is_dir()}

    def write(self, cmd):
        content = cmd['text']
        if not isinstance(content, str) or len(content) > self.max_chars:
            raise MotorError('texto inválido o demasiado largo')
        dest = self.path(cmd['path'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if not dest.is_file():
                raise MotorError('el destino no es un archivo')
            existing = dest.read_text(encoding='utf-8')
            if existing != content:
                raise MotorError('archivo diferente ya existe; requiere aprobación explícita')
        else:
            dest.write_text(content, encoding='utf-8')
        return {'path': str(dest.relative_to(self.root)), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}

    def read(self, cmd):
        dest = self.path(cmd['path'])
        value = dest.read_text(encoding='utf-8')
        return {'length': len(value), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}

    def exists(self, cmd):
        dest = self.path(cmd['path'])
        if not dest.is_file():
            raise MotorError('archivo esperado no existe')
        return {'exists': True, 'path': str(dest.relative_to(self.root))}

    def contains(self, cmd):
        dest = self.path(cmd['path'])
        needle = cmd['text']
        if not isinstance(needle, str) or not needle:
            raise MotorError('texto de verificación inválido')
        if needle not in dest.read_text(encoding='utf-8'):
            raise MotorError('no contiene el texto esperado')
        return {'verified': True, 'path': str(dest.relative_to(self.root))}

    def finish(self, cmd):
        return {'batch_finished': True, 'objective_audited': False}

    def order(self, operations):
        if not isinstance(operations, list) or not (1 <= len(operations) <= self.max_ops):
            raise MotorError('número de operaciones inválido')
        table = {}
        for item in operations:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'].strip():
                raise MotorError('ID inválido')
            if item['id'] in table:
                raise MotorError('ID duplicado')
            if item.get('op') not in self.ops_allowed or item['op'] not in self.handlers:
                raise MotorError('operación no autorizada: ' + str(item.get('op')))
            deps = item.get('depends_on', [])
            if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
                raise MotorError('depends_on inválido')
            if len(set(deps)) != len(deps):
                raise MotorError('dependencias duplicadas')
            table[item['id']] = item
        for item in operations:
            if any(dep not in table for dep in item.get('depends_on', [])):
                raise MotorError('dependencia inexistente')
        status, result = {}, []
        def visit(node):
            if status.get(node) == 'active':
                raise MotorError('ciclo DAG')
            if status.get(node) == 'done':
                return
            status[node] = 'active'
            for dep in table[node].get('depends_on', []):
                visit(dep)
            status[node] = 'done'
            result.append(table[node])
        for item in operations:
            visit(item['id'])
        return result

    def run(self, doc):
        try:
            if not isinstance(doc, dict):
                raise MotorError('JSON raíz debe ser un objeto')
            ordered = self.order(doc['ops'])
            for item in ordered:
                result = self.handlers[item['op']](item)
                self.receipts.append({'id': item['id'], 'op': item['op'], 'ok': True, 'result': result})
        except (MotorError, ValueError, TypeError, KeyError, OSError, UnicodeError) as exc:
            self.errors.append({'type': type(exc).__name__, 'message': str(exc)})
        return {'ok': not self.errors, 'ops_total': len(doc.get('ops', [])) if isinstance(doc, dict) else 0,
                'ops_executed': len(self.receipts), 'receipts': self.receipts, 'errors': self.errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan')
    parser.add_argument('--policy', required=True)
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    doc = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    policy = json.loads(Path(args.policy).read_text(encoding='utf-8'))
    report = Motor(args.root, policy).run(doc)
    print('YAIWES_OP_REPORT ' + json.dumps(report, ensure_ascii=False))
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    sys.exit(main())
