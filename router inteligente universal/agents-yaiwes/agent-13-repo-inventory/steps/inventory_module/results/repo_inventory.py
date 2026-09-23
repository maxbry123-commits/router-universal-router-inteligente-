import os
import json

def summarize(root_listing: list[dict]) -> dict:
    total_files = 0
    total_bytes = 0
    top_level_projects = {}

    prefix = "Componente open soure router inteligente universal/"
    prefix_len = len(prefix)

    for entry in root_listing:
        path = entry["path"]
        if entry["type"] == "blob":
            total_files += 1
            total_bytes += entry["size"]

        if not path.startswith(prefix):
            continue

        # Quitamos el prefijo
        remainder = path[prefix_len:]

        # Si no hay nada más o no tiene subcarpeta (el nombre del proyecto es la primera parte)
        if "/" not in remainder:
            continue  # blob directamente en la raíz, ignorar

        project_name, _ = remainder.split("/", 1)

        if entry["type"] == "blob":
            if project_name not in top_level_projects:
                top_level_projects[project_name] = {"files": 0, "bytes": 0}
            top_level_projects[project_name]["files"] += 1
            top_level_projects[project_name]["bytes"] += entry["size"]

    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
