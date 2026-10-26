"""Crea el banco desde variables de entorno (NVIDIA_API_KEY_n, GROQ_API_KEY_n, OPENAI_*). Sin secretos en el archivo."""
import os, re, sys
from pathlib import Path
from .vault import Vault


def ref_for(name: str):
    m = re.match(r"^(NVIDIA|GROQ)_API_KEY_(\d+)$", name)
    if m:
        return m.group(1).lower() + "/" + m.group(2)
    m = re.match(r"^OPENAI_([0-9A-Za-z_]+)$", name)
    if m:
        return "openai/" + m.group(1).lower().replace("_", ".")
    return None


def build(path, master, env=None):
    env = env or os.environ
    v = Vault(path)
    if not v.exists():
        v.initialize(master)
    u = v.unlock(master)
    n = 0
    for k, val in env.items():
        r = ref_for(k)
        if r and val:
            u.put(r, val)
            n += 1
    return n


if __name__ == "__main__":
    print(build(Path(sys.argv[1]), os.environ["RIU_BANK_MASTER"]))
