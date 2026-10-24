"""Prueba real de todos los modelos y herramientas contra el Router. Uso: RIU_KEY=<clave> python -m mvp.pruebas_vivo.correr [--base URL] [--solo modelo] [--sin-medios] [--video]
Escribe informe_sol.md e informe_sol.json (evidencia cruda recortada). PASS solo con salida real; si no hay respuesta, FAIL con el error exacto."""
import json
import os
import sys
import time
from mvp import modelos
from mvp.pruebas_vivo.cliente import Cliente, texto

REPO = "maxbry123-commits/router-universal-router-inteligente-"
FILAS = []


def escribir_informe():
    print("PASS %d / %d. Informe: informe_sol.md" % (sum(x["estado"] == "PASS" for x in FILAS), len(FILAS)))


if __name__ == "__main__":
    main(sys.argv)
