"""router.py — core routing del Router Universal NCT."""
import json
import time
from dataclasses import asdict
from typing import Any
from urllib.request import Request, urlopen

from enchufe_gate import Artifact, gate

SATELLITES = {
    "openclaw": "http://95.111.232.89:7001",
    "claude-code": "http://95.111.232.89:7002",
    "mimo-code": "http://95.111.232.89:7003",
    "nct": "http://95.111.232.89:7004",
    "ocr": "http://95.111.232.89:9001",
    "obsidian": "http://95.111.232.89:8001",
    "graphiti": "http://95.111.232.89:8002",
    "openhands": "http://95.111.232.89:3000",
    "hermes_mem": "http://95.111.232.89:8007",
    "paperclip": "http://95.111.232.89:8009",
}

def send(to: str, payload: Any, kind: str = "text", timeout_ms: int = 30000, secret: str = "") -> dict:
    if to not in SATELLITES: return {"ok": False, "error": f"unknown satellite: {to}"}
    art = Artifact(artifact_id=f"art_{int(time.time()*1000):x}{hash(str(payload)) & 0xffff:04x}", kind=kind, transport="http", payload=payload, timeout_ms=timeout_ms)
    art.hash = art.compute_hash()
    if secret: art.signature = art.sign(secret)
    ok, err = gate(art, secret=secret)
    if not ok: return {"ok": False, "error": err}
    req = Request(SATELLITES[to] + "/execute", data=json.dumps(asdict(art)).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=timeout_ms / 1000) as r: return json.loads(r.read().decode("utf-8"))
    except Exception as e: return {"ok": False, "error": str(e), "satellite": to}

def broadcast(payload: Any, satellites: list[str] = None, kind: str = "text") -> list[dict]:
    sats = satellites or list(SATELLITES.keys())
    return [send(s, payload, kind=kind) for s in sats]

if __name__ == "__main__":
    print("Router NCT — satélites disponibles:")
    for name, url in SATELLITES.items(): print(f"  {name:15} → {url}")
    print("\nDemo:")
    print(f"  openclaw: {send('openclaw', {'text': 'ping'}, kind='text')}")
