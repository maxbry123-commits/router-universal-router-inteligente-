"""Cliente mínimo del Router YAIWES para los adaptadores de la colmena."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

FLAG_URL = (
    "https://raw.githubusercontent.com/maxbry123-commits/"
    "router-universal-router-inteligente-/main/router%20inteligente%20universal/"
    "agents-yaiwes/ROUTER_JOB_PAUSE.flag"
)


def _simulated(rol: str) -> dict:
    role = rol.lower()
    plan = {
        "tasks": [{
            "id": "task-1",
            "objective": "ejecutar objetivo simulado",
            "role": "coder",
            "dependencies": [],
            "allowed_paths": ["src/"],
            "acceptance": ["tests PASS"],
        }]
    }
    if role in {"hermes.plan", "openclaw.plan", "hermes.synthesize"}:
        return plan
    if role in {"hermes.critique", "openclaw.critique", "openclaw.review_plan"}:
        return {"approve": True, "issues": []}
    if role in {"hermes.review", "openclaw.review", "hermes.reconsider", "openclaw.reconsider"}:
        return {"approve": True, "issues": []}
    if role == "ruflo.init_swarm":
        return {"status": "PASS", "topology": "hierarchical"}
    if role == "ruflo.dispatch":
        return {
            "status": "PASS",
            "tests": ["simulated"],
            "evidence": ["simulated"],
            "issues": [],
        }
    if role == "claude.design":
        return {"status": "PASS", "design": ["plan", "contract", "tests"]}
    if role in {"grok.execute", "grok.correct", "meta.fixer"}:
        return {
            "status": "PASS",
            "changed_files": ["simulated.py"],
            "tests": ["simulated"],
            "evidence": ["simulated"],
            "issues": [],
        }
    if role.startswith("meta."):
        return {"status": "PASS", "issues": []}
    if role == "claude.review":
        return {"status": "PASS", "issues": []}
    if role == "rowboat":
        return {"status": "PLANNING"}
    return {"status": "PASS", "approve": True, "issues": []}


class RouterCliente:
    """POST /chat/send (o /chat/route si se pasa `group`). En SIMULADO=1 nunca toca la red."""

    def __init__(self, live_url: str | None = None, max_tokens: int = 1200) -> None:
        self._url = live_url
        self.max_tokens = max_tokens

    def _live_url(self) -> str:
        if self._url:
            return self._url.rstrip("/")
        env_url = os.environ.get("RIU_LIVE_URL", "").strip()
        if env_url:
            return env_url.rstrip("/")
        with urllib.request.urlopen(FLAG_URL, timeout=20) as response:
            text = response.read().decode("utf-8", "replace")
        for line in text.splitlines():
            if line.startswith("LIVE_URL="):
                url = line.split("=", 1)[1].strip()
                if url:
                    return url.rstrip("/")
        raise RuntimeError("LIVE_URL no encontrado")

    @staticmethod
    def _extract_text(data: object) -> str:
        if isinstance(data, str):
            return data
        if not isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False)
        for key in ("reply", "response", "content", "text", "message"):
            value = data.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = value.get("content")
                if isinstance(nested, str):
                    return nested
        return json.dumps(data, ensure_ascii=False)

    def chat(self, prompt: str, rol: str, group: str | None = None) -> str:
        if os.environ.get("SIMULADO") == "1":
            return json.dumps(_simulated(rol), ensure_ascii=False)

        message = f"[ROL={rol}]\n{prompt}"
        if group:  # grupo de política del Router (p. ej. "assistants"): cadena + fallback la decide el Router
            url = self._live_url() + "/chat/route"
            payload = {"group": group, "message": message, "max_tokens": self.max_tokens}
        else:
            url = self._live_url() + "/chat/send"
            payload = {"provider": "auto", "message": message, "max_tokens": self.max_tokens}
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        hf = os.environ.get("HF_TOKEN")
        key = os.environ.get("RIU_ROUTER_API_KEY")
        if hf:
            headers["Authorization"] = f"Bearer {hf}"
        if key:
            headers["X-API-Key"] = key

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                request = urllib.request.Request(
                    url, data=body, headers=headers, method="POST"
                )
                with urllib.request.urlopen(request, timeout=120) as response:
                    data = json.loads(response.read().decode("utf-8", "replace"))
                return self._extract_text(data)
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", "replace")
                try:
                    raw = json.loads(raw).get("detail", raw)
                except (ValueError, AttributeError):
                    pass
                last_error = RuntimeError(f"HTTP {exc.code}: {raw}")
                if attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
        raise RuntimeError(f"Router no respondió tras 3 intentos: {last_error}")
