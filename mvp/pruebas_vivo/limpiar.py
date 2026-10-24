"""Deja el Router como estaba tras las pruebas: quita los pendientes 'sol-*' y el yaiwes.md 'proyecto-*' que escribieron los modelos de prueba.
Uso: RIU_KEY=<clave> python3 -m mvp.pruebas_vivo.limpiar [--base URL]. Solo toca datos que empiezan por esos prefijos."""
import os
import sys
from mvp.pruebas_vivo.cliente import Cliente

BASE = "https://comand-center-1-riu-router.hf.space"


def limpiar(c):
    quitados, ok = [], True
    bien, d = c.herramienta("pendientes", {"accion": "listar"})
    ok = ok and bien
    for p in (d.get("pendientes") or []) if bien else []:
        if str(p.get("texto", "")).startswith("sol-"):
            quitados.append(p["texto"]); c.herramienta("pendientes", {"accion": "quitar", "id": p["id"]})
    bien, d = c.herramienta("yaiwes_md", {"accion": "leer"})
    ok = ok and bien
    if bien and str(d.get("texto", "")).startswith("proyecto-"):
        c.herramienta("yaiwes_md", {"accion": "escribir", "texto": ""}); quitados.append("yaiwes.md")
    return ok, quitados


def main(argv):
    base = argv[argv.index("--base") + 1] if "--base" in argv else BASE
    if not os.environ.get("RIU_KEY"):
        sys.exit("Falta la variable RIU_KEY (la clave de acceso del Router).")
    ok, quitados = limpiar(Cliente(base, os.environ["RIU_KEY"]))
    print("Limpieza %s. Quitado: %s" % ("OK" if ok else "con errores (herramienta bloqueada?)", ", ".join(quitados) or "nada"))


if __name__ == "__main__":
    main(sys.argv)
