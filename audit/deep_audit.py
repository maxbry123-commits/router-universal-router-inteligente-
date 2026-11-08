import os, json
from huggingface_hub import HfApi

USER = "COMAND-CENTER-1"
api = HfApi(token=os.environ.get("HF_TOKEN"))

# Archivos exactos que necesitamos leer completos (sin recortes)
targets = {
    "COMAND-CENTER-1/riu-router": ["proxy.py", "boot.sh", "README.md"],
    "COMAND-CENTER-1/claude-github-mcp-backup": ["fleet.py", "mini.py", "door.py", "app.py", "README.md"],
    "COMAND-CENTER-1/swe-code-web": ["src/server.js", "src/motor.js", "src/modos.js", "README.md"]
}

results = {}

for sp_id, files in targets.items():
    results[sp_id] = {}
    try:
        repo_files = api.list_repo_files(repo_id=sp_id, repo_type="space")
        for f in files:
            # Buscar el archivo (incluso si está en subcarpetas)
            matches = [p for p in repo_files if p == f or p.endswith("/" + f)]
            if not matches:
                results[sp_id][f] = "NO_EXISTE"
                continue
            
            rel_path = matches[0]
            # Descargar el archivo completo
            local_path = api.hf_hub_download(repo_id=sp_id, repo_type="space", filename=rel_path)
            with open(local_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                results[sp_id][rel_path] = content  # Sin recortes
    except Exception as e:
        results[sp_id]["error"] = str(e)

# Guardar el JSON completo
with open("audit/edificio2/full_code.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("===AUDITORIA_PROFUNDA_COMPLETADA===")
print(json.dumps(results, indent=2))
