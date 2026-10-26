"""Guardia de lo cableado: falla si algo protegido cambió, falta o un enlace no resuelve.
Uso: python3 chat/auditoria/guardia_cableado.py [--crear]   (sin GitHub Actions: solo git y Python)
Compara contra chat-router/cableado.manifest.json:
  1) protegido: huella (sha256) de `git ls-files -s` de cada ruta protegida (los blobs de git = contenido exacto) y que el árbol de trabajo no tenga cambios ahí;
  2) enlaces protegidos: existen y apuntan a donde apuntaban;
  3) plugins/: cada entrada del manifiesto sigue existiendo, resuelve y conserva su ficha.json (el cargador descubre por nombre de carpeta)."""
import hashlib, json, os, pathlib, subprocess, sys
R = pathlib.Path(__file__).resolve().parents[2]
M = R / "chat-router" / "cableado.manifest.json"
PROTEGIDO = ["chat/backend", "chat/frontend", "chat/e2e", "chat/auditoria", "chat/espejo", "router", "fichas", "raiz_router", "raiz_fichas_prompt", "plugins/puente_chat", "plugins/hf_storage", "plugins/__init__.py", "CLAUDE.md"]
ENLACES = ["mvp", "plugins/deepseek_harness", "plugins/router_api_cliente.py", "chat-router/chat", "chat-router/harness"]


def git(*a):
    return subprocess.run(["git", *a], cwd=R, capture_output=True, text=True).stdout


def huella(ruta):
    s = git("ls-files", "-s", "--", ruta)
    return hashlib.sha256(s.encode()).hexdigest(), len(s.splitlines())


def plugins():
    d = R / "plugins"; out = {}
    for p in sorted(d.iterdir()):
        if p.name.startswith(("__", ".")):
            continue
        ficha = (p / "ficha.json").exists() if p.is_dir() else False
        if ficha or p.is_symlink():  # solo lo que el cargador descubre (ficha.json) o ya es un enlace de compatibilidad
            out[p.name] = {"enlace": p.is_symlink(), "destino": os.readlink(p) if p.is_symlink() else "", "ficha": ficha}
    return out


def crear():
    m = {"protegido": {r: dict(zip(("sha256", "archivos"), huella(r))) for r in PROTEGIDO},
         "enlaces": {e: os.readlink(R / e) for e in ENLACES if (R / e).is_symlink()}, "plugins": plugins()}
    M.write_text(json.dumps(m, indent=1, ensure_ascii=False, sort_keys=True) + "\n"); print("manifiesto creado:", M.relative_to(R), len(m["protegido"]), "rutas protegidas,", len(m["plugins"]), "plugins")


def revisar():
    m = json.loads(M.read_text()); fallos = []
    for r, v in m["protegido"].items():
        h, n = huella(r)
        if h != v["sha256"]: fallos.append(f"CAMBIÓ lo protegido: {r} ({v['archivos']} → {n} archivos)")
        if git("status", "--porcelain", "--", r).strip(): fallos.append(f"CAMBIOS sin guardar en lo protegido: {r}")
    for e, destino in m["enlaces"].items():
        p = R / e
        if not p.is_symlink() or os.readlink(p) != destino or not p.resolve().exists(): fallos.append(f"ENLACE roto o distinto: {e} → {destino}")
    ahora = plugins()
    for nombre, v in m["plugins"].items():
        a = ahora.get(nombre)
        if a is None: fallos.append(f"FALTA plugins/{nombre}"); continue
        if not (R / "plugins" / nombre).resolve().exists(): fallos.append(f"plugins/{nombre} no resuelve")
        if v["ficha"] and not a["ficha"]: fallos.append(f"plugins/{nombre} perdió su ficha.json")
    for f in fallos: print("FAIL:", f)
    print(("GUARDIA FAIL=%d" % len(fallos)) if fallos else "GUARDIA OK: %d rutas protegidas intactas, %d enlaces y %d plugins presentes" % (len(m["protegido"]), len(m["enlaces"]), len(m["plugins"])))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--crear" in sys.argv: crear()
    else: sys.exit(revisar())
