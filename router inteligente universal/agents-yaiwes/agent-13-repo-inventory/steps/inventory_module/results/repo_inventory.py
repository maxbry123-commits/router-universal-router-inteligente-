def summarize(root_listing: list[dict]) -> dict:
    prefix = "Componente open soure router inteligente universal/"
    total_files = 0
    total_bytes = 0
    projects = {}

    for item in root_listing:
        if item.get("type") != "blob":
            continue
        size = item.get("size", 0)
        total_files += 1
        total_bytes += size

        path = item.get("path", "")
        if not path.startswith(prefix):
            continue
        remainder = path[len(prefix):]
        # Ignore blobs directly in the root (no subfolder after prefix)
        if not remainder:
            continue
        # Find first '/' to get the top-level project name
        first_slash = remainder.find("/")
        if first_slash == -1:
            # This would be a blob like "prefix<name>" without trailing slash; treat as root blob -> ignore
            continue
        project = remainder[:first_slash]
        if project not in projects:
            projects[project] = {"files": 0, "bytes": 0}
        projects[project]["files"] += 1
        projects[project]["bytes"] += size

    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes,
    }
