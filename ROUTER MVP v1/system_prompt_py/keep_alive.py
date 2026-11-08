import threading
import time
import httpx

class SpaceKeepAlive:
    def __init__(self, space_url: str, interval_s: int = 300):
        self.space_url = space_url.rstrip('/')
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._thread.start()

    def _loop(self):
        while not self._stop.wait(self.interval_s):
            try:
                with httpx.Client(timeout=10) as client:
                    client.get(f"{self.space_url}/health")
            except Exception:
                pass

    def stop(self):
        self._stop.set()
