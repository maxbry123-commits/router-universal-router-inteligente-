"""Auditoria de cableado del chat (solo lectura). Uso: python3 plugins/chat-router/e2e/cableado.py [--json]
Raiz FRONTEND: plugins/chat-router/frontend   Raiz BACKEND: mvp + plugins/deepseek_harness + plugins/router_api_cliente.py
Comprueba: imports resueltos, modulos huerfanos, sintaxis, endpoints del frontend contra rutas del backend,
rutas/herramientas MCP del backend contra pruebas, ids del DOM usados por el JS."""
import re, subprocess, sys, json, pathlib

R = pathlib.Path(__file__).resolve().parents[3]
FE = R / "plugins/chat-router/frontend"
BE = R / "mvp"
out = {"FAIL": [], "AVISO": [], "OK": []}


def f(k, m):
    out[k].append(m)


# ---------- FRONTEND ----------
js = sorted(p for p in FE.glob("*.js"))
names = {p.name for p in FE.iterdir()}
imp = re.compile(r'(?:from\s+|import\s*\(\s*|import\s+)["\']([^"\']+)["\']')
grafo = {}
for p in js:
    t = p.read_text(errors="ignore")
    deps = set()
    for m in imp.finditer(t):
        s = m.group(1).split("?")[0]
        if s.startswith("/chat/ui/"):
            s = s[len("/chat/ui/"):]
        elif s.startswith("./"):
            s = s[2:]
        else:
            continue
        deps.add(s)
        if s not in names and not (FE / s).exists():
            f("FAIL", f"FE import roto: {p.name} -> {s}")
    grafo[p.name] = deps
html_txt = "".join(h.read_text(errors="ignore") for h in FE.glob("*.html"))
entradas = set(re.findall(r'/chat/ui/([\w.\-]+\.js)', html_txt))
entradas |= {"shell.js", "config.js", "version.js"}
vistos, pila = set(), list(entradas)
while pila:
    n = pila.pop()
    if n in vistos:
        continue
    vistos.add(n)
    pila += list(grafo.get(n, []))
# modulos cargados por nombre desde shell/otros (cadenas con .js)
dinam = set()
for p in js:
    dinam |= set(re.findall(r'["\']([\w\-]+\.js)["\']', p.read_text(errors="ignore")))
huerf = [p.name for p in js if p.name not in vistos and p.name not in dinam]
for h in huerf:
    f("AVISO", f"FE modulo sin enlazar desde ninguna entrada: {h}")
for p in js:
    r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
    if r.returncode:
        f("FAIL", f"FE sintaxis: {p.name}: {r.stderr.strip().splitlines()[0] if r.stderr else ''}")
f("OK", f"FE: {len(js)} modulos .js, {len(vistos)} alcanzables, sintaxis revisada")

# endpoints usados por el frontend
usados = {}
for p in js:
    for m in re.finditer(r'["\'`](/(?:chat|almacen|health|mcp|memoria|plugins|api|vault)[\w/\-{}$.]*)', p.read_text(errors="ignore")):
        usados.setdefault(m.group(1).rstrip("/"), set()).add(p.name)

# ---------- BACKEND ----------
rutas = set()
for p in BE.glob("*.py"):
    if p.name.startswith("test_"):
        continue
    t = p.read_text(errors="ignore")
    for m in re.finditer(r'@\w+\.(?:get|post|put|delete)\(\s*["\'](/[^"\']*)', t):
        rutas.add(m.group(1))
    for m in re.finditer(r'add_api_route\(\s*[\'"](/[^\'"]*)', t):
        rutas.add(m.group(1))
rutas |= {"/memoria/save", "/memoria/load", "/memoria/search"}
rx = [re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", r) + "$") for r in rutas]
vercel = (FE / "vercel.json").read_text()
for u, quien in sorted(usados.items()):
    base = u.split("$")[0].split("{")[0].rstrip("/") or u
    ok = any(x.match(u) or x.match(base) for x in rx) or any(r.startswith(base) for r in rutas)
    if u.startswith("/chat/ui") or u in ("/api/power", "/api"):
        ok = True  # estatico del propio Vercel / funcion de Vercel
    if u.startswith("/plugins") or u.startswith("/vault"):
        ok = True  # rewrite de Vercel al Router
    if not ok:
        f("AVISO", f"Endpoint usado por FE sin ruta en el Router (mvp): {u}  <- {', '.join(sorted(quien))}")
f("OK", f"Rutas del Router: {len(rutas)}; endpoints distintos usados por FE: {len(usados)}")

# MCP: herramientas contra pruebas
mcp = (BE / "mcp_route.py").read_text()
tools = set(re.findall(r"['\"](\w+)['\"]\s*:\s*\{['\"]description", mcp)) or set(re.findall(r"\bname['\"]?\s*[:=]\s*['\"](\w+)['\"]", mcp))
tests = "".join(p.read_text(errors="ignore") for p in BE.glob("test_*.py")) + "".join(p.read_text(errors="ignore") for p in (BE / "pruebas_vivo").glob("*.py"))
for t in sorted(tools):
    if t not in tests:
        f("AVISO", f"Herramienta MCP sin prueba que la nombre: {t}")
f("OK", f"MCP: {len(tools)} herramientas detectadas")
for r in sorted(rutas):
    clave = r.split("{")[0].rstrip("/")
    if clave and clave not in tests:
        f("AVISO", f"Ruta sin prueba que la nombre: {r}")
# modulos backend con prueba
for p in sorted(BE.glob("*.py")):
    if p.name.startswith("test_") or p.name in ("__init__.py",):
        continue
    if not (BE / f"test_{p.stem}.py").exists() and p.stem not in tests.replace("from mvp import ", ""):
        f("AVISO", f"Modulo backend sin prueba: {p.name}")
r = subprocess.run([sys.executable, "-c", "import mvp.app, mvp.mcp_route, mvp.memoria, mvp.externos, mvp.control, mvp.bank, mvp.hf_store"], capture_output=True, text=True, cwd=R)
f("OK" if r.returncode == 0 else "FAIL", "BE importa app/mcp/memoria/externos/control/bank/hf_store" if r.returncode == 0 else "BE import: " + r.stderr[-300:])

# ids del DOM usados por JS
ids_def = set(re.findall(r'\bid=["\']([\w\-]+)', html_txt))
for p in js:
    t = p.read_text(errors="ignore")
    ids_def |= set(re.findall(r'\bid=\\?["\']([\w\-]+)', t)) | set(re.findall(r'\.id\s*=\s*["\']([\w\-]+)', t)) | set(re.findall(r'\bid:\s*["\']([\w\-]+)', t))
sin = {}
for p in js:
    for m in re.finditer(r'getElementById\(\s*["\']([\w\-]+)["\']', p.read_text(errors="ignore")):
        if m.group(1) not in ids_def:
            sin.setdefault(m.group(1), set()).add(p.name)
for i, q in sorted(sin.items()):
    f("AVISO", f"id del DOM pedido y no definido en ningun html/js: #{i} <- {', '.join(sorted(q))}")

if "--json" in sys.argv:
    print(json.dumps(out, indent=1, ensure_ascii=False))
else:
    for k in ("FAIL", "AVISO", "OK"):
        for m in out[k]:
            print(f"{k}: {m}")
    print(f"RESUMEN FAIL={len(out['FAIL'])} AVISO={len(out['AVISO'])} OK={len(out['OK'])}")
sys.exit(1 if out["FAIL"] else 0)
