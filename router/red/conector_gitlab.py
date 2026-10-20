"""Adaptador GitLab v6 para Router Inteligente Universal.

Contrato: todo secreto se resuelve por variable de entorno y la clase conserva
la interfaz universal ``enviar(payload)`` / ``sondear()``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx


@dataclass
class ConectorGitLab:
    """GitLab REST API adapter sin lógica de orquestación."""

    conector_id: str
    project: str
    base_url: str = "https://gitlab.com/api/v4"
    token_env: str = "GITLAB_TOKEN"
    timeout_s: float = 30.0

    def _headers(self) -> dict[str, str]:
        token = os.environ.get(self.token_env, "")
        if not token:
            raise RuntimeError(f"env_faltante:{self.token_env}")
        return {"PRIVATE-TOKEN": token}

    def _project_path(self) -> str:
        if not self.project:
            raise ValueError("project_faltante")
        return quote(self.project, safe="")

    async def enviar(self, payload: dict) -> dict:
        """Ejecuta una acción GitLab declarada y devuelve contrato DONE/FAIL."""
        accion = payload.get("_accion", "project_info")
        project = self._project_path()
        routes = {
            "project_info": ("GET", f"/projects/{project}"),
            "get_file": (
                "GET",
                f"/projects/{project}/repository/files/"
                f"{quote(payload.get('path', ''), safe='')}",
            ),
            "create_issue": ("POST", f"/projects/{project}/issues"),
            "create_mr": ("POST", f"/projects/{project}/merge_requests"),
            "trigger_pipeline": ("POST", f"/projects/{project}/pipeline"),
        }
        if accion not in routes:
            return {"status": "FAIL", "error": f"accion_no_soportada:{accion}"}
        method, route = routes[accion]
        body = {k: v for k, v in payload.items() if not k.startswith("_")}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{route}",
                    headers=self._headers(),
                    params=body if method == "GET" else None,
                    json=body if method != "GET" else None,
                )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            output = response.json() if "json" in content_type else response.text
            return {"status": "DONE", "code": response.status_code, "output": output}
        except Exception as exc:  # noqa: BLE001
            return {"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"}

    async def sondear(self) -> bool:
        """Comprueba acceso real al proyecto sin ocultar credenciales faltantes."""
        result = await self.enviar({"_accion": "project_info"})
        return result["status"] == "DONE"
