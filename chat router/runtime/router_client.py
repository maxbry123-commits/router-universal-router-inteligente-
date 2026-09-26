"""S3 — Cliente único hacia el Router. Puerta obligatoria de todo el staff.

Ningún agente habla con un proveedor de IA: todos llaman aquí y el Router aplica la ruta del Director
(NVIDIA/Kimi -> Cerebras -> Groq -> DeepSeek V4 Flash). Si un proveedor no responde se baja al siguiente
y la respuesta trae `degradado=True` + `aviso` para pintar la nota ROJA en el chat.

Configuración por entorno (sin claves en el repo):
  RIU_ROUTER_URL      base del Router            (def. http://127.0.0.1:8000)
  RIU_ROUTER_API_KEY  clave de agente del Router (X-API-Key)

Uso:
    from router_client import RouterClient
    c = RouterClient()
    r = c.preguntar("rowboat", "divide esta orden: ...")
    print(r["reply"], r["provider"], r["degradado"])
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

RUTAS = yaml.safe_load((Path(__file__).resolve().parent / "rutas_ia.yaml").read_text(encoding="utf-8"))
TIMEOUT = float(os.getenv("RIU_ROUTER_TIMEOUT", "120"))


class RouterError(RuntimeError):
    pass


class RouterClient:
    def __init__(self, base: str | None = None, api_key: str | None = None, modo: str = "cascada") -> None:
        self.base = (base or os.getenv("RIU_ROUTER_URL") or "http://127.0.0.1:8000").rstrip("/")
        self.api_key = api_key or os.getenv("RIU_ROUTER_API_KEY", "")
        if modo not in RUTAS["modos"]:
            raise ValueError(f"modo desconocido: {modo}")
        self.modo = modo
        self._modelos: dict[str, list[str]] = {}

    # ---------------- HTTP ----------------
    def _http(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        req = urllib.request.Request(
            self.base + path, method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            detalle = exc.read().decode(errors="replace")[:200]
            raise RouterError(f"{exc.code}:{detalle}") from exc
        except Exception as exc:
            raise RouterError(f"{type(exc).__name__}: Router no responde") from exc

    # ---------------- estado ----------------
    def salud(self) -> dict[str, Any]:
        return self._http("GET", "/health")

    def proveedores(self) -> list[dict[str, Any]]:
        return self._http("GET", "/chat/providers")["providers"]

    def configurados(self) -> list[str]:
        return [p["id"] for p in self.proveedores() if p.get("configured")]

    def modelos(self, proveedor: str) -> list[str]:
        if proveedor not in self._modelos:
            self._modelos[proveedor] = self._http("GET", f"/chat/providers/{proveedor}/models").get("models", [])
        return self._modelos[proveedor]

    def elegir_modelo(self, proveedor: str) -> str | None:
        catalogo = self.modelos(proveedor)
        if not catalogo:
            return None
        for patron in RUTAS["proveedores"].get(proveedor, {}).get("preferencias", []):
            for m in catalogo:
                if patron.lower() in m.lower():
                    return m
        return catalogo[0]

    # ---------------- staff ----------------
    def registrar_agente(self, agent_id: str, nombre: str, rol: str, prompt: str, modelos: list[str] | None = None) -> dict:
        return self._http("POST", "/chat/agents", {"id": agent_id.replace("_", "-"), "name": nombre, "role": rol,
                                                   "system_prompt": prompt, "models": modelos or []})

    def agentes(self) -> list[dict[str, Any]]:
        return self._http("GET", "/chat/agents")["agents"]

    # ---------------- ruta de IA ----------------
    def preguntar(self, agent_id: str | None, mensaje: str, *, conversacion: str | None = None,
                  max_tokens: int = 1024) -> dict[str, Any]:
        """Recorre la cascada del Director y devuelve la primera respuesta real."""
        intentos: list[dict[str, str]] = []
        for proveedor in RUTAS["modos"][self.modo]["orden"]:
            try:
                modelo = self.elegir_modelo(proveedor)
            except RouterError as exc:
                intentos.append({"proveedor": proveedor, "error": str(exc)})
                continue
            if not modelo:
                intentos.append({"proveedor": proveedor, "error": "sin catálogo (clave no configurada)"})
                continue
            cuerpo: dict[str, Any] = {"message": mensaje, "provider": proveedor, "model": modelo,
                                      "max_tokens": max_tokens,
                                      "mode": "agent" if agent_id else "direct"}
            if agent_id:
                cuerpo["agent_id"] = agent_id.replace("_", "-")
            if conversacion:
                cuerpo["conversation_id"] = conversacion
            try:
                data = self._http("POST", "/chat/send", cuerpo)
            except RouterError as exc:
                intentos.append({"proveedor": proveedor, "error": str(exc)})
                continue
            degradado = bool(intentos)
            return {**data, "degradado": degradado, "intentos": intentos,
                    "aviso": f"ROJO: se bajó a {proveedor}; fallaron " +
                             ", ".join(i["proveedor"] for i in intentos) if degradado else ""}
        raise RouterError("NINGUN_PROVEEDOR_DISPONIBLE: " + json.dumps(intentos, ensure_ascii=False))
