# merkle_ledger.py
import hashlib
import json
from typing import List

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

class MerkleLedger:
    """
    Ledger append-only con verificación Merkle.
    Cada bloque se encadena al hash del bloque anterior.
    """
    def __init__(self):
        self.blocks: List[dict] = []

    def append(self, event: dict) -> str:
        prev_hash = self.blocks[-1]["hash"] if self.blocks else "0" * 64
        block = {
            "index": len(self.blocks),
            "event": event,
            "prev_hash": prev_hash
        }
        block_str = json.dumps(block, sort_keys=True)
        block["hash"] = hash_data(block_str)
        self.blocks.append(block)
        return block["hash"]

    def verify_chain(self) -> bool:
        """Verifica que ningún bloque haya sido alterado."""
        for i in range(1, len(self.blocks)):
            if self.blocks[i]["prev_hash"] != self.blocks[i-1]["hash"]:
                return False
        return True

    def merkle_root(self) -> str:
        """Calcula el hash raíz de todo el historial."""
        if not self.blocks:
            return hash_data("")
        hashes = [b["hash"] for b in self.blocks]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])  # Duplicar el último si es impar
            hashes = [hash_data(hashes[i] + hashes[i+1]) for i in range(0, len(hashes), 2)]
        return hashes[0]
