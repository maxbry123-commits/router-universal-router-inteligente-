import os
import json

def summarize(root_listing: list[dict]) -> dict:
    """
    Procesa el listado completo del árbol del repositorio y devuelve:
    - total_files: número total de archivos (blobs)
    - total_bytes: suma total de tamaños (bytes)
    - top_level_projects: agrupación de proyectos en el primer nivel bajo
      "Componente open soure router inteligente universal/"
    """
    total_files = 0
    total_bytes = 0
    # Diccionario para proyectos de primer nivel: {nombre: {"files": int, "bytes": int}}
    projects = {}

    prefix = "Componente open soure router inteligente universal/"

    for entry in root_listing:
        path = entry["path"]
        ftype = entry["type"]
        size = entry.get("size", 0)

        # Solo procesamos blobs (archivos)
        if ftype == "blob":
            total_files += 1
            total_bytes += size

            # Verificar si la ruta comienza con el prefijo y tiene al menos una subcarpeta
            if path.startswith(prefix):
                # Eliminar el prefijo y obtener el resto
                remainder = path[len(prefix):]
                # Buscar el primer segmento
                first_slash = remainder.find("/")
                if first_slash != -1:
                    project_name = remainder[:first_slash]
                    if project_name not in projects:
                        projects[project_name] = {"files": 0, "bytes": 0}
                    projects[project_name]["files"] += 1
                    projects[project_name]["bytes"] += size
                # Si la ruta coincide con el prefijo exacto o solo tiene el nombre del proyecto sin slash, se ignora
                # (blobs en la raíz del directorio del router inteligente, sin subcarpeta)

    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
