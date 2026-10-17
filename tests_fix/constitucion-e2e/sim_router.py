"""Router simulado para la prueba E2E del chat: frontend real + plugins reales (fichas_qwen, puente_chat) con el modelo simulado
en la frontera del Harness (puente_chat._chat). El modelo obedece SOLO lo que recibe en el prompt."""
import importlib, json, mimetypes, os, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
WT = Path(sys.argv[1]); PORT = int(sys.argv[2]); LOG = Path(sys.argv[3])
RAIZ = WT / 'router inteligente universal'; FRONT = WT / 'chat router' / 'chat frontend'
sys.path[:0] = [str(RAIZ), str(WT / 'chat router' / '04-MEMORIA')]
os.environ.pop('HF_TOKEN', None)
os.environ['RIU_ROUTER_URL'] = 'http://127.0.0.1:%d' % PORT
import plugins.puente_chat.plugin as pc  # noqa
import plugins.fichas_qwen.plugin as fq  # noqa
_lock = threading.Lock()
def log(d):
    with _lock, LOG.open('a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
def modelo(body):
    texto = '\n'.join(str(m.get('content') or '') for m in body.get('messages') or [])
    log({'tipo': 'modelo', 'model': body.get('model'), 'nodo': body.get('nodo'), 'tiene_constitucion': 'CONSTITUCION SENTINELA' in texto,
         'tiene_sentinela7': 'SENTINELA7' in texto, 'tiene_sp': 'SYSTEM PROMPT DEL DIRECTOR' in texto})
    if 'JUEZ-CORRECTOR' in texto:
        m = re.search(r'TERMINA CON: (\S+)', texto); out = 'Corregida. ' + (m.group(1) if m else '')
    else:
        out = 'Hola, soy el modelo simulado.'
        m = re.search(r'SYSTEM PROMPT DEL DIRECTOR[^\n]*\n(.+)', texto)
        if m and 'Empieza con VALE' in m.group(1): out = 'VALE. ' + out
        if 'CONSTITUCION SENTINELA' in texto and 'DESOBEDECE' not in texto:
            m = re.search(r'termina con (\S+)', texto, re.I)
            if m: out += ' ' + m.group(1)
    if callable(body.get('stream_fn')): body['stream_fn'](out)
    return {'choices': [{'message': {'role': 'assistant', 'content': out}}], 'herramientas': []}
pc._chat = modelo
pc._qwen_conf = lambda: ('sk-sp-simulada', 'https://token-plan.simulado/v1')
fq._gov_prepare = lambda ficha, opts, ap, esperado='': {}
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body, ctype='application/json'):
        b = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/health': return self._send(200, {'status': 'ok'})
        if p == '/': p = '/shell.html'
        if p.startswith('/chat/ui/'): p = p[len('/chat/ui'):]
        f = FRONT / p.lstrip('/')
        if f.is_file(): return self._send(200, f.read_bytes(), mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
        self._send(404, {'error': 'no'})
    def do_POST(self):
        partes = self.path.split('?')[0].strip('/').split('/')
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
        if len(partes) == 4 and partes[0] == 'plugins' and partes[2] == 'call':
            if partes[3] not in ('resultado',):
                log({'tipo': 'http', 'ruta': '/' + '/'.join(partes), 'origen': 'harness' if 'urllib' in (self.headers.get('User-Agent') or '') else 'navegador', 'sentinela': body.get('sentinela'), 'system_prompt': body.get('system_prompt'),
                     'constitucion': body.get('constitucion'), 'ficha_qwen': body.get('ficha_qwen'), 'modelo': body.get('modelo')})
            try:
                r = importlib.import_module('plugins.%s.plugin' % partes[1]).handle(partes[3], body)
                if partes[3] == 'resultado' and isinstance(r, dict) and 'reply' in r:
                    log({'tipo': 'resultado', 'reply': r.get('reply'), 'sentinela': r.get('sentinela')})
                return self._send(200, {'status': 'ok', 'result': r})
            except Exception as e:  # noqa
                return self._send(200, {'status': 'error', 'reason': type(e).__name__ + ': ' + str(e)[:200]})
        self._send(404, {'error': 'no'})
ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
