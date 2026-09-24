import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    prefix_len = len(prefix)
    
    top_level = {}
    total_files = 0
    total_bytes = 0
    
    for item in root_listing:
        path = item["path"]
        typ = item["type"]
        
        if typ == "blob":
            total_files += 1
            total_bytes += item["size"]
            
            # Check if it's under the prefix
            if path.startswith(prefix):
                rest = path[prefix_len:]
                if "/" in rest:
                    project_name = rest.split("/")[0]
                    if project_name not in top_level:
                        top_level[project_name] = {"files": 0, "bytes": 0}
                    top_level[project_name]["files"] += 1
                    top_level[project_name]["bytes"] += item["size"]
    
    return {
        "top_level_projects": top_level,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
