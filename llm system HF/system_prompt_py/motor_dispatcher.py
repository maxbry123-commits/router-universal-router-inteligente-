# motor_dispatcher.py
from safe_executor import safe_path
import os

class MotorError(Exception):
    pass

class MotorDispatcher:
    """
    Extraído de motor_cli.py. Despacha las operaciones declarativas (JSON) a funciones Python.
    """
    def __init__(self, root: str, policy: dict):
        self.root = root
        self.ops_allowed = set(policy.get('allowed_ops', []))
        self.max_ops = policy.get('max_ops', 32)
        self.max_chars = policy.get('max_text_chars', 10000)
        
        # El mapeo de comandos a funciones
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
            raise MotorError(f"Operación no autorizada o inexistente: {op}")
        
        return self.handlers[op](cmd)

    def inspect(self, cmd):
        return {'files': sorted(os.listdir(self.root))[:100]}

    def mkdir(self, cmd):
        dest = safe_path(self.root, cmd['path'])
        os.makedirs(dest, exist_ok=True)
        return {'path': cmd['path'], 'exists': True}

    def write(self, cmd):
        content = cmd['text']
        if len(content) > self.max_chars:
            raise MotorError('Texto demasiado largo')
        dest = safe_path(self.root, cmd['path'])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        return {'path': cmd['path'], 'written': len(content)}

    def read(self, cmd):
        dest = safe_path(self.root, cmd['path'])
        with open(dest, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'content': content, 'length': len(content)}

    def finish(self, cmd):
        return {'batch_finished': True}
