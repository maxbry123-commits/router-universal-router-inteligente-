"""agent_mirror.py — Crea/actualiza los mirrors de OpenClaw y Hermes en HF."""
import os
import logging
from huggingface_hub import HfApi, HfHubHTTPError, RepositoryNotFoundError

logger = logging.getLogger(__name__)
api = HfApi(token=os.getenv("HF_TOKEN"))

def ensure_mirror(agent_name: str) -> dict:
    """Asegura que el mirror del agente existe en HF. Si no, lo crea."""
    source_repo = f"COMAND-CENTER-1/{agent_name}"
    mirror_repo = f"COMAND-CENTER-1/{agent_name}-mirror"
    
    try:
        # Verificar si el mirror ya existe
        api.repo_info(mirror_repo, repo_type="space")
        logger.info(f"Mirror {mirror_repo} ya existe.")
        return {"status": "exists", "mirror": mirror_repo}
    except RepositoryNotFoundError:
        logger.info(f"Mirror {mirror_repo} no existe. Creando...")
        try:
            # Crear el mirror vacío como Space de Docker
            api.create_repo(repo_id=mirror_repo, repo_type="space", space_sdk="docker", private=True)
            return {"status": "created", "mirror": mirror_repo}
        except Exception as e:
            logger.error(f"Fallo al crear mirror {mirror_repo}: {e}")
            return {"status": "error", "detail": str(e)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

def sync_agent_configs(agents: list):
    """Sincroniza la configuración de los agentes en sus repos de mirror."""
    results = []
    for agent in agents:
        if agent in ["openclaw", "hermes"]:
            results.append(ensure_mirror(agent))
    return results
