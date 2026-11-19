#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador del auto-pull (FAIL_CLOSED). Ejecutar: python3 scripts/verify_auto_pull.py"""
import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTO = ROOT / "external" / "core" / "auto_pull.py"
PROXY = ROOT / "ROUTER MVP v1" / "system_prompt_py" / "openai_compatible_proxy.py"
MGR = ROOT / "llm system HF" / "manager_v2.py"
FALLOS = []


def check(nombre, cond, detalle=""):
    print("  %-26s %s %s" % (nombre, "PASS" if cond else "FAIL", detalle))
    if not cond:
        FALLOS.append(nombre)


def load_auto():
    spec = importlib.util.spec_from_file_location("auto_pull_test", AUTO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    # V1 V2
    check("V1 auto_pull existe", AUTO.is_file(), str(AUTO.stat().st_size) + " B")
    src = AUTO.read_text(encoding="utf-8")
    check("V2 py_compile", subprocess.call([sys.executable, "-m", "py_compile", str(AUTO)]) == 0)
    check("V3 fetch+reset+execv", all(k in src for k in
          ('"fetch", "--depth", "1"', '"reset", "--hard"', "os.execv")))
    mod = load_auto()

    # V4 fail-closed: sin clon no toca nada
    os.environ["AUTO_PULL_REPO_DIR"] = "/tmp/no-existe-este-repo"
    r = mod.poll_once()
    check("V4 fail-closed sin repo", (not r.get("ok")) and ("no hay clon" in (r.get("error") or "")))
    del os.environ["AUTO_PULL_REPO_DIR"]

    # V5 el hook post-reset re-aplica el parche --reasoning off
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "llm system HF").mkdir()
        mgr = root / "llm system HF" / "manager_v2.py"
        mgr.write_text('cmd = ["llama-server", "--n-gpu-layers", "0"]\n', encoding="utf-8")
        done = mod._post_reset_hooks(root)
        txt = mgr.read_text(encoding="utf-8")
        check("V5 hook reasoning-off", "reasoning_off" in done and '"--reasoning", "off"' in txt)

    # V6 las 3 raices con su origen real
    reg = json.loads((ROOT / "router_llm_hf" / "AGENTS_REGISTRY.json").read_text(encoding="utf-8"))
    roots = set(reg.get("roots") or {})
    check("V6 3 raices del registro", roots == set(mod.ROOT_SOURCES), ",".join(sorted(roots)))
    check("V7 origen ruflo/rowboat", mod.ROOT_SOURCES["ruflo"]["repo"] == "ruvnet/ruflo"
          and mod.ROOT_SOURCES["rowboat"]["pinned_commit"].startswith("d31c0381"))

    # V8 proxy: arranca el watcher + expone estado
    ps = PROXY.read_text(encoding="utf-8")
    check("V8 proxy cableado", "_arranca_auto_pull()" in ps and "/v1/auto-pull" in ps
          and '"auto_pull": (AUTO_PULL.status()' in ps)

    # V9 manager: arranca el watcher con on_reload que mata llama-server
    ms = MGR.read_text(encoding="utf-8")
    check("V9 manager cableado", "_reload_matar_llama" in ms
          and "_mod.start(on_reload=_reload_matar_llama)" in ms
          and '"auto_pull": (AUTO_PULL.status()' in ms)

    # V10 el manager mata el llama-server ANTES de execv
    tree = ast.parse(ms)
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_reload_matar_llama"), None)
    cuerpo = ast.dump(fn) if fn else ""
    check("V10 kill antes de execv", fn is not None and "SIGTERM" in cuerpo and "execv" in cuerpo)

    # V11 nunca se escribe la URL del remoto (lleva el token)
    check("V11 sin URL con token", "x-access-token" not in src and "@github.com" not in src.replace(
        "https://github.com/{repo}.git", ""))

    # V12 sin secretos en los ficheros tocados
    secretos = []
    for f in (AUTO, PROXY, MGR):
        t = f.read_text(encoding="utf-8")
        for pat in ("770361793Max", "nvapi-", "gsk_", "sk-sp-"):
            if pat in t:
                secretos.append("%s:%s" % (f.name, pat))
    check("V12 sin secretos", not secretos, ",".join(secretos))

    # V13 idempotencia del parche
    before = (PROXY.read_bytes(), MGR.read_bytes())
    rc = subprocess.run([sys.executable, "/workspace/patch_auto_pull_wiring.py"],
                        capture_output=True).returncode
    after = (PROXY.read_bytes(), MGR.read_bytes())
    check("V13 parche idempotente", rc == 0 and before == after)

    if FALLOS:
        print("AUTO_PULL_VERIFY FAIL: %s" % ",".join(FALLOS))
        return 1
    print("AUTO_PULL_VERIFY OK (13 checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
