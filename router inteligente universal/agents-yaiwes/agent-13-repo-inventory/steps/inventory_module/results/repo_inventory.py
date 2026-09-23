import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    top_level_projects = {}
    total_files = 0
    total_bytes = 0
    
    for entry in root_listing:
        if entry["type"] != "blob":
            continue
            
        path = entry["path"]
        size = entry.get("size", 0)
        total_files += 1
        total_bytes += size
        
        if path.startswith(prefix):
            # Remove the prefix
            rel_path = path[len(prefix):]
            # Split to get the first segment after the prefix
            parts = rel_path.split("/", 1)
            if len(parts) >= 1 and parts[0]:
                project_name = parts[0]
                if project_name not in top_level_projects:
                    top_level_projects[project_name] = {"files": 0, "bytes": 0}
                top_level_projects[project_name]["files"] += 1
                top_level_projects[project_name]["bytes"] += size
        # else: ignore blobs not under the expected prefix
    
    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
