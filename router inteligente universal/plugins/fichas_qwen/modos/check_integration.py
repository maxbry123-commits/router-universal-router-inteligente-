#!/usr/bin/env python3
"""Verifica la integracion de modos en TU repo del chat (determinista, FAIL-CLOSED).
Uso: python3 check_integration.py /ruta/al/repo-del-chat
Comprueba: pares >>> MODOS BEGIN / <<< MODOS END balanceados, al menos 1 por capa (front y back),
y que los 5 archivos del paquete esten copiados. No modifica nada."""
import os, re, sys

BEGIN = re.compile(r">>>\s*MODOS BEGIN")
END = re.compile(r"<<<\s*MODOS END")
EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".vue", ".svelte"}
SKIP = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv"}
PACKAGE = ["modes_registry.json", "research_sources.json", "mode_router.py", "validate_modes.py", "mode_selector.js"]

def main():
    if len(sys.argv) < 2:
        print("VEREDICTO: FAIL - falta ruta del repo"); sys.exit(1)
    root = sys.argv[1]
    errs, touched, found = [], {}, set()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f in PACKAGE:
                found.add(f)
            if os.path.splitext(f)[1] not in EXTS or f in PACKAGE:
                continue
            p = os.path.join(dp, f)
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            b, e = len(BEGIN.findall(t)), len(END.findall(t))
            if b or e:
                touched[p] = (b, e)
                if b != e:
                    errs.append(f"marcadores desbalanceados en {p}: BEGIN={b} END={e}")
    for f in PACKAGE:
        if f not in found:
            errs.append(f"archivo del paquete no encontrado en el repo: {f}")
    if not touched:
        errs.append("no hay ningun bloque MODOS BEGIN/END: la integracion no se aplico")
    back = [p for p in touched if p.endswith(".py")]
    front = [p for p in touched if os.path.splitext(p)[1] in {".js", ".jsx", ".ts", ".tsx", ".html", ".vue", ".svelte"}]
    if not back: errs.append("falta integracion en el BACKEND (.py)")
    if not front: errs.append("falta integracion en el FRONTEND")
    if errs:
        print("VEREDICTO: FAIL")
        for x in errs: print(" -", x)
        sys.exit(1)
    print("VEREDICTO: PASS")
    for p, (b, _) in sorted(touched.items()):
        print(f" - {p}: {b} bloque(s)")

if __name__ == "__main__":
    main()
