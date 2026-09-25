import os
import json

def summarize(root_listing: list[dict]) -> dict:
    """
    Summarize the repository listing, grouping by top-level projects under
    "Componente open soure router inteligente universal/".
    """
    total_files = 0
    total_bytes = 0
    top_level_projects = {}
    
    base = "Componente open soure router inteligente universal/"
    prefix_len = len(base)
    
    for entry in root_listing:
        path = entry["path"]
        entry_type = entry.get("type")
        size = entry.get("size", 0)
        
        # Count all blobs
        if entry_type == "blob":
            total_files += 1
            total_bytes += size
        
        # Check if path starts with the base prefix
        if not path.startswith(base):
            continue
        
        # Get the part after the base
        remainder = path[prefix_len:]
        
        # Split into components
        parts = remainder.split("/", 1)
        
        # Ignore blobs directly at the root of the base
        if len(parts) < 2:
            continue
        
        project_name = parts[0]
        
        # Only process blobs to avoid counting directories
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
