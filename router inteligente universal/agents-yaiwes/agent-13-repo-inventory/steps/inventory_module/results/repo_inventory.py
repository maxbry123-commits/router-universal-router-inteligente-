import json
import os

def summarize(root_listing: list[dict]) -> dict:
    total_files = 0
    total_bytes = 0
    projects = {}
    
    for entry in root_listing:
        path = entry["path"]
        entry_type = entry["type"]
        
        # Only process blobs (files)
        if entry_type != "blob":
            continue
            
        total_files += 1
        total_bytes += entry["size"]
        
        # Check if path starts with the base directory
        base = "Componente open soure router inteligente universal/"
        if path.startswith(base):
            # Get the part after the base
            relative = path[len(base):]
            # Check if there's a subdirectory (project name)
            if "/" in relative:
                project_name = relative.split("/")[0]
                if project_name:
                    if project_name not in projects:
                        projects[project_name] = {"files": 0, "bytes": 0}
                    projects[project_name]["files"] += 1
                    projects[project_name]["bytes"] += entry["size"]
    
    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
