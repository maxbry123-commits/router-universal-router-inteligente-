import json
import os
from typing import List, Dict

def summarize(root_listing: List[Dict]) -> Dict:
    prefix = "Componente open soure router inteligente universal/"
    top_level: Dict[str, Dict[str, int]] = {}
    total_files = 0
    total_bytes = 0

    for entry in root_listing:
        if entry.get("type") != "blob":
            continue
        total_files += 1
        size = entry.get("size", 0)
        total_bytes += size

        path = entry.get("path", "")
        if not path.startswith(prefix):
            continue
        rest = path[len(prefix):]
        if not rest:
            # blob directly under the root folder -> ignore for project stats
            continue
        # first component after the prefix is the project name
        project = rest.split("/", 1)[0]
        if not project:
            continue
        if project not in top_level:
            top_level[project] = {"files": 0, "bytes": 0}
        top_level[project]["files"] += 1
        top_level[project]["bytes"] += size

    return {
        "top_level_projects": top_level,
        "total_files": total_files,
        "total_bytes": total_bytes,
    }
