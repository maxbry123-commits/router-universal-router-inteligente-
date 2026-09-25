import os
import json

def summarize(root_listing: list[dict]) -> dict:
    """
    Procesa una lista de archivos/ directorios y devuelve un resumen.
    """
    total_files = 0
    total_bytes = 0
    top_level_projects = {}

    prefix = "Componente open soure router inteligente universal/"

    for entry in root_listing:
        path = entry["path"]
        entry_type = entry["type"]
        size = entry.get("size", 0)

        if entry_type == "blob":
            total_files += 1
            total_bytes += size

            # Verificar si está bajo el prefijo del proyecto
            if path.startswith(prefix):
                # Quitar el prefijo para obtener la parte después
                rest = path[len(prefix):]
                # Si hay al menos un directorio después del prefijo
                if "/" in rest:
                    project_name = rest.split("/")[0]
                    if project_name not in top_level_projects:
                        top_level_projects[project_name] = {"files": 0, "bytes": 0}
                    top_level_projects[project_name]["files"] += 1
                    top_level_projects[project_name]["bytes"] += size
                # Si no tiene subdirectorio (blob directamente en la raíz), se ignora

    return {
        "top_level_projects": top_level_projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
