import os
import json

def summarize(root_listing: list[dict]) -> dict:
    """
    Procesa una lista de archivos del repositorio y devuelve un resumen.
    
    Args:
        root_listing: Lista de diccionarios con "path", "type" y "size".
        
    Returns:
        Diccionario con top_level_projects, total_files y total_bytes.
    """
    total_files = 0
    total_bytes = 0
    projects = {}
    
    base_prefix = "Componente open soure router inteligente universal/"
    
    for item in root_listing:
        path = item["path"]
        item_type = item.get("type")
        size = item.get("size", 0)
        
        # Solo procesar blobs (archivos)
        if item_type == "blob":
            total_files += 1
            total_bytes += size
            
            # Verificar si la ruta comienza con el prefijo base
            if path.startswith(base_prefix):
                # Obtener el resto después del prefijo base
                rest = path[len(base_prefix):]
                
                # Dividir por "/" para obtener el nombre del proyecto
                parts = rest.split("/")
                if len(parts) >= 2:  # Tiene al menos un subdirectorio
                    project_name = parts[0]
                    
                    if project_name:
                        if project_name not in projects:
                            projects[project_name] = {"files": 0, "bytes": 0}
                        projects[project_name]["files"] += 1
                        projects[project_name]["bytes"] += size
    
    return {
        "top_level_projects": projects,
        "total_files": total_files,
        "total_bytes": total_bytes
    }
