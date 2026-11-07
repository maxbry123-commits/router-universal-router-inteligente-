# xray_auditor.py
import os
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import List, Dict

class XRayAuditor:
    """
    Implementación Python de la GUÍA DEL AGENTE X-RAY.
    Fase 0: Preflight -> Fase 1: Inventario -> Fase 2: Símbolos -> Fase 6: Huecos.
    """
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.state = {"commit_sha": self._get_commit(), "files": {}}

    def _get_commit(self) -> str:
        try:
            return subprocess.check_output(["git", "-C", str(self.repo_path), "rev-parse", "HEAD"]).decode().strip()
        except:
            return "UNKNOWN"

    def preflight(self) -> dict:
        """Fase 0: Registra commit, rama, lenguajes."""
        extensions = set()
        for root, _, files in os.walk(self.repo_path):
            for f in files:
                ext = Path(f).suffix
                if ext:
                    extensions.add(ext)
        return {"commit_sha": self.state["commit_sha"], "extensions": list(extensions)}

    def inventory(self) -> dict:
        """Fase 1: Hash y líneas de cada archivo."""
        inventory = {}
        for root, _, files in os.walk(self.repo_path):
            if ".git" in root: continue
            for f in files:
                full_path = Path(root) / f
                rel_path = str(full_path.relative_to(self.repo_path))
                try:
                    content = full_path.read_bytes()
                    inventory[rel_path] = {
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "lines": len(content.splitlines())
                    }
                except:
                    inventory[rel_path] = {"sha256": "UNREADABLE", "lines": 0}
        self.state["files"] = inventory
        return inventory

    def symbols(self) -> dict:
        """Fase 2: Extrae funciones y clases usando AST (solo Python)."""
        symbols = {}
        for rel_path in self.state["files"]:
            if not rel_path.endswith(".py"): continue
            full_path = self.repo_path / rel_path
            try:
                tree = ast.parse(full_path.read_text(encoding="utf-8"))
                funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                symbols[rel_path] = {"functions": funcs, "classes": classes}
            except:
                symbols[rel_path] = {"error": "PARSE_ERROR"}
        return symbols

    def detect_gaps(self) -> list:
        """Fase 6: Detecta huecos (ej. archivos sin tests, TODO/FIXME)."""
        gaps = []
        for rel_path in self.state["files"]:
            full_path = self.repo_path / rel_path
            if rel_path.endswith(".py"):
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                if "TODO" in content or "FIXME" in content:
                    gaps.append({"file": rel_path, "type": "TODO/FIXME"})
                if "test" not in rel_path.lower() and not any("test" in f for f in self.state["files"]):
                    gaps.append({"file": rel_path, "type": "MISSING_TEST"})
        return gaps

    def run(self) -> dict:
        """Ejecuta la auditoría completa."""
        pre = self.preflight()
        inv = self.inventory()
        sym = self.symbols()
        gaps = self.detect_gaps()
        return {
            "preflight": pre,
            "inventory_count": len(inv),
            "symbols": sym,
            "gaps": gaps
        }
