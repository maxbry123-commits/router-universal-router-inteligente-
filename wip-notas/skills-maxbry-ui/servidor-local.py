import http.server,os,sys
ROOT="/workspace/wt/rui/chat router/chat frontend"
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(s,p):
        p=p.split('?')[0]
        if p.startswith('/chat/ui/'): return os.path.join(ROOT,p[len('/chat/ui/'):])
        return os.path.join(ROOT,p.lstrip('/'))
    def log_message(s,*a): pass
http.server.ThreadingHTTPServer(('127.0.0.1',8765),H).serve_forever()
