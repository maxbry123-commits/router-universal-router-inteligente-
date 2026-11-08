import os
import json
import hashlib
from pathlib import Path

def audit_repo(root_path):
    root = Path(root_path)
    inventory = {}
    for f in root.glob('*.py'):
        if f.name == 'xray_audit.py': continue
        content = f.read_bytes()
        inventory[f.name] = {
            'sha256': hashlib.sha256(content).hexdigest(),
            'bytes': len(content),
            'lines': len(content.splitlines())
        }
    with open(root / 'XRAY_INVENTORY.json', 'w') as out:
        json.dump(inventory, out, indent=2)
    print(f'XRAY_AUDIT_OK: {len(inventory)} archivos auditados.')

if __name__ == '__main__':
    audit_repo(os.path.dirname(os.path.abspath(__file__)))
