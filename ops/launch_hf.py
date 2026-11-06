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
        # D-100: WORK_DIR del job. Dentro del contenedor de HF /tmp es local del contenedor
        # (el problema D-64 es del overlay del sandbox), asi que el scratch del job va a un
        # subdirectorio propio y se crea antes de clonar.
        "WORK_DIR": os.environ.get("WORK_DIR", "/tmp/work"),
    }


def build_cmd(job):
    env = repo_env()
    br = env["GH_BRANCH"]
    # D-30: un solo envoltorio `bash -lc`; el rc del script se propaga y el log se imprime.
    # D-100: clon LIGERO con filtro de blobs + sparse-checkout de las 3 carpetas que el job
    # necesita (ops/, connections/, kernel/). El clon COMPLETO (373.420 ficheros) hacia morir el
    # job en el techo de 1800 s (medido: 1798 s y 1796 s en los dos ultimos jobs). Con filtro el
    # clon es de MB y el ARBOL git completo sigue disponible para `git ls-tree` (gate baseline).
    return (
        "set +e; pip install -q huggingface_hub pyyaml git-filter-repo >/dev/null 2>&1; "
        f"mkdir -p {env.get('WORK_DIR','/tmp/work')}; "
        f"git clone --single-branch --branch {br} --depth 1 --filter=blob:none --sparse https://github.com/{env['GH_REPO']}.git /tmp/repo > /tmp/job.log 2>&1; "
        "echo clone_rc=$? >> /tmp/job.log; "
        "git -C /tmp/repo sparse-checkout set ops connections kernel >> /tmp/job.log 2>&1; echo sparse_rc=$? >> /tmp/job.log; "
        # D-101: el log del contenedor se escribe a fichero y solo se volcaba AL FINAL, asi que
        # un job que se colgaba en el clon se consumia su techo de 30 min a ciegas (job
        # 6aed575d0e0338d1bb80e13a: ERROR 'Job timeout' sin una linea de log). Ahora cada fase
        # hace tail a stdout y el log se ve en vivo en la API de HF.
        "echo '--- fase: clon ---' >> /tmp/job.log; tail -n 20 /tmp/job.log; "
        "cd /tmp/repo && python ops/%s.py >> /tmp/job.log 2>&1; echo script_rc=$? >> /tmp/job.log; "
        "echo '--- fase: script ---' >> /tmp/job.log; tail -n 40 /tmp/job.log; "
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
    timeout = int(os.environ.get("HF_JOB_TIMEOUT", "3600")) + 300  # D-100: el waiter supera al timeout del job
    if "--timeout" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout") + 1])
    env = repo_env()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = "AUTHORIZATION: basic " + base64.b64encode(
        ("x-access-token:" + os.environ["GH_TOKEN"]).encode()).decode()
    # D-100: MODE y WORK_DIR tambien viajan. Sin MODE, j6b_swap (MODE=swap) empuja a main
    # sin que nadie lo pida; sin WORK_DIR, el clon ligero del job no tiene directorio padre.
    for extra in ("AUDIT_JOBS", "WAIT_S", "MIRROR_BASELINE", "MIRROR_LIGHT", "MODE", "WORK_DIR"):
        if extra in os.environ:
            env[extra] = os.environ[extra]
    sec = {"GH_TOKEN": os.environ["GH_TOKEN"], "HF_TOKEN": os.environ["HF_TOKEN"]}
    name = f"kernel-{job}-{int(time.time())}"
    # D-100: timeout explicito del Job de HF (R6 del INPUT BLOCK) + waiter local que lo supera.
    job_timeout = int(os.environ.get("HF_JOB_TIMEOUT", "3600"))
    job_info = create(name, docker_image="python:3.12", command=build_cmd(job),
                      secrets=sec, environment=env, flavor="cpu-upgrade", timeout=job_timeout)
    print(json.dumps({"job_created": job_info.get("id"), "flavor": "cpu-upgrade",
                      "branch": env["GH_BRANCH"], "job": job, "job_timeout": job_timeout}))
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
