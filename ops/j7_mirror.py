from common import *
import urllib.request,time
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    sp=need("SPACE_REPO");api=HfApi(token=need("HF_TOKEN"))
    d=clone("/tmp/s");sha=head(d)
    r=wc(d);check("wiring_check_before_mirror",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish(commit=sha)
    api.upload_folder(folder_path=d,repo_id=sp,repo_type="space",commit_message=f"mirror {sha[:12]}",
        ignore_patterns=[".git/**","_quarantine/**","**/node_modules/**","**/__pycache__/**"])
    hu=os.environ.get("HEALTH_URL");wait=int(os.environ.get("WAIT_S","600"));t0=time.time();seen=None;stage=None
    while time.time()-t0<wait:
        stage=str(api.get_space_runtime(sp).stage)
        if "RUNNING" in stage and hu:
            try:
                seen=json.loads(urllib.request.urlopen(hu,timeout=15).read()).get("commit")
                if seen and sha.startswith(seen[:12]):break
            except Exception:pass
        time.sleep(20)
    check("space_RUNNING","RUNNING" in str(stage),stage)
    check("health_url_set",bool(hu),"add GET /health -> {commit} (kernel R4)")
    check("health_commit_equals_HEAD",bool(seen) and sha.startswith(seen[:12]),f"seen={seen} head={sha[:12]}")
    finish({"space":sp,"head":sha},commit=sha)
if __name__=="__main__":run(main)
