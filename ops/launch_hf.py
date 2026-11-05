"""ops/launch_hf.py — lanza un job del kernel como Job de Hugging Face (32 GB + CPU).

D-64: los jobs pesados (espejo, auditoria, reescritura de historial) NO terminan en LOCAL:
el sandbox reinicia su overlay de /tmp cada 15-20 min y se lleva el clon de 18 GB y el proceso
del job a mitad. En un Job de HF el contenedor vive hasta el techo de 1800 s y tiene 32 GB.

D-65: para estos jobs el clon es COMPLETO (sin --filter=tree:0 ni --sparse): el espejo necesita
el arbol entero y el `git ls-tree` del gate.

Uso: python ops/launch_hf.py <job_id> [--wait] [--timeout 1700]
"""
import base64, json, os, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_job import create  # noqa: E402


def repo_env():
    return {
        "GH_REPO": os.environ.get("GH_REPO", "maxbry123-commits/router-universal-router-inteligente-"),
        "GH_BRANCH": os.environ.get("TARGET_BRANCH") or os.environ.get("GH_BRANCH", "main"),
        "RUN_ID": os.environ.get("RUN_ID", "20261104-kernel01"),
        "DATASET_REPO": os.environ.get("DATASET_REPO", "COMAND-CENTER-1/router-universal-router-inteligente-auditoria"),
        "SPACE_REPO": os.environ.get("SPACE_REPO", "COMAND-CENTER-1/riu-router"),
        "HEALTH_URL": os.environ.get("HEALTH_URL", "https://comand-center-1-riu-router.hf.space/health"),
        "TEST_CMD": os.environ.get("TEST_CMD", "python ops/backend_smoke.py --ensure"),
    }


def build_cmd(job):
    env = repo_env()
    br = env["GH_BRANCH"]
    # D-30: un solo envoltorio `bash -lc`; el rc del script se propaga y el log se imprime.
    return (
        "set +e; pip install -q huggingface_hub pyyaml git-filter-repo >/dev/null 2>&1; "
        f"git clone --single-branch --branch {br} --depth 1 https://github.com/{env['GH_REPO']}.git /tmp/repo > /tmp/job.log 2>&1; "
        "echo clone_rc=$? >> /tmp/job.log; "
        "cd /tmp/repo && python ops/%s.py >> /tmp/job.log 2>&1; echo script_rc=$? >> /tmp/job.log; "
        "cat /tmp/job.log; "
        # D-68: el log del contenedor se publica en el Dataset (evidencia durable del job)
        "echo %s | base64 -d > /tmp/up.py; python /tmp/up.py >> /tmp/job.log 2>&1; "
        "echo upload_rc=$?; cat /tmp/job.log" % (
            job,
            base64.b64encode(
                ("import os\n"
                 "from huggingface_hub import upload_file\n"
                 "kw=dict(repo_id=os.environ['DATASET_REPO'],repo_type='dataset',"
                 "path_in_repo='job-evidencia/%s.log')\n"
                 "try:\n"
                 "    upload_file(path='/tmp/job.log',**kw)\n"
                 "except TypeError:\n"
                 "    upload_file('/tmp/job.log',**kw)\n" % job).encode()).decode())
    )


def main():
    job = sys.argv[1]
    wait = "--wait" in sys.argv
    timeout = 1700
    if "--timeout" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout") + 1])
    env = repo_env()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = "AUTHORIZATION: basic " + base64.b64encode(
        ("x-access-token:" + os.environ["GH_TOKEN"]).encode()).decode()
    for extra in ("AUDIT_JOBS", "WAIT_S", "MIRROR_BASELINE"):
        if extra in os.environ:
            env[extra] = os.environ[extra]
    sec = {"GH_TOKEN": os.environ["GH_TOKEN"], "HF_TOKEN": os.environ["HF_TOKEN"]}
    name = f"kernel-{job}-{int(time.time())}"
    job_info = create(name, docker_image="python:3.12", command=build_cmd(job),
                      secrets=sec, environment=env, flavor="cpu-upgrade")
    print(json.dumps({"job_created": job_info.get("id"), "flavor": "cpu-upgrade",
                      "branch": env["GH_BRANCH"], "job": job}))
    if not wait:
        return 0
    from huggingface_hub import hf_hub_download
    path = f"{env['RUN_ID']}/{job}/result.json"
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(20)
        try:
            p = hf_hub_download(env["DATASET_REPO"], repo_type="dataset", filename=path,
                                token=os.environ["HF_TOKEN"])
            res = json.load(open(p))
            print(json.dumps({"job": job, "status": res.get("status"), "failed": res.get("failed")}))
            return 0 if res.get("status") == "PASS" else 1
        except Exception:
            continue
    print(json.dumps({"job": job, "status": "TIMEOUT"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
