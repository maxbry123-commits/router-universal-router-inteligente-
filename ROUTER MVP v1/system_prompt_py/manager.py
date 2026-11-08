import json, os, signal, subprocess, sys, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
BACKEND_PORT = 8081
BACKEND = f"http://127.0.0.1:{BACKEND_PORT}"
IDLE_UNLOAD_S = float(os.environ.get("IDLE_UNLOAD_S", "900"))
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"ok"}')
        elif self.path == "/v1/models":
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"data":[]}')
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path.startswith("/v1/chat/completions"):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            req = urllib.request.Request(BACKEND + "/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req) as resp:
                    self.send_response(resp.status); self.end_headers(); self.wfile.write(resp.read())
            except Exception as e:
                self.send_response(502); self.end_headers()
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, format, *args): pass
if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("Manager on 8080"); server.serve_forever()
