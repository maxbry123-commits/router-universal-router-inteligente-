import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    prefix_len = len(prefix)
    projects = {}
    total_files = 0
    total_bytes = 0
    
    for entry in root_listing:
        path = entry["path"]
        entry_type = entry["type"]
        size = entry.get("size", 0)
        
        # Only process blobs
        if entry_type != "blob":
            continue
            
        total_files += 1
        total_bytes += size
        
        # Check if path starts with the prefix
        if path.startswith(prefix) and len(path) > prefix_len:
            # Get the part after prefix
            rest = path[prefix_len:]
            # Find the first component name (up to first "/")
            slash_pos = rest.find("/")
            if slash_pos > 0:
                project_name = rest[:slash_pos]
                if project_name not in projects:
                    projects[project_name] = {"files": 0, "bytes": 0}
                projects[project_name]["files"] += 1
                projects[project_name]["bytes"] += size
    
    return {
        "top_level_projects": dict(sorted(projects.items())),
        "total_files": total_files,
        "total_bytes": total_bytes
    }
