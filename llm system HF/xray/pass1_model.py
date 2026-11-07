import os, json
from huggingface_hub import HfApi

USERNAME = "COMAND-CENTER-1"
api = HfApi(token=os.environ.get("HF_TOKEN"))
out = {"spaces": [], "datasets": [], "models": [], "categorization": {"bancos": [], "modelos_locales": [], "almacenamiento_colas": [], "basura": []}}

for sp in api.list_spaces(author=USERNAME):
    info = api.space_info(repo_id=sp.id)
    files = [f for f in api.list_repo_files(repo_id=sp.id, repo_type="space") if f != ".gitattributes"]
    try:
        # [FIX-DAG-v3/2] get_space_secrets() devuelve un DICT {nombre: SpaceSecret}, no una lista
        #   de objetos: iterarlo da las CLAVES (str) y "s.key" reventaba con
        #   "AttributeError: 'str' object has no attribute 'key'" (quedaba tapado por el except
        #   y TODOS los Spaces salian como NO_ACCESS, falseando la categoria 'bancos').
        secrets = list(api.get_space_secrets(repo_id=sp.id).keys())
    except:
        secrets = ["NO_ACCESS"]

    # [FIX-DAG-v3/1] En huggingface_hub 2.4.0 SpaceRuntime.hardware es un STRING ('cpu-upgrade'),
    #   no un dict: "info.runtime.hardware.current" reventaba con
    #   "AttributeError: 'str' object has no attribute 'current'" y mataba la PASADA 1 entera.
    _hw = info.runtime.hardware if info.runtime else None
    _hw = _hw.get("current") if isinstance(_hw, dict) else _hw

    sp_data = {"id": sp.id, "sdk": info.sdk, "hardware": _hw, "files": files, "secrets_names": secrets}
    out["spaces"].append(sp_data)

    if any("bank" in s.lower() or "key" in s.lower() for s in secrets) or "bank" in sp.id.lower():
        out["categorization"]["bancos"].append(sp.id)
    if "qwen" in sp.id.lower() or "lfm" in sp.id.lower() or "model" in sp.id.lower():
        out["categorization"]["modelos_locales"].append(sp.id)
    if any("queue" in f.lower() or "cola" in f.lower() or "watchdog" in f.lower() or "control" in f.lower() for f in files):
        out["categorization"]["almacenamiento_colas"].append(sp.id)
    if "v7" in sp.id.lower() or "snapshot" in sp.id.lower():
        out["categorization"]["basura"].append(sp.id)

for ds in api.list_datasets(author=USERNAME):
    out["datasets"].append({"id": ds.id})
for m in api.list_models(author=USERNAME):
    out["models"].append({"id": m.id})

with open("llm system HF/xray/huella_digital_v2.json", "w") as f:
    json.dump(out, f, indent=2)
print("PASS_1_OK: Huella generada.")
