import json
import os

def summarize(root_listing: list[dict]) -> dict:
    """
    Summarize repository inventory from a file listing.
    
    Args:
        root_listing: List of dicts with keys "path", "type" ("blob"|"tree"), 
                     and "size" (int, bytes, only for blobs)
    
    Returns:
        dict with keys "top_level_projects", "total_files", "total_bytes"
    """
    prefix = "Componente open soure router inteligente universal/"
    
    # Count total files and bytes
    total_files = 0
    total_bytes = 0
    for item in root_listing:
        if item["type"] == "blob":
            total_files += 1
            total_bytes += item["size"]
    
    # Group by top-level project name
    projects = {}
    for item in root_listing:
        if item["type"] != "blob":
            continue
        path = item["path"]
        # Check if path starts with the prefix and has at least one more component
        if not path.startswith(prefix):
            continue
        # Get the part after prefix
        relative_path = path[len(prefix):]
        # Find the first path component (project name)
        first_slash = relative_path.find("/")
        if first_slash == -1:
            # This is a blob directly in the root of the prefix, ignore
            continue
        project_name = relative_path[:first_slash]
        # Initialize or update project stats
        if project_name not in projects:
            projects[project_name] = {"files": 0, "bytes": 0}
        projects[project_name]["files"] += 1
        projects[project_name]["bytes"] += item["size"]
    
    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
