"""agent_credentials.py — Gestión segura de credenciales para los agentes.
Nunca expone los tokens en texto plano (solo los lee del entorno).
"""
import os
import logging

logger = logging.getLogger(__name__)

class AgentCredentials:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.hf_token = os.getenv("HF_TOKEN", "")
        self.router_api_key = os.getenv("ROUTER_API_KEY", "")

    def validate(self, agent_name: str) -> dict:
        """Verifica si el agente tiene los tokens necesarios configurados."""
        missing = []
        if not self.github_token: missing.append("GITHUB_TOKEN")
        if not self.hf_token: missing.append("HF_TOKEN")
        if not self.router_api_key: missing.append("ROUTER_API_KEY")
        
        if missing:
            logger.warning(f"Credenciales faltantes para {agent_name}: {missing}")
            return {"valid": False, "missing": missing}
        return {"valid": True, "missing": []}

    def get_github_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github.v3+json"}

    def get_hf_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.hf_token}"}

    def get_router_headers(self) -> dict:
        return {"X-API-Key": self.router_api_key}

# Instancia global
CREDS = AgentCredentials()
