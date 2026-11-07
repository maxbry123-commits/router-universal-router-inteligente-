import os, json, time, sys
from huggingface_hub import HfApi

USER = "COMAND-CENTER-1"
file_path = "llm system HF/xray/huella_digital_v2.json"

# Esperar a que Pass 1 termine
for _ in range(30):
    if os.path.exists(file_path): break
    time.sleep(2)

if not os.path.exists(file_path):
    print("SHERIFF_FAIL: No se encontró huella_digital_v2.json")
    sys.exit(1)
    
with open(file_path, "r") as f:
    data = json.load(f)
    
verdict = {"pass1_count": len(data["spaces"]), "api_check": False, "verdict": "PASS"}

# El Sheriff verifica contra la API real de HF
api = HfApi(token=os.environ.get("HF_TOKEN"))
real_spaces = [s.id for s in api.list_spaces(author=USER)]

if len(real_spaces) != verdict["pass1_count"]:
    verdict["verdict"] = "FAIL"
    print(f"SHERIFF_FAIL: Conteo mismatch. API={len(real_spaces)}, JSON={verdict['pass1_count']}")
else:
    verdict["api_check"] = True
    print("SHERIFF_PASS: Conteo coincide con la API.")
    
with open("llm system HF/xray/centinel_verdict.json", "w") as f:
    json.dump(verdict, f, indent=2)
    
if verdict["verdict"] == "FAIL": sys.exit(1)
