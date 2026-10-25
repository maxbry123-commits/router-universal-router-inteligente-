"""Lista de cambios por commit (archivos y funciones añadidas/quitadas). Uso: python3 plugins/chat-router/e2e/cambios.py"""
import re, subprocess, pathlib
R = pathlib.Path(__file__).resolve().parents[3]
FN = re.compile(r'^[+-]\s*(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>|def\s+(\w+)|async def\s+(\w+))')


def git(*a):
    return subprocess.run(["git", *a], cwd=R, capture_output=True, text=True).stdout


def escribir(salida, titulo, rutas, filtro_ext):
    filas = git("log", "--reverse", "--format=%h|%ad|%an|%s", "--date=short", "--", *rutas).strip().splitlines()
    s = [f"# {titulo}\n\nGenerado por `plugins/chat-router/e2e/cambios.py` desde `git log`. Para auditar un cambio: `git show <commit> -- <archivo>`.\nColumnas: commit · fecha · autor · qué · archivos · funciones (+ añadidas / − quitadas).\n",
         f"Total de commits: **{len(filas)}**\n", "| Commit | Fecha | Autor | Cambio | Archivos | Funciones |", "|---|---|---|---|---|---|"]
    for l in filas:
        h, d, a, m = l.split("|", 3)
        arch = [x for x in git("show", "--format=", "--name-only", h, "--", *rutas).split() if x.endswith(filtro_ext)]
        mas, menos = [], []
        diff = git("show", "--format=", "-U0", h, "--", *rutas)
        for ln in diff.splitlines():
            if ln.startswith(("+++", "---")):
                continue
            mt = FN.match(ln)
            if mt:
                n = next(g for g in mt.groups() if g)
                (mas if ln[0] == "+" else menos).append(n)
        nuevos = sorted(set(mas) - set(menos))
        quitados = sorted(set(menos) - set(mas))
        fn = (("+" + ", +".join(nuevos[:8]) + (" …" if len(nuevos) > 8 else "")) if nuevos else "") + ((" · −" + ", −".join(quitados[:8])) if quitados else "")
        ar = ", ".join(f"`{pathlib.Path(x).name}`" for x in arch[:7]) + (f" … (+{len(arch) - 7})" if len(arch) > 7 else "")
        s.append(f"| `{h}` | {d} | {a} | {m[:150].replace('|', '/')} | {ar or '—'} | {fn or '—'} |")
    (R / salida).write_text("\n".join(s) + "\n")
    print(salida, len(filas))


escribir("docs/chat_frontend/CAMBIOS.md", "Cambios del FRONTEND del chat (todos los commits)", ["plugins/chat-router/frontend", "plugins/chat-router/e2e"], (".js", ".css", ".html", ".json", ".sh", ".mjs", ".py", ".md", "vercel.json"))
escribir("docs/chat_backend/CAMBIOS.md", "Cambios del BACKEND del chat (todos los commits)", ["mvp", "plugins/deepseek_harness", "plugins/router_api_cliente.py"], (".py", ".json", ".sh", ".md", ".txt"))
