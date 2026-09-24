import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    projects = {}
    total_files = 0
    total_bytes = 0
    
    for item in root_listing:
        path = item["path"]
        typ = item["type"]
        size = item.get("size", 0)
        
        # Count all blobs for totals
        if typ == "blob":
            total_files += 1
            total_bytes += size
        
        # Check if path starts with the prefix and has at least one subfolder after it
        if path.startswith(prefix):
            remainder = path[len(prefix):]
            if "/" in remainder:
                project_name = remainder.split("/")[0]
                if project_name not in projects:
                    projects[project_name] = {"files": 0, "bytes": 0}
                if typ == "blob":
                    projects[project_name]["files"] += 1
                    projects[project_name]["bytes"] += size
    
    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
