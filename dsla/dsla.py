# -*- coding: utf-8 -*-
"""
dsla — DSL · DAG · shema · sheriff · validador · verificación ·
       sentinela · guardián · supervisor · juez · imput · block ·
       verbatim · salida  (id de tarea)

Python ≥3.8 · solo stdlib · sin red · sin eval/exec.

Contrato (jsonc):
  {
    "dsl": "dsla@1",
    "id_tarea": "t-0001",
    "grafo": {
      "nodos": [
        {"id": "n1", "verb": "EJECUTAR", "deps": [],
         "params": {"cmd": "hola", "n": 3}},
        {"id": "n2", "verb": "VALIDAR",  "deps": ["n1"],
         "params": {"min_long": 1}}
      ]
    },
    "inputs":  {"cfg": {"a": 1}},
    "checks":  {"tipo": "str", "min_long": 1, "max_long": 1000000,
                "frase": "OK"},
    "outputs": [{"k": "r0", "de": "n2"}],
    "contrato_salida": {"frase": "OK", "tipo": "str"}
  }

Reglas anti-inyección (resumen; ver dsl/DAGSHEMA.md):
  R1  No hay eval/exec ni introspección dinámica del payload.
  R2  Todo se valida ANTES de ejecutar un solo nodo (shema + topología + ids).
  R3  id_tarea: ^[a