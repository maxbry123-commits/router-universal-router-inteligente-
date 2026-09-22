def summarize(root_listing):
    prefix = "Componente open soure router inteligente universal/"
    total_files = 0
    total_bytes = 0
    top_level_projects = {}
    for entry in root_listing:
        if entry.get("type") != "blob":
            continue
        total_files += 1
        total_bytes += entry.get("size", 0)
        path = entry.get("path", "")
        if path.startswith(prefix):
            rest = path[len(prefix):]
            # Ignoro los blobs que están directamente bajo el prefijo (sin subcarpeta)
            if '/' not in rest:
                continue
            name = rest.split('/', 1)[0]
            proj = top_level_projects.get(name)
            if proj is None:
                top_level_projects[name] = {"files": 0, "bytes": 0}
            top_level_projects[name]["files"] += 1
            top_level_projects[name]["bytes"] += entry.get("size", 0)
    return {"top_level_projects": top_level_projects, "total_files": total_files, "total_bytes": total_bytes}
