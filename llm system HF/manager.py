import json
import os
import signal
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BACKEND_PORT = 8081
BACKEND = f"http://127.0.0.1:{BACKEND_PORT}"
IDLE_UNLOAD_S = float(os.environ.get("IDLE_UNLOAD_S", "900"))
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
MODEL_PATH = os.getenv("MODEL_PATH", "/data/models/qwen2.5-coder-0.5b-instruct-q5_k_m.gguf")

if not ROUTER_API_KEY:
    raise RuntimeError("FATAL: ROUTER_API_KEY no configurada.")

class ModelProcess:
    def __init__(self):
        self.process = None
        self.last_call = time.time()
        self.lock = threading.Lock()

    def load(self):
        with self.lock:
            if self.process is None:
                print("Cargando llama-server...")
                try:
                    self.process = subprocess.Popen(
                        ["llama-server", "-m", MODEL_PATH, "--port", str(BACKEND_PORT), "--ctx-size", "8192"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except FileNotFoundError:
                    raise RuntimeError("llama-server no instalado en la imagen")
            self.last_call = time.time()

    def unload_if_idle(self):
        with self.lock:
            if self.process is not None and (time.time() - self.last_call) > IDLE_UNLOAD_S:
                self.process.send_signal(signal.SIGTERM)
                self.process.wait()
                self.process = None

MODEL = ModelProcess()

def idle_monitor():
    while True:
        time.sleep(10)
        MODEL.unload_if_idle()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path.startswith("/v1/chat/completions"):
            if self.headers.get("X-API-Key") != ROUTER_API_KEY:
                self.send_response(401); self.end_headers(); self.wfile.write(b'{"error":"Invalid API Key"}')
                return

            try:
                MODEL.load()
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                req = urllib.request.Request(BACKEND + "/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req) as resp:
                    self.send_response(resp.status); self.end_headers(); self.wfile.write(resp.read())
            except Exception as e:
                self.send_response(500); self.end_headers(); self.wfile.write(str(e).encode())
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, format, *args): pass

if __name__ == "__main__":
    threading.Thread(target=idle_monitor, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", 7860), Handler)
    server.serve_forever()
