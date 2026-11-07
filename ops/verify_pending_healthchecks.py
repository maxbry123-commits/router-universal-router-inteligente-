"""ops/verify_pending_healthchecks.py — cierra las verificaciones pendientes en el clon completo.

D-55: seis conexiones quedaban como `pending_verificacion` porque el clon de trabajo local
es sparse (no materializa sus modulos). Se verifican en el clon completo (el que usa la
cadena para los lotes) y, si responden, pasan a `active` con la evidencia de la ejecucion.

Uso: python ops/verify_pending_healthchecks.py <ruta_clon_completo>
"""
import os, pathlib, subprocess, sys
import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
CLONE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"r2")

PEND = {
    "CON-007": ("chat-router", "plugins.router_api_cliente"),
    "CON-008": ("chat-router", "agentes.adaptadores.modelos"),
    "CON-021": ("chat-router", "plugins.puente_chat.plugin"),
    "CON-022": ("chat-router", "agentes.adaptadores"),
    "CON-026": ("chat-router", "plugins"),
    "CON-037": ("router-mvp", "fichas.fichas_qwen.plugin"),
}


def run_import(root, module):
    code = "import sys;sys.path.insert(0,%r);import %s" % (root, module)
    p = subprocess.run([sys.executable, "-c", code], cwd=CLONE, capture_output=True, text=True, timeout=300)
    return p.returncode == 0, ((p.stderr or "").strip().splitlines() or [""])[-1][:300]


def main():
    if not pathlib.Path(CLONE).is_dir():
        print("clon completo no disponible:", CLONE)
        return 1
    res = {}
    for cid, (root, mod) in PEND.items():
        ok, err = run_import(root, mod)
        res[cid] = (root, mod, ok, err)
        print(f"{cid} {'OK' if ok else 'FAIL'} {root} -> {mod} {err[:90]}")

    hcp = REPO / "connections" / "healthchecks.yaml"
    hcd = yaml.safe_load(open(hcp))
    for h in hcd["healthchecks"]:
        cid = h.get("connection")
        if cid in res:
            root, mod, ok, err = res[cid]
            h["status"] = "verified" if ok else "failing"
            h["command"] = f"python -c \"import sys;sys.path.insert(0,'{root}');import {mod}\""
            h["evidence"] = f"verificado en el clon completo ({CLONE}): import ok" if ok else err
            h["verified_in"] = CLONE
    with open(hcp, "w") as f:
        f.write("# connections/healthchecks.yaml — verificación real por conexión (§5/§8).\n")
        f.write("# Generado por ops/make_healthchecks.py y cerrado por ops/verify_pending_healthchecks.py:\n")
        f.write("# cada comando se EJECUTA y su resultado decide el estado. \"sin healthcheck no hay activo\".\n")
        yaml.safe_dump(hcd, f, sort_keys=False, allow_unicode=True, width=1000)

    rgp = REPO / "connections" / "registry.yaml"
    rg = yaml.safe_load(open(rgp))
    for c in rg["connections"]:
        cid = c["id"]
        if cid in res:
            root, mod, ok, err = res[cid]
            c["status"] = "active" if ok else "broken"
            c["evidence"] = {
                "type": "import",
                "command": f"python -c \"import sys;sys.path.insert(0,'{root}');import {mod}\"",
                "result": "ok", "verified_in": CLONE,
                "detail": "import ejecutado: el modulo carga y se importa sin error",
            }
            c["verification"] = {
                "type": "import", "root": root, "module": mod,
                "command": f"python -c \"import sys;sys.path.insert(0,'{root}');import {mod}\"",
                "result": "ok" if ok else "error",
                "verified_in": CLONE,
                "detail": None if ok else err,
            }
    with open(rgp, "w") as f:
        yaml.safe_dump(rg, f, sort_keys=False, allow_unicode=True, width=1000)

    from collections import Counter
    print("registry:", Counter(c["status"] for c in rg["connections"]))
    print("healthchecks:", Counter(h["status"] for h in hcd["healthchecks"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
