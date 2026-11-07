"""ops/make_healthchecks.py — healthcheck real por conexion con canal real (§5/§8).

Regla de la guia: "sin healthcheck no hay activo". Para cada conexion con canal real
documentado en la auditoria (import in-proc verificable), se deriva un comando de
import real a partir del fichero destino de la arista, se EJECUTA y se registra el
resultado. Solo pasan a `active` las que su healthcheck responde.

Uso: python ops/make_healthchecks.py [--dry]
"""
import os, re, subprocess, sys, json, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
AUDIT = pathlib.Path('/workspace/output/auditoria-registry-38-conexiones.md')
DRY = '--dry' in sys.argv

CANDIDATE_ROOTS = [".", "chat-router", "chat-router/chat", "router-mvp", "chat-router/chat/backend", "ops"]

# id -> (raiz_relativa, modulo) deducidos del fichero destino de la arista documentada
CHANNELS = {
    "CON-005": ("router-mvp", "router.integration.chat_mvp.core"),
    "CON-006": (".", "kernel"),
    "CON-007": ("chat-router", "plugins.router_api_cliente"),
    "CON-008": ("chat-router", "agentes.adaptadores.modelos"),
    "CON-010": ("router-mvp", "router.mcp_puente_github"),
    "CON-018": ("chat-router/chat", "backend.mvp.herramientas.modos"),
    "CON-020": ("router-mvp", "router.red.http_plugins"),
    "CON-021": ("chat-router", "plugins.puente_chat.plugin"),
    "CON-022": ("chat-router", "agentes.adaptadores"),
    "CON-023": ("chat-router/chat", "backend.mvp.prompt"),
    "CON-026": ("chat-router", "plugins"),
    "CON-028": ("router-mvp", "router.integration.chat_mvp.swen_mcp"),
    "CON-036": ("chat-router", "backend.mvp"),
    "CON-037": ("router-mvp", "fichas.fichas_qwen.plugin"),
}
# conexiones con gateway real (no import) comprobables por HTTP
HTTP_CHANNELS = {
    "CON-003": {"method": "http", "target": "GET /health del Harness", "expect": {"status": 200}},
}


# fichero real en el arbol git de cada modulo (para distinguir "no cableado" de "no esta en el clon sparse")
PATHS = {
    "plugins.router_api_cliente": "chat-router/plugins/router_api_cliente.py",
    "agentes.adaptadores.modelos": "chat-router/agentes/adaptadores/modelos.py",
    "plugins.puente_chat.plugin": "chat-router/plugins/puente_chat/plugin.py",
    "agentes.adaptadores": "chat-router/agentes/adaptadores/__init__.py",
    "plugins": "chat-router/plugins/__init__.py",
    "router.integration.chat_mvp.swen_mcp": "router-mvp/router/integration/chat_mvp/swen_mcp.py",
    "fichas.fichas_qwen.plugin": "router-mvp/fichas/fichas_qwen/plugin.py",
    "router.integration.chat_mvp.core": "router-mvp/router/integration/chat_mvp/core.py",
    "kernel": "ops/kernel.py",
    "router.mcp_puente_github": "router-mvp/router/mcp_puente_github.py",
    "backend.mvp.herramientas.modos": "chat-router/chat/backend/mvp/herramientas/modos/__init__.py",
    "router.red.http_plugins": "router-mvp/router/red/http_plugins.py",
    "backend.mvp.prompt": "chat-router/chat/backend/mvp/prompt.py",
    "backend.mvp": "chat-router/chat/backend/mvp/__init__.py",
}


def in_git_tree(path):
    """True si el fichero existe en el arbol de la rama actual (aunque no este en el working tree)."""
    r = subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"], cwd=str(REPO),
                       capture_output=True, text=True)
    return r.returncode == 0


def run_import(root, module):
    code = "import sys;sys.path.insert(0,%r);import %s" % (root, module)
    p = subprocess.run([sys.executable, "-c", code], cwd=str(REPO), capture_output=True, text=True, timeout=120)
    return p.returncode == 0, (p.stderr or "").strip().splitlines()[-1] if p.stderr.strip() else ""


