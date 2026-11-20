"""install_service_adapters.py — Op3: instala los 4 adapters de SERVICIO en HF.

Contexto: el "Job fix3" del Director pedia 4 modos. Los 4 modos de SERVICIO
(swe_code, swe_free, team_qwe, deployment) NO tenian adapter_config.json: sin
adapter no hay enrute y fix3 daria 0/4. Este script los crea con el MISMO
esquema que los 12 modos de codigo (adapter_type: "service"), actualiza el
manifest.json y deja el CONTRATO de cada modo en swe-code-modes (sin inventar
filas de entrenamiento: un modo de servicio no se entrena, se enruta).

Escrituras: SOLO en Hugging Face (2 repos), por protocolo git, 1 commit por repo.
Idempotente: si el contenido ya es identico, no hay commit.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys

HF_TOKEN = os.environ.get("HF_TOKEN_1_NEW") or os.environ.get("HF_TOKEN")
NS = "COMAND-CENTER-1"
ADAPTERS_REPO = "COMAND-CENTER-1/swe-code-adapters"
MODES_REPO = "COMAND-CENTER-1/swe-code-modes"
WORK = "/workspace/hf_service_adapters"

# Mismos datos que router_llm_hf/service_routes.py en el repo de GitHub.
SERVICE_MODES = {
    "swe_code": {
        "route": "/v1/swe",
        "space": "space-grupo-2-router-llm-hf-1",
        "model": "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
        "local_first": True,
        "description": "SWE CODE con clave: ejecuta en el Space local del Grupo 2.",
    },
    "swe_free": {
        "route": "/v1/swe-free",
        "space": "space-grupo-2-router-llm-hf-3",
        "model": "unsloth/Qwen3.5-0.8B-GGUF",
        "local_first": True,
        "description": "SWE CODE gratuito: mismo codigo, ruta propia y coste cero.",
    },
    "team_qwe": {
        "route": "/v1/team-qwe",
        "space": "space-grupo-2-router-llm-hf-2",
        "model": "LiquidAI/LFM2.5-350M-GGUF",
        "local_first": False,
        "description": "Orquestador multi-agente: cadena de proveedores.",
    },
    "deployment": {
        "route": "/v1/deployment",
        "space": None,
        "model": None,
        "local_first": False,
        "description": "Despliegue: cadena de proveedores + guia de despliegue.",
    },
}


def sh(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("comando fallo: {}\nstdout: {}\nstderr: {}".format(
            " ".join(cmd), proc.stdout.strip(), proc.stderr.strip()))
    return proc.stdout.strip()


def auth_header():
    token = base64.b64encode("{}:{}".format(NS, HF_TOKEN).encode()).decode()
    return "Authorization: Basic {}".format(token)


def git_url(repo):
    """URL de git de HF. Los repos de DATASET van bajo /datasets/."""
    if repo.startswith("COMAND-CENTER-1/") and repo.split("/", 1)[1] in ("swe-code-modes",):
        return "https://huggingface.co/datasets/{}".format(repo)
    return "https://huggingface.co/{}".format(repo)


def clone(repo, dest):
    if os.path.exists(dest) and not os.path.isdir(os.path.join(dest, ".git")):
        # Directorio a medias de un clone fallido: se limpia y se repite.
        import shutil
        shutil.rmtree(dest)
    if os.path.exists(dest):
        sh(["git", "-C", dest, "fetch", "--depth", "5", "origin", "main"])
        sh(["git", "-C", dest, "reset", "--hard", "origin/main"])
    else:
        os.makedirs(dest, exist_ok=True)
        # El repo de modos es PRIVADO: la credencial debe ir en el propio clon.
        sh(["git", "clone", "--depth", "1",
            "-c", "http.extraHeader={}".format(auth_header()),
            git_url(repo), dest])
    sh(["git", "-C", dest, "config", "user.email", "maxbry123@gmail.com"])
    sh(["git", "-C", dest, "config", "user.name", "Maxbry"])
    sh(["git", "-C", dest, "config", "http.extraHeader", auth_header()])


def adapter_config(mode, cfg):
    """Mismo esquema que los 12 adapters de codigo, con adapter_type=service."""
    return {
        "mode": mode,
        "base_model": cfg["model"],
        "dataset_sources": [],
        "dataset_combined": None,
        "dataset_rows": 0,
        "lora": None,
        "lora_repo": None,
        "lora_state": "skip (modo de servicio: no entrenable)",
        "fuentes": [],
        "dataset": None,
        "dataset_repo": MODES_REPO,
        "dataset_path": "{}/service_contract.json".format(mode),
        "lora_path": None,
        "adapter_type": "service",
        "service_route": cfg["route"],
        "local_space": cfg["space"],
        "local_first": cfg["local_first"],
        "description": cfg["description"],
    }


def service_contract(mode, cfg):
    return {
        "mode": mode,
        "adapter_type": "service",
        "service_route": cfg["route"],
        "local_space": cfg["space"],
        "local_model": cfg["model"],
        "local_first": cfg["local_first"],
        "description": cfg["description"],
        "entrenamiento": "no aplica: un modo de servicio se enruta, no se entrena",
        "contrato": {
            "method": "POST",
            "path": cfg["route"],
            "auth": "x-api-key: ROUTER_API_KEY",
            "body": {"model": "auto o id completo", "messages": [{"role": "user", "content": "..."}]},
            "respuesta": {
                "provider": "hf_local | nvidia | groq",
                "mode": mode,
                "service_mode": mode,
                "route": cfg["route"],
                "adapter": {"base_model": cfg["model"], "lora": None, "dataset": None},
            },
            "fallo": "503 con diag (nvidia_keys, groq_keys, ultimo error)",
        },
    }


def write_if_changed(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            if fh.read() == content:
                return False
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return True


def commit_and_push(repo_dir, message):
    status = sh(["git", "-C", repo_dir, "status", "--porcelain"])
    if not status:
        print("  sin cambios -> no hay commit")
        return None
    sh(["git", "-C", repo_dir, "add", "-A"])
    sh(["git", "-C", repo_dir, "commit", "-q", "-F", "-"], ) if False else None
    subprocess.run(["git", "-C", repo_dir, "commit", "-q", "-F", "-"], input=message, text=True, check=True)
    sh(["git", "-C", repo_dir, "push", "origin", "HEAD:main"])
    sha = sh(["git", "-C", repo_dir, "rev-parse", "HEAD"])
    print("  commit: {}".format(sha))
    return sha


def main():
    if not HF_TOKEN:
        print("FATAL: falta HF_TOKEN_1_NEW", file=sys.stderr)
        return 2
    os.makedirs(WORK, exist_ok=True)

    # --- 1) adapters -------------------------------------------------------
    print("== swe-code-adapters ==")
    a_dir = os.path.join(WORK, "swe-code-adapters")
    clone(ADAPTERS_REPO, a_dir)
    changed = 0
    for mode, cfg in SERVICE_MODES.items():
        p = os.path.join(a_dir, mode, "adapter_config.json")
        if write_if_changed(p, json.dumps(adapter_config(mode, cfg), indent=2, ensure_ascii=False) + "\n"):
            changed += 1
            print("  escrito: {}/adapter_config.json".format(mode))
    man_path = os.path.join(a_dir, "manifest.json")
    with open(man_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["total_modes"] = 16
    manifest["service_modes"] = 4
    manifest["generado"] = "2026-11-18"
    manifest.setdefault("modes", {})
    for mode, cfg in SERVICE_MODES.items():
        manifest["modes"][mode] = {
            "mode": mode,
            "adapter": "ok",
            "dataset": "n/a (modo de servicio)",
            "lora": "n/a (modo de servicio)",
            "filas": 0,
            "service_route": cfg["route"],
            "local_space": cfg["space"],
            "notas": ["Modo de servicio: ruta del proxy; no es un modo entrenable."],
        }
    if write_if_changed(man_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"):
        changed += 1
        print("  escrito: manifest.json (16 modos: 12 codigo + 4 servicio)")
    msg = ("feat(adapters): 4 modos de SERVICIO con adapter_config.json (fix3 4/4)\n\n"
           "swe_code (/v1/swe), swe_free (/v1/swe-free), team_qwe (/v1/team-qwe) y\n"
           "deployment (/v1/deployment): mismo esquema que los 12 modos de codigo con\n"
           "adapter_type=service. Sin ellos, el Job fix3 daria 0/4.\n"
           "manifest.json: total_modes 12 -> 16.\n")
    sha_a = commit_and_push(a_dir, msg)

    # --- 2) swe-code-modes (contrato, sin filas inventadas) ------------------
    print("== swe-code-modes ==")
    m_dir = os.path.join(WORK, "swe-code-modes")
    clone(MODES_REPO, m_dir)
    changed = 0
    for mode, cfg in SERVICE_MODES.items():
        p = os.path.join(m_dir, mode, "service_contract.json")
        if write_if_changed(p, json.dumps(service_contract(mode, cfg), indent=2, ensure_ascii=False) + "\n"):
            changed += 1
            print("  escrito: {}/service_contract.json".format(mode))
    idx_path = os.path.join(m_dir, "MODES_SERVICE_4.json")
    idx = {
        "total": 4,
        "nota": "Modos de SERVICIO: se enrutan, no se entrenan. No hay combined.jsonl.",
        "modes": {m: {"route": c["route"], "space": c["space"], "model": c["model"],
                      "local_first": c["local_first"]} for m, c in SERVICE_MODES.items()},
    }
    if write_if_changed(idx_path, json.dumps(idx, indent=2, ensure_ascii=False) + "\n"):
        changed += 1
        print("  escrito: MODES_SERVICE_4.json")
    msg2 = ("feat(modes): contrato de los 4 modos de servicio (sin filas inventadas)\n\n"
            "service_contract.json por modo + MODES_SERVICE_4.json. Un modo de servicio\n"
            "se enruta (ruta del proxy + Space local), no se entrena: no se crea un\n"
            "combined.jsonl con filas de mentira.\n")
    sha_m = commit_and_push(m_dir, msg2)

    print("ADAPTERS_SHA {}".format(sha_a))
    print("MODES_SHA {}".format(sha_m))
    print("OP3_INSTALL_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
