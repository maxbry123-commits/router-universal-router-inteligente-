"""connectors.py — transportes disponibles para el router."""
import json
import time
from typing import Any


class HTTPConnector:
    def __init__(self, base_url: str, timeout: int = 30000):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def send(self, artifact: dict) -> dict:
        from urllib.request import Request, urlopen
        req = Request(self.base_url + "/execute",
                      data=json.dumps(artifact).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=self.timeout / 1000) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            return {"ok": False, "error": str(e)}


class SSEConnector:
    """Server-Sent Events — para streams largos."""
    def __init__(self, base_url: str):
        self.base_url = base_url

    def stream(self, artifact: dict):
        from urllib.request import urlopen
        url = self.base_url + "/events?artifact_id=" + artifact.get("artifact_id", "")
        with urlopen(url) as r:
            for line in r:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    yield json.loads(line[6:])


class WebSocketConnector:
    """WebSocket — bidireccional."""
    def __init__(self, ws_url: str):
        self.ws_url = ws_url

    def connect(self):
        try:
            import websocket
            return websocket.create_connection(self.ws_url)
        except ImportError:
            raise RuntimeError("websocket-client not installed: pip install websocket-client")


class FileConnector:
    """Para sync local con VPS via filesystem."""
    def __init__(self, path: str):
        self.path = path

    def send(self, artifact: dict) -> dict:
        import os
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fname = os.path.join(self.path, f"{artifact['artifact_id']}.json")
        with open(fname, "w") as f:
            json.dump(artifact, f, indent=2)
        return {"ok": True, "path": fname}
