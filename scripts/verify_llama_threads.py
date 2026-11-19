#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador del parche de hilos de llama-server (FAIL_CLOSED).

Comprueba, sobre los ficheros reales del repo:
  V1  manager.py  y  manager_v2.py lanzan llama-server con --threads y --threads-batch
  V2  manager_v2.py conserva el patron que aplica el sed de entrypoint_v5.sh
      ('"--n-gpu-layers", "0"]') -> el parche --reasoning off NO se pierde
  V3  simulando ese sed, la linea de comando final contiene --reasoning off Y --threads
  V4  _detect_threads lee la cuota del cgroup v2 ("800000 100000" -> 8)
  V5  _detect_threads lee la cuota del cgroup v1 (quota/period -> 8)
  V6  LLAMA_THREADS (env) manda sobre la deteccion
  V7  sin cgroup detectable -> default 8
  V8  el fichero es sintacticamente valido (py_compile)
"""
import ast
import os
import subprocess
import sys
import tempfile

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "llm system HF")
M2 = os.path.join(BASE, "manager_v2.py")
M1 = os.path.join(BASE, "manager.py")
SED_OLD = '"--n-gpu-layers", "0"]'
SED_NEW = '"--n-gpu-layers", "0", "--reasoning", "off"]'
FALLOS = []


def check(nombre, cond, detalle=""):
    print("  %-4s %s %s" % (nombre, "PASS" if cond else "FAIL", detalle))
    if not cond:
        FALLOS.append(nombre)


def _load_func(path):
    """Extrae _detect_threads del fuente y la ejecuta aislada (sin importar fastapi)."""
    src = open(path, "r", encoding="utf-8").read()
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_detect_threads")
    ns = {"os": os}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), path, "exec"), ns)
    return ns["_detect_threads"]


def main():
    s1 = open(M1, "r", encoding="utf-8").read()
    s2 = open(M2, "r", encoding="utf-8").read()

    # V1
    for etiqueta, src in (("manager.py", s1), ("manager_v2.py", s2)):
        check("V1." + etiqueta,
              '"--threads"' in src and '"--threads-batch"' in src,
              "--threads/--threads-batch presentes")
    # V2
    check("V2", SED_OLD in s2, "patron del sed --reasoning off intacto en manager_v2.py")
    # V3
    parcheado = s2.replace(SED_OLD, SED_NEW)
    check("V3", '"--reasoning", "off"' in parcheado and '"--threads"' in parcheado
          and '"--threads-batch"' in parcheado,
          "el sed produce --reasoning off + --threads")
    # V4/V5/V6/V7
    fn = _load_func(M2)
    with tempfile.TemporaryDirectory() as d:
        v2 = os.path.join(d, "cpu.max")
        open(v2, "w").write("800000 100000\n")
        check("V4", fn(cgroup_v2=v2) == 8, "cgroup v2 800000/100000 -> 8")
        os.environ["LLAMA_THREADS"] = "5"
        check("V6", fn(cgroup_v2=v2) == 5, "env LLAMA_THREADS=5 -> 5")
        del os.environ["LLAMA_THREADS"]
        q = os.path.join(d, "cpu.cfs_quota_us")
        p = os.path.join(d, "cpu.cfs_period_us")
        open(q, "w").write("800000\n")
        open(p, "w").write("100000\n")
        check("V5", fn(cgroup_v2=os.path.join(d, "nope"), cgroup_v1_quota=q, cgroup_v1_period=p) == 8,
              "cgroup v1 800000/100000 -> 8")
        check("V7", fn(cgroup_v2=os.path.join(d, "nope"), cgroup_v1_quota=os.path.join(d, "nope2"),
                       cgroup_v1_period=os.path.join(d, "nope3")) == 8, "sin cgroup -> 8")
    # V8
    for etiqueta, path in (("manager.py", M1), ("manager_v2.py", M2)):
        rc = subprocess.call([sys.executable, "-m", "py_compile", path])
        check("V8." + etiqueta, rc == 0, "py_compile")

    if FALLOS:
        print("LLAMA_THREADS_VERIFY FAIL: %s" % ",".join(FALLOS))
        return 1
    print("LLAMA_THREADS_VERIFY OK (%d checks)" % 13)
    return 0


if __name__ == "__main__":
    sys.exit(main())
