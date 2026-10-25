#!/usr/bin/env python3
"""Aditivo: NO modifica los archivos base. Genera:
  loop_contract.schema.v1_1.json  (schema base + addon)
  loop_contract.example.v1_1.json (ejemplo base + bloques del addon)"""
import json, copy

def load(p):
    with open(p, encoding="utf-8") as f: return json.load(f)

addon = load("loop_contract.addon.json")
schema = copy.deepcopy(load("loop_contract.schema.json"))
example = copy.deepcopy(load("loop_contract.example.json"))

schema["$id"] = "https://yaiwes.local/schemas/loop_contract.schema.v1_1.json"
schema["title"] = "LOOP_CONTRACT_DAG_v1_1"
schema["properties"]["schema_version"] = {"const": addon["adds_schema_version"]}
for k, v in addon["properties"].items():
    if k in schema["properties"]:
        raise SystemExit(f"FAIL: la propiedad {k} ya existe en el schema base (additive-only)")
    schema["properties"][k] = v
for k, v in addon["defs"].items():
    if k in schema["$defs"]:
        raise SystemExit(f"FAIL: def {k} ya existe (additive-only)")
    schema["$defs"][k] = v
for r in addon["required_additions"]:
    if r not in schema["required"]:
        schema["required"].append(r)

example["schema_version"] = addon["adds_schema_version"]
for k, v in addon["example_values"].items():
    example[k] = v

with open("loop_contract.schema.v1_1.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)
with open("loop_contract.example.v1_1.json", "w", encoding="utf-8") as f:
    json.dump(example, f, ensure_ascii=False, indent=2)
print("OK: generados loop_contract.schema.v1_1.json y loop_contract.example.v1_1.json")
