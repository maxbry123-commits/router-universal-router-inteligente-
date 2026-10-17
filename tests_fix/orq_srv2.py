import json, os, sys, mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
R = '/workspace/orq/router inteligente universal'; F = '/workspace/orq/chat router/chat frontend'
sys.path.insert(0, R)
os.environ.setdefault('RIU_PUENTE_URL', 'https://comand-center-1-riu-router.hf.space/plugins/puente_chat/call')
os.environ.setdefault('RIU_ORQ_DIR', '/workspace/sim/live-lat/orq-v2-data/orq'); os.environ.setdefault('RIU_DATA_DIR', '/workspace/sim/live-lat/orq-v2-data')
from plugins.orquestador import plugin as orq
class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', '*'); self.send_header('Access-Control-Allow-Methods', 'POST,GET,OPTIONS')
    def do_OPTIONS(self): self.send_response(204); self._cors(); self.end_headers()
    def do_POST(self):
        pre = '/plugins/orquestador/call/'
        if not self.path.startswith(pre): self.send_response(404); self.end_headers(); return
        n = int(self.headers.get('Content-Length') or 0); p = json.loads(self.rfile.read(n) or b'{}')
        try: res = {'status': 'ok', 'result': orq.handle(self.path[len(pre):], p)}
        except Exception as x: res = {'status': 'error', 'reason': repr(x)}
        b = json.dumps(res).encode(); self.send_response(200); self._cors(); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        path = self.path.split('?')[0]
        path = '/shell.html' if path == '/' else path.replace('/chat/ui/', '/', 1)
        fp = os.path.normpath(F + path)
        if not fp.startswith(F) or not os.path.isfile(fp): self.send_response(404); self.end_headers(); return
        b = open(fp, 'rb').read(); self.send_response(200); self.send_header('Content-Type', mimetypes.guess_type(fp)[0] or 'text/plain'); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
ThreadingHTTPServer(('127.0.0.1', 8899), H).serve_forever()
