def summarize(root_listing):
    """
    Summarizes a repository listing.

    Args:
        root_listing (list[dict]): List of dicts with keys:
            - "path": str, full path using '/' separator
            - "type": str, either "blob" or "tree"
            - "size": int, size in bytes for blobs (ignored for trees)

    Returns:
        dict: {
            "top_level_projects": {
                <project_name>: {"files": <blob count>, "bytes": <total size>}
            },
            "total_files": <total number of blobs>,
            "total_bytes": <sum of sizes of all blobs>
        }
    """
    PREFIX = "Componente open soure router inteligente universal/"
    top_level = {}
    total_files = 0
    total_bytes = 0

    for entry in root_listing:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        size = entry.get("size", 0)

        # Update overall totals
        total_files += 1
        total_bytes += size

        # Check if the blob belongs to a top‑level project under the prefix
        if not path.startswith(PREFIX):
            continue

        remainder = path[len(PREFIX):]  # part after the prefix
        # Ignore blobs directly in the root of the prefix (no subfolder)
        if not remainder or '/' not in remainder:
            continue

        # The first component after the prefix is the project name
        project = remainder.split('/', 1)[0]

        if project not in top_level:
            top_level[project] = {"files": 0, "bytes": 0}
        top_level[project]["files"] += 1
        top_level[project]["bytes"] += size

    return {
        "top_level_projects": top_level,
        "total_files": total_files,
        "total_bytes": total_bytes,
    }
