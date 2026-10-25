"""Genera los indices de las dos raices del chat con commits reales. Uso: python3 plugins/chat-router/e2e/indice.py"""
import re, subprocess, pathlib
R = pathlib.Path(__file__).resolve().parents[3]
BASE = "1b916a587c"


def git(*a):
    return subprocess.run(["git", *a], cwd=R, capture_output=True, text=True).stdout


GRUPOS_FE = [
    ("Entradas y arranque", r"^(shell\.(js|html|css)|config\.js|version\.js|build\.sh|vercel\.json|panel-chat\.html|responsive\.css)$"),
    ("Núcleo del chat", r"^(panel-chat\.js|enviar-mensaje\.js|controles-chat\.js|buzon-proceso\.js|pildora-ficha\.js|chat-contexto\.js|contexto\.js|api\.js|api/.*|chat-espacio\.css|chat-movil\.css|chat-pulido\.css)$"),
    ("Composer y botones", r"^(composer-filas\.(js|css)|boton-enviar\.css|tools-ventana\.js|agregar-al-chat\.(js|css)|menu-habilidades\.js|habilidades\.css|pensando-3d\.(js|css)|chat-microfono\.js|chat-medios\.(js|css))$"),
    ("Selectores y modelos", r"^(chat-selectores\.js|chat-selector-modelos\.js|selects-secundarios\.js|selector-ancla\.js|selector-workflows\.js|selector-resp\.css|fichas-externas\.js|mode_selector\.js|modes_registry\.json|agentes-mirror\.js|ventana-motor\.js)$"),
    ("Anclas, proyecto y pendientes", r"^(chat-ancla\.js|anclaje-.*|objetivos-ancla\.js|proyecto\.js|pendientes-panel\.js|handoff-editor\.js)$"),
    ("Ventanas", r"^(ventana.*|ventanas-.*|notas-ventana\.js|canvas-visor\.js|acceso-clave\..*|bloqueo-pin\.js|ventana-.*\.css)$"),
    ("Componentes RIU/RUI", r"^(riu-.*|chat-riu.*|shell-riu\.css|paneles-reales\.css|encendido\.css)$"),
    ("Paneles de la shell", r"^(panel-(archivos|canvas|org|seguimiento|apariencia).*|almacen.*|archivos-borrar\.js|seguimiento-real\.js)$"),
    ("Apariencia y temas", r"^(apariencia-.*|temas-nuevos\.css|panel-apariencia.*)$"),
]
GRUPOS_BE = [
    ("Servidor y rutas", r"^(app|run|config|prompt|trabajos|escalado)\.(py|json)$"),
    ("Permisos y seguridad", r"^(control|bank)\.py$"),
    ("Modelos y proveedores", r"^(modelos|compute|externos|sdk_qwen|multimedia)\.(py|json)$"),
    ("MCP y herramientas", r"^(mcp_route|mcp_cliente|harness_client|sala_turno)\.py$"),
    ("Persistencia y memoria", r"^(hf_store|memoria)\.py$"),
]


def grupo(n, tabla):
    for g, rx in tabla:
        if re.match(rx, n):
            return g
    return "Otros"


def info(path):
    l = git("log", "--format=%h|%an", "--", path).strip().splitlines()
    desde = git("log", "--format=%h", f"{BASE}..HEAD", "--", path).split()
    return (l[0].split("|") if l else ["-", "-"]), len(l), len(desde)


def tabla(arch, base, grupos, titulo):
    por = {}
    for p in arch:
        por.setdefault(grupo(p.relative_to(base).as_posix(), grupos), []).append(p)
    s = [f"## {titulo}\n"]
    for g in [x[0] for x in grupos] + ["Otros"]:
        if g not in por:
            continue
        s.append(f"### {g} ({len(por[g])})\n\n| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |\n|---|--:|---|---|--:|--:|")
        for p in sorted(por[g]):
            (h, a), n, d = info(str(p.relative_to(R)))
            try:
                ln = sum(1 for _ in p.open(errors="ignore"))
            except Exception:
                ln = 0
            s.append(f"| `{p.relative_to(base).as_posix()}` | {ln} | `{h}` | {a} | {n} | {d} |")
        s.append("")
    return "\n".join(s)


FE = R / "plugins/chat-router/frontend"
fe_files = [p for p in FE.rglob("*") if p.is_file() and "yaiwes" not in p.parts and "test" not in p.parts and "__pycache__" not in p.parts]
BE = R / "mvp"
be_files = [p for p in BE.glob("*") if p.is_file() and not p.name.startswith("test_") and p.suffix in (".py", ".json")]
be_files += [R / "plugins/deepseek_harness/server.py", R / "plugins/router_api_cliente.py"]
be_tests = sorted(BE.glob("test_*.py"))

(R / "docs/chat_frontend").mkdir(exist_ok=True)
(R / "docs/chat_backend").mkdir(exist_ok=True)
(R / "docs/chat_frontend/INDICE.md").write_text(
    "# Raíz FRONTEND del chat — índice de archivos\n\nCarpeta real: `plugins/chat-router/frontend/` (no se movió: Vercel, `build.sh` y los imports dependen de esa ruta). Pruebas: `plugins/chat-router/e2e/`.\nGenerado por `plugins/chat-router/e2e/indice.py` (commits reales de `git log`). Base de comparación: `" + BASE + "`.\n\n"
    + tabla(fe_files, FE, GRUPOS_FE, "Archivos") + "\n")
bt = ["## Pruebas del backend\n", "| Archivo | Líneas | Último commit | Autor |\n|---|--:|---|---|"]
for p in be_tests:
    (h, a), n, d = info(str(p.relative_to(R)))
    bt.append(f"| `mvp/{p.name}` | {sum(1 for _ in p.open())} | `{h}` | {a} |")
(R / "docs/chat_backend/INDICE.md").write_text(
    "# Raíz BACKEND del chat — índice de archivos\n\nCarpeta real: `mvp/` (Router FastAPI) + `plugins/deepseek_harness/server.py` (Harness) + `plugins/router_api_cliente.py`. No se movió: el Space y el autopull arrancan `mvp.run`.\nGenerado por `plugins/chat-router/e2e/indice.py`. Base: `" + BASE + "`.\n\n"
    + tabla(be_files, R, [(g, r"^mvp/" + rx[1:]) for g, rx in GRUPOS_BE] + [("Harness y cliente", r"^plugins/")], "Archivos") + "\n" + "\n".join(bt) + "\n")
print(len(fe_files), len(be_files), len(be_tests))
