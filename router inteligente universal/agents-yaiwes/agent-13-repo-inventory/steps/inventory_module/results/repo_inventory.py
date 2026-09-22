import json
import os
from typing import List, Dict, Any

def summarize(root_listing: List[Dict[str, Any]]) -> Dict[str, Any]:
    prefix = "Componente open soure router inteligente universal/"
    total_files = 0
    total_bytes = 0
    projects: Dict[str, Dict[str, int]] = {}

    for entry in root_listing:
        if entry.get("type") == "blob":
            total_files += 1
            size = entry.get("size", 0)
            total_bytes += size
            path = entry.get("path", "")
            if path.startswith(prefix):
                suffix = path[len(prefix):]
                # Ignore blobs directly in the root of the prefix (no subfolder)
                if suffix and '/' in suffix:
                    project = suffix.split('/', 1)[0]
                    proj_info = projects.get(project)
                    if proj_info is None:
                        proj_info = {"files": 0, "bytes": 0}
                        projects[project] = proj_info
                    proj_info["files"] += 1
                    proj_info["bytes"] += size

    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes,
    }
