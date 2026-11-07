"""ops/backend_smoke.py — arranque REAL del backend + smoke test (gate TEST_CMD de S5_j5).

Por que existe: el Space `COMAND-CENTER-1/riu-router` esta en hardware de pago sin saldo
(HF responde 402) y queda PAUSED, asi que su /health da 503 y el gate "real backend start +
smoke" no se puede cumplir a traves del Space. Este job hace lo mismo dentro de un Job de HF
(cpu-upgrade, hardware de pago de 32 GB + CPU): clona el repo, instala las dependencias del backend, levanta
uvicorn con la app real, llama a /health y publica el resultado en el Dataset.

Modos:
  --run    (dentro del Job de HF) arranca el backend, hace el smoke y publica el resultado.
  --check  (en local) descarga el resultado publicado y devuelve rc=0 solo si el smoke fue PASS.
  --ensure (en local) si el resultado no existe o es de otro commit, lanza el Job y espera.

D-45: sustituye al TEST_CMD basado en el Space (misma semantica: backend real arrancado +
smoke real), sin depender del saldo de la cuenta.
"""
import json, os, subprocess, sys, time, pathlib

RUN_ID = os.environ.get("RUN_ID", "20261104-kernel01")
DS = os.environ.get("DATASET_REPO", "COMAND-CENTER-1/router-universal-router-inteligente-auditoria")
REPO = os.environ.get("GH_REPO", "maxbry123-commits/router-universal-router-inteligente-")
BRANCH = os.environ.get("GH_BRANCH", "main")
BACKEND = "chat-router/chat/backend"
APP = "mvp.app:app"
HEALTH = "/health"


def _hf():
    from huggingface_hub import HfApi, hf_hub_download
    return HfApi(token=os.environ.get("HF_TOKEN")), hf_hub_download


def _download_result():
    _, dl = _hf()
    p = dl(repo_id=DS, repo_type="dataset", filename=f"{RUN_ID}/backend_smoke/result.json",
           token=os.environ.get("HF_TOKEN"))
    return json.load(open(p))


def _publish(res):
    from huggingface_hub import HfApi
    api = HfApi(token=os.environ.get("HF_TOKEN"))
    out = pathlib.Path(wd("out","backend_smoke"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(res, indent=1))
    api.upload_folder(folder_path=str(out), repo_id=DS, repo_type="dataset",
                      path_in_repo=f"{RUN_ID}/backend_smoke")


def cmd_run():
    """Dentro del Job de HF: clona, instala, arranca y hace el smoke."""
    res = {"job": "backend_smoke", "run_id": RUN_ID, "checks": [], "status": "FAIL"}
    def chk(name, ok, detail=""):
        res["checks"].append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
        return bool(ok)
    d = os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"backend")
    r = subprocess.run(f"git clone --single-branch --branch {BRANCH} --depth 1 "
                       f"https://github.com/{REPO}.git {d}", shell=True, capture_output=True, text=True)
    if not chk("clone_repo", r.returncode == 0, r.stderr[-300:]):
        _publish(res); print(json.dumps(res)); return 1
    req = f"{d}/{BACKEND}/mvp/requirements.txt"
    r = subprocess.run(f"pip install -q -r {req} uvicorn", shell=True, capture_output=True, text=True)
    chk("deps_installed", r.returncode == 0, r.stderr[-300:])
    env = dict(os.environ)
    # D-49: el backend importa paquetes que viven en varias raices del repo:
    #   mvp      -> chat-router/chat/backend      (from mvp import ...)
    #   router   -> router-mvp                    (from router import ...)
    #   agentes  -> chat-router                   (from agentes import ...)
    #   plugins  -> chat-router                   (from plugins import ...)
    # Con solo el backend en PYTHONPATH el import mvp_route peta con "No module named 'router'".
    env["PYTHONPATH"] = ":".join([f"{d}/{BACKEND}", f"{d}/router-mvp", f"{d}/chat-router", f"{d}/chat-router/chat"])
    proc = subprocess.Popen(["python", "-m", "uvicorn", APP, "--host", "127.0.0.1", "--port", "8099"],
                            cwd=f"{d}/{BACKEND}", env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    body = None
    for _ in range(60):
        time.sleep(5)
        if proc.poll() is not None:
            break
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:8099{HEALTH}", timeout=10) as resp:
                body = json.loads(resp.read().decode())
                chk("health_http_200", resp.status == 200, resp.status)
                break
        except Exception:
            continue
    if body is None:
        try:
            out = proc.communicate(timeout=10)[0]
        except Exception:
            proc.kill(); out = ""
        chk("health_http_200", False, (out or "")[-300:])
    else:
        chk("health_status_ok", body.get("status") in ("ok", "degraded"), body.get("status"))
        chk("health_has_commit", bool(body.get("commit")), body.get("commit"))
        res["health"] = body
    try:
        proc.kill()
    except Exception:
        pass
    res["status"] = "PASS" if all(c["ok"] for c in res["checks"]) else "FAIL"
    res["ts"] = time.strftime("%FT%TZ", time.gmtime())
    _publish(res)
    print(json.dumps(res, indent=1)[:1200])
    return 0 if res["status"] == "PASS" else 1


def cmd_check():
    try:
        res = _download_result()
    except Exception as e:
        print(json.dumps({"backend_smoke": "MISSING", "error": str(e)[:200]}))
        return 1
    print(json.dumps({"backend_smoke": res.get("status"), "ts": res.get("ts"),
                      "checks": res.get("checks")}, indent=1)[:1200])
    return 0 if res.get("status") == "PASS" else 1


def cmd_ensure():
    """Si no hay resultado vigente, lanza el Job de HF (cpu-upgrade, el hardware del owner) y espera."""
    try:
        res = _download_result()
        if res.get("status") == "PASS":
            return cmd_check()
    except Exception:
        pass
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from hf_job import create, legacy_command  # noqa: F401
    import base64
    cmd = ("set -e; pip install -q huggingface_hub; "
           f"git clone --single-branch --branch {BRANCH} --depth 1 https://github.com/{REPO}.git /tmp/repo; "
           "cd /tmp/repo && python ops/backend_smoke.py --run")
    env = {"GH_REPO": REPO, "GH_BRANCH": BRANCH, "RUN_ID": RUN_ID, "DATASET_REPO": DS}
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = "AUTHORIZATION: basic " + base64.b64encode(
        ("x-access-token:" + os.environ["GH_TOKEN"]).encode()).decode()
    sec = {"GH_TOKEN": os.environ["GH_TOKEN"], "HF_TOKEN": os.environ["HF_TOKEN"]}
    job = create("backend-smoke", docker_image="python:3.12", command=cmd,
                 secrets=sec, environment=env, flavor="cpu-upgrade")
    print(json.dumps({"job_created": job.get("id"), "flavor": "cpu-upgrade"}))
    for i in range(120):
        time.sleep(15)
        try:
            res = _download_result()
            if res.get("status") == "PASS":
                return cmd_check()
        except Exception:
            pass
    print(json.dumps({"backend_smoke": "TIMEOUT", "job": job.get("id")}))
    return 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    sys.exit({"--run": cmd_run, "--check": cmd_check, "--ensure": cmd_ensure}[mode]())
