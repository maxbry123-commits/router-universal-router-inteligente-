import json
import os
from typing import List, Dict

def summarize(root_listing: List[Dict]) -> Dict:
    base = "Componente open soure router inteligente universal/"
    total_files = 0
    total_bytes = 0
    projects: Dict[str, Dict[str, int]] = {}

    for item in root_listing:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        size = item.get("size", 0)

        total_files += 1
        total_bytes += size

        if not path.startswith(base):
            continue
        remainder = path[len(base):]
        # Ignore blobs directly under the base folder (no further subdirectory)
        if not remainder or "/" not in remainder:
            continue
        project_name = remainder.split("/", 1)[0]
        if project_name not in projects:
            projects[project_name] = {"files": 0, "bytes": 0}
        projects[project_name]["files"] += 1
        projects[project_name]["bytes"] += size

    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes,
    }
