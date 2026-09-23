import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    top_level_projects = {}
    total_files = 0
    total_bytes = 0

    for entry in root_listing:
        path = entry["path"]
        typ = entry["type"]
        if typ == "blob":
            total_files += 1
            total_bytes += entry["size"]

            if path.startswith(prefix):
                # Remove prefix and split
                remainder = path[len(prefix):]
                parts = remainder.split("/", 1)
                if len(parts) == 2:
                    project_name = parts[0]
                    if project_name not in top_level_projects:
                        top_level_projects[project_name] = {"files": 0, "bytes": 0}
                    top_level_projects[project_name]["files"] += 1
                    top_level_projects[project_name]["bytes"] += entry["size"]

    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
