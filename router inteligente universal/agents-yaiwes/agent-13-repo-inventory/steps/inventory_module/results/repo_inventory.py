import os
import json

def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    top_level_projects = {}
    total_files = 0
    total_bytes = 0
    
    for item in root_listing:
        path = item["path"]
        item_type = item["type"]
        size = item.get("size", 0)
        
        if item_type == "blob":
            total_files += 1
            total_bytes += size
            
            if path.startswith(prefix):
                rel_path = path[len(prefix):]
                if "/" in rel_path:
                    project_name = rel_path.split("/")[0]
                    if project_name:
                        if project_name not in top_level_projects:
                            top_level_projects[project_name] = {"files": 0, "bytes": 0}
                        top_level_projects[project_name]["files"] += 1
                        top_level_projects[project_name]["bytes"] += size
    
    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
