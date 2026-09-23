import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    top_level_projects = {}
    total_files = 0
    total_bytes = 0
    
    for entry in root_listing:
        path = entry["path"]
        entry_type = entry["type"]
        size = entry.get("size", 0)
        
        total_files += 1 if entry_type == "blob" else 0
        total_bytes += size if entry_type == "blob" else 0
        
        if path.startswith(prefix):
            relative_path = path[len(prefix):]
            if "/" in relative_path:
                project_name = relative_path.split("/")[0]
                if entry_type == "blob":
                    if project_name not in top_level_projects:
                        top_level_projects[project_name] = {"files": 0, "bytes": 0}
                    top_level_projects[project_name]["files"] += 1
                    top_level_projects[project_name]["bytes"] += size
    
    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
