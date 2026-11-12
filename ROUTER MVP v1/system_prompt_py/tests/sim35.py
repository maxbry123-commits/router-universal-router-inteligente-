import sys, os, json, asyncio, tempfile, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, sys.argv[1])
import chat_ab_orchestrator as orch_mod
from code_splitter import split_code, NodeTooLargeError
SHARED = {}
class MemCache:
    def __init__(self, *a, **k): pass
    async def get(self, k): return SHARED.get(k)
    async def set(self, k, v, ttl_s=None): SHARED[k] = v
orch_mod.TempCache = MemCache
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"ok": true}')
    def log_message(self, *a): pass
srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["AGENT_HARNESS_URL"] = f"http://127.0.0.1:{srv.server_address[1]}/execute"
ok = True
def check(n, c, e=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{e}]" if e else ""))
class Seq:
    def __init__(self, outs): self.outs = list(outs); self.i = 0; self.prompts = []
    async def generate_raw_meta(self, prompt, session_id="default"):
        self.prompts.append(prompt)
        r = self.outs[min(self.i, len(self.outs)-1)]; self.i += 1
        return r if isinstance(r, tuple) else (r, "stop")
BIG = "import math\n\n" + "\n\n".join(f"def fn_{i}(x):\n    y = x + {i}\n    return math.floor(y)" for i in range(150))
BIG_JSON = json.dumps({"code": BIG, "tests": "def test_ok():\n    assert fn_0(1) == 1\n    assert fn_149(0) == 149\n"})
def make(outs):
    d = tempfile.mkdtemp(); os.chdir(d); os.environ["ORCHESTRATOR_WORKSPACE"] = os.path.join(d, "ws")
    os.environ["AGENT_HARNESS_URL"] = os.environ["AGENT_HARNESS_URL"]
    o = orch_mod.ChatABOrchestrator("plan-35", {"env": "sim"}); o.chat_b.adapter = Seq(outs); return o, d
async def main():
    print("=== A. division determinista ===")
    sp = split_code(BIG, 200, "block_1"); parts = sp["parts"]
    check("codigo de 450 LOC se divide en varias partes", len(parts) >= 3, f"partes={len(parts)}")
    check("cada parte <= 200 LOC", all(len(t.splitlines()) <= 200 for _, t in parts), str([len(t.splitlines()) for _, t in parts]))
    check("el agregador importa todas las partes", sp["aggregator"][1].count("import *") == len(parts))
    try: split_code("def big():\n" + "\n".join(f"    v{i} = {i}" for i in range(260)), 200, "block_x"); check("nodo unico de 260 LOC -> NodeTooLargeError", False)
    except NodeTooLargeError: check("nodo unico de 260 LOC -> NodeTooLargeError", True)
    print("=== B. parcial y reanudacion ===")
    SHARED.clear()
    o, _ = make([("{\"code\": \"def f():\\n    return 1", "length"), ("", "length"), ("", "length"), ("", "length")])
    try: await o.run("tarea parcial")
    except RuntimeError: pass
    check("respuesta cortada -> parcial guardado en checkpoint", "def f():" in o.checkpoint.get_partial("block_1"))
    o2 = orch_mod.ChatABOrchestrator("plan-35", {"env": "sim"})
    seq = Seq([("\\n\\n\\ndef f2():\\n    return 2\\n\", \"tests\": \"def test_ok():\\n    assert f() == 1\\n\"}", "stop")]); o2.chat_b.adapter = seq
    try: ev = await o2.run("tarea parcial")
    except RuntimeError as e: ev = {"final_status": f"ERR {e}"}
    done1 = "block_1" in [b["id"] for b in o2.checkpoint.state["completed_blocks"]]
    check("reintento incluye el parcial en el prompt y completa block_1", any("PARCIAL YA RECIBIDO" in p for p in seq.prompts) and done1, f"llamadas={len(seq.prompts)} block_1_ok={done1}")
    print("=== C. flujo completo con division y pytest ===")
    SHARED.clear()
    o3, d3 = make([BIG_JSON])
    ev3 = await o3.run("codigo grande")
    names = o3.checkpoint.state["parts"].get("block_1", [])
    check("bloque grande -> PASS con partes en checkpoint", ev3["final_status"] == "PASS" and len(names) >= 3, f"partes={len(names)} status={ev3['final_status']}")
    ws = os.path.join(d3, "ws")
    sizes = [len(open(os.path.join(ws, n + ".py")).read().splitlines()) for n in names]
    check("cada archivo generado <= 200 LOC", all(s <= 200 for s in sizes), str(sizes))
    b1 = [c for c in ev3["code"] if c["root_id"] == "block_1"]
    check("evidencia registra cada parte <= 200", all(c["loc"] <= 200 for c in ev3["code"]) and len(b1) == len(names), f"block_1 entries={len(b1)} names={len(names)}")
    check("pytest sobre el agregador pasa", any(t["status"] == "PASS" for t in ev3["tests"]))
    print("RESULTADO B35:", "TODO OK" if ok else "HAY FALLOS")
asyncio.run(main())
