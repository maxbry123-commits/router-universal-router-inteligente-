import os
import json

def summarize(root_listing):
    """
    Summariza el listado del repositorio.
    
    Parámetros:
        root_listing (list[dict]): Lista de dicts con claves "path", "type" y opcional "size".
    
    Retorna:
        dict: {"top_level_projects": dict, "total_files": int, "total_bytes": int}
    """
    prefix = "Componente open soure router inteligente universal/"
    top_level_projects = {}
    total_files = 0
    total_bytes = 0

    for item in root_listing:
        # Solo procesar blobs (archivos)
        if item.get("type") != "blob":
            continue

        size = item.get("size", 0)
        total_files += 1
        total_bytes += size

        path = item.get("path", "")
        if path.startswith(prefix):
            rest = path[len(prefix):]  # parte después del prefijo
            # Ignorar archivos directamente en la raíz del prefijo (sin subcarpeta)
            if '/' in rest:
                project_name = rest.split('/', 1)[0]
                if project_name:  # seguridad extra
                    proj_data = top_level_projects.get(project_name)
                    if proj_data is None:
                        top_level_projects[project_name] = {"files": 0, "bytes": 0}
                    top_level_projects[project_name]["files"] += 1
                    top_level_projects[project_name]["bytes"] += size

    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
