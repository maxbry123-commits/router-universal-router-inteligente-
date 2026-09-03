"""enchufe_gate.py — validador de contratos para el router universal.

Valida que cada artifact cumpla el schema antes de rutear.
"""
import hashlib
import hmac
import re
import time
from dataclasses import dataclass, field
from typing import Any

# Regex
RE_ARTIFACT = re.compile(r"^art_[a-z0-9]{8,32}$")
RE_HASH = re.compile(r"^[a-f0-9]{64}$")
RE_KINDS = {"text", "code", "file", "image", "consensus", "manifest"}
RE_TRANSPORTS = {"http", "sse", "ws", "file", "ipc"}
RE_SANDBOX = {"pyodide", "wasm", "native", "none", "docker"}
RE_ESTADO = {"pending", "approved", "rejected", "completed", "expired"}


@dataclass
class Artifact:
    artifact_id: str
    estado: str = "pending"
    kind: str = "text"
    transport: str = "http"
    sandbox: str = "none"
    timeout_ms: int = 30000
    payload: Any = None
    hash: str = ""
    signature: str = ""
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    ttl_ms: int = 3600000

    def validate(self) -> tuple[bool, str]:
        """Returns (ok, error_message)."""
        if not RE_ARTIFACT.match(self.artifact_id):
            return False, f"artifact_id invalid: {self.artifact_id}"
        if self.estado not in RE_ESTADO:
            return False, f"estado invalid: {self.estado}"
        if self.kind not in RE_KINDS:
            return False, f"kind invalid: {self.kind}"
        if self.transport not in RE_TRANSPORTS:
            return False, f"transport invalid: {self.transport}"
        if self.sandbox not in RE_SANDBOX:
            return False, f"sandbox invalid: {self.sandbox}"
        if self.timeout_ms < 100 or self.timeout_ms > 600000:
            return False, f"timeout_ms out of range: {self.timeout_ms}"
        if not self.hash:
            return False, "hash required"
        if not RE_HASH.match(self.hash):
            return False, f"hash invalid (not SHA256): {self.hash}"
        # Expiración
        if self.created_at + self.ttl_ms < int(time.time() * 1000):
            return False, "artifact expired"
        return True, "ok"

    def compute_hash(self) -> str:
        """Calcula SHA256 del payload."""
        if isinstance(self.payload, (dict, list)):
            import json
            s = json.dumps(self.payload, sort_keys=True)
        else:
            s = str(self.payload)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def sign(self, secret: str) -> str:
        """Firma HMAC-SHA256."""
        msg = f"{self.artifact_id}|{self.estado}|{self.kind}|{self.hash}"
        return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


def gate(art: Artifact, secret: str = "") -> tuple[bool, str]:
    """Enchufe gate: valida contrato + verifica firma."""
    if not art.hash:
        art.hash = art.compute_hash()
    ok, err = art.validate()
    if not ok:
        return False, err
    if secret:
        if not art.signature:
            return False, "signature required when secret configured"
        expected = art.sign(secret)
        if not hmac.compare_digest(art.signature, expected):
            return False, "signature mismatch"
    return True, "ok"


if __name__ == "__main__":
    # Demo
    a = Artifact(artifact_id="art_test123abc", payload={"hello": "world"})
    a.hash = a.compute_hash()
    a.signature = a.sign("demo-secret")
    print(gate(a, secret="demo-secret"))
