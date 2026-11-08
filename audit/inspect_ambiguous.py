import os, json
from huggingface_hub import HfApi

USER = "COMAND-CENTER-1"
TOKEN = os.environ.get("HF_TOKEN")
api = HfApi(token=TOKEN)

spaces_to_inspect = [
    "COMAND-CENTER-1/riu-router",
    "COMAND-CENTER-1/claude-github-mcp-backup",
    "COMAND-CENTER-1/swe-code-web"
]

# Archivos que delatan si es cómputo, cola o banco
target_files = ["README.md", "app.py", "server.js", "proxy.py", "boot.sh", "mini.py", "fleet.py"]

results = {}

for sp_id in spaces_to_inspect:
    results[sp_id] = {}
    try:
        files = api.list_repo_files(repo_id=sp_id, repo_type="space")
        for f in target_files:
            # [FIX-DAG-v4/1] El DAG comprobaba "if f in files" (coincidencia EXACTA de raiz): en
            #   swe-code-web el fichero clave no esta en la raiz sino en src/ (src/server.js),
            #   asi que ese Space solo devolvia README.md y quedaba sin inspeccionar. Ahora se
            #   acepta tambien el anidado por nombre (p == f o p.endswith("/"+f)) y la clave del
            #   resultado es la ruta REAL dentro del Space.
            matches = [p for p in files if p == f or p.endswith("/" + f)]
            for rel in matches:
                path = api.hf_hub_download(repo_id=sp_id, repo_type="space", filename=rel)
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
                    # Leer solo los primeros 1000 caracteres para no saturar
                    results[sp_id][rel] = content[:1000] + ("..." if len(content) > 1000 else "")
    except Exception as e:
        results[sp_id]["error"] = str(e)

with open("audit/inspection_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("===INSPECCION_COMPLETADA===")
print(json.dumps(results, indent=2))
