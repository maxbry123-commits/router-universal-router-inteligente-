"""Imprime las llamadas MCP exactas (JSON) de cada tarea para quien solo tiene las herramientas MCP (sin Python ni HTTP al Space).
Uso: python3 -m mvp.pruebas_vivo.guion [--modelos a,b] [--pruebas t1,t2,t3,t4,t5,t6]   (no necesita red ni clave)"""
import json
import sys
from unittest.mock import patch
from mvp import modelos
from mvp.pruebas_vivo import pruebas, tareas


class Grabador:
    def __init__(self):
        self.pasos = []

    def chat(self, modelo, mensaje=None, rid="x", **extra):
        self.pasos.append({"herramienta": "chat", "argumentos": {"ficha_qwen": "1", "modelo": modelo, "request_id": pruebas.CORRIDA + rid, "message": mensaje, **extra}})
        return {"estado": "completado"}

    def herramienta(self, nombre, args):
        self.pasos.append({"herramienta": nombre + "  (comprobar)", "argumentos": args})
        return True, {}


def main(argv):
    lista = argv[argv.index("--modelos") + 1].split(",") if "--modelos" in argv else [m["id"] for m in modelos.cargar()["texto"] if m["p"]]
    sel = argv[argv.index("--pruebas") + 1].split(",") if "--pruebas" in argv else list(tareas.TAREAS)
    for m in lista:
        g = Grabador()
        pruebas.FILAS.clear()
        with patch.object(pruebas, "anotar", lambda *a, **k: None):  # solo se imprimen las llamadas: sin informes ni PASS/FAIL
            tareas.tareas_modelo(g, m, sel)
        print(json.dumps({"modelo": m, "pasos": g.pasos}, ensure_ascii=False, indent=1))
        print("Despues de cada chat: llamar a `resultado` con su proceso_id hasta estado=completado; comprobar con las llamadas (comprobar). t4 necesita permisos.ia=true (herramienta `salud`).")


if __name__ == "__main__":
    main(sys.argv)