def main():
    results = {}
    for cid, (root, module) in CHANNELS.items():
        ok, err = run_import(root, module)
        # si falla con la raiz prevista, se prueban las alternativas declaradas
        if not ok:
            for alt in CANDIDATE_ROOTS:
                if alt == root:
                    continue
                ok2, err2 = run_import(alt, module)
                if ok2:
                    ok, err, root = True, "", alt
                    break
        path = PATHS.get(module)
        en_arbol = in_git_tree(path) if path else None
        if not ok and en_arbol:
            # el modulo existe en el repo: el fallo es del clon sparse, no del cableado
            estado = "pending_verificacion_full_clone"
        elif not ok:
            estado = "broken"
        else:
            estado = "verified"
        results[cid] = {"root": root, "module": module, "ok": ok, "error": err,
                        "path": path, "en_arbol": en_arbol, "estado": estado}
        print(f"{cid} {'OK ' if ok else 'FAIL'} root={root} module={module} {err[:90]}")

    if DRY:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # --- healthchecks.yaml ---
    hc = {"healthchecks": []}
    existing = {"HC-001": ("CON-003", "http", "plugins -> harness"),
                "HC-002": ("CON-005", "mcp", "chat -> harness"),
                "HC-003": ("CON-007", "http", "backend -> agents"),
                "HC-004": ("CON-008", "space", "repo -> Space")}
    n = 1
    for cid, (root, module) in CHANNELS.items():
        r = results[cid]
        hc["healthchecks"].append({
            "id": f"HC-{n:03d}", "connection": cid, "method": "import",
            "target": f"{root} -> {module}",
            "command": f"python -c \"import sys;sys.path.insert(0,'{root}');import {module}\"",
            "expect": {"import_ok": True},
            "status": r["estado"],
            "evidence": (None if r["ok"] else
                         (f"modulo presente en el arbol git ({r['path']}); el clon sparse local no lo materializa"
                          if r["estado"] == "pending_verificacion_full_clone" else r["error"][:300])),
        })
        n += 1
    # los 4 healthchecks heredados de la guia se conservan como declared (sin ejecucion propia)
    for hid, (cid, method, target) in existing.items():
        hc["healthchecks"].append({
            "id": hid, "connection": cid, "method": method, "target": target,
            "command": None, "expect": {}, "status": "declared_heredado",
        })

    path = REPO / "connections" / "healthchecks.yaml"
    with open(path, "w") as f:
        f.write("# connections/healthchecks.yaml — verificación real por conexión (§5/§8).\n")
        f.write("# Generado por ops/make_healthchecks.py: un healthcheck por conexión con canal real;\n")
        f.write('# el comando se EJECUTA y su resultado decide el estado. "sin healthcheck no hay activo".\n')
        yaml_dump(hc, f)

    # --- registry.yaml: status + verification de las que responden ---
    reg = load_yaml(REPO / "connections" / "registry.yaml")
    by_id = {c["id"]: c for c in reg["connections"]}
    for cid, r in results.items():
        c = by_id.get(cid)
        if not c:
            continue
        if r["ok"]:
            c["status"] = "active"
            c["evidence"] = {
                "type": "import",
                "command": f"python -c \"import sys;sys.path.insert(0,'{r['root']}');import {r['module']}\"",
                "result": "ok", "verified_in": "clon local",
                "detail": "import ejecutado: el modulo carga y se importa sin error",
            }
            c["verification"] = {
                "type": "import", "root": r["root"], "module": r["module"],
                "command": f"python -c \"import sys;sys.path.insert(0,'{r['root']}');import {r['module']}\"",
                "result": "ok", "checked_at": os.environ.get("RUN_ID", "20261104-kernel01"),
            }
        else:
            # D-108: 'pending_verificacion' NO es un estado valido del registro
            # (validos: pending_audit|active|broken) y rompe 'registry_valid' (F04).
            # Un modulo presente en el arbol pero no materializado es 'pending_audit'.
            c["status"] = "pending_audit" if r["estado"] == "pending_verificacion_full_clone" else "broken"
            c["verification"] = {"type": "import", "root": r["root"], "module": r["module"],
                                 "path": r["path"], "en_arbol_git": r["en_arbol"],
                                 "result": "pending_full_clone" if r["estado"] == "pending_verificacion_full_clone" else "error",
                                 "detail": (r["error"] or "")[:300]}
    dump_yaml(reg, REPO / "connections" / "registry.yaml")
    ok_n = sum(1 for r in results.values() if r["ok"])
    pend = sum(1 for r in results.values() if r["estado"] == "pending_verificacion_full_clone")
    brk = sum(1 for r in results.values() if r["estado"] == "broken")
    print(f"healthchecks: {len(hc['healthchecks'])} | active (import ejecutado ok): {ok_n} | "
          f"pendientes (modulo en el arbol, falta clon completo): {pend} | broken: {brk}")


def load_yaml(p):
    import yaml
    return yaml.safe_load(open(p))


def dump_yaml(obj, p):
    import yaml
    with open(p, "w") as f:
        yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, width=1000)


def yaml_dump(obj, f):
    import yaml
    yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, width=1000)


if __name__ == "__main__":
    main()
