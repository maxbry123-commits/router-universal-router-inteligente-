import json
import os

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    top_level_projects = {}

    total_files = 0
    total_bytes = 0

    for entry in root_listing:
        path = entry["path"]
        entry_type = entry["type"]
        size = entry.get("size", 0)

        if entry_type == "blob":
            total_files += 1
            total_bytes += size

        # Check if path starts with the prefix and has another component after
        if path.startswith(prefix):
            remainder = path[len(prefix):]
            # Split by "/" to get project name (first component)
            parts = remainder.split("/")
            if len(parts) >= 2 and parts[0] != "":
                project_name = parts[0]
                if project_name not in top_level_projects:
                    top_level_projects[project_name] = {"files": 0, "bytes": 0}
                if entry_type == "blob":
                    top_level_projects[project_name]["files"] += 1
                    top_level_projects[project_name]["bytes"] += size

    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
