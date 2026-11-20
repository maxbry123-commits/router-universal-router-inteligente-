import os
import hashlib
from pathlib import Path

class MotorError(Exception):
    pass

class MotorDispatcher:
    def __init__(self, root: str, policy: dict):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.ops_allowed = set(policy.get('allowed_ops', []))
        self.max_chars = int(policy.get('max_text_chars', 10000))
        self.handlers = {
            'inspect_workspace': self.inspect,
            'create_directory': self.mkdir,
            'write_text': self.write,
            'read_text': self.read,
            'finish': self.finish,
        }

    def dispatch(self, cmd: dict) -> dict:
        op = cmd.get('op')
        if op not in self.ops_allowed or op not in self.handlers:
            raise MotorError(f"Operacion no autorizada: {op}")
        return self.handlers[op](cmd)

    def inspect(self, cmd):
        return {'files': sorted(p.name for p in self.root.iterdir())[:100]}

    def mkdir(self, cmd):
        dest = (self.root / cmd['path']).resolve()
        if not dest.is_relative_to(self.root):
            raise MotorError('Ruta fuera del workspace')
        dest.mkdir(parents=True, exist_ok=True)
        return {'path': cmd['path'], 'exists': True}

    def write(self, cmd):
        if len(cmd['text']) > self.max_chars:
            raise MotorError('Texto demasiado largo')
        dest = (self.root / cmd['path']).resolve()
        if not dest.is_relative_to(self.root):
            raise MotorError('Ruta fuera del workspace')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cmd['text'], encoding='utf-8')
        return {'path': cmd['path'], 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}

    def read(self, cmd):
        dest = (self.root / cmd['path']).resolve()
        if not dest.is_file():
            raise MotorError('Archivo no existe')
        return {'content': dest.read_text(encoding='utf-8'), 'length': len(dest.read_text(encoding='utf-8'))}

    def finish(self, cmd):
        return {'batch_finished': True}
