from common import *
import shutil,pathlib
def main():
    for k in ["GH_REPO","GH_BRANCH","DATASET_REPO","HF_TOKEN","RUN_ID"]:check(f"env:{k}",bool(os.environ.get(k)))
    check("GH_TOKEN_mode",True,"set" if os.environ.get("GH_TOKEN") else "absent: public repo only")
    free=shutil.disk_usage(os.environ.get("WORK_DIR","/workspace/work")).free/2**30   # G2/G3: el disco que se mide es el del scratch real
    check("disk_free_gb",free>=float(os.environ.get("MIN_FREE_GB","30")),f"{free:.1f}GB")
    v=sh(["git","--version"]).stdout.split()[2];check("git>=2.31",tuple(int(x) for x in v.split(".")[:2])>=(2,31),v)
    br=os.environ.get("TARGET_BRANCH") or os.environ.get("GH_BRANCH")
    r=sh(["git","ls-remote","--heads",f"https://github.com/{os.environ['GH_REPO']}.git",br],check=False)
    check("remote_and_branch",r.returncode==0 and br in r.stdout,f"rc={r.returncode}")
    ops=pathlib.Path(__file__).parent
    # D-108: los jobs del DAG v3 tambien deben estar en la rama.
    miss=[f for f in ["common","j1_inventory","j2_graph","j3_history","j4_plan","j5_apply","j6_rewrite","j6b_swap","j7_mirror","j8_audit","j9_remirror","j10_final_audit","bridge","wiring_check","kernel"] if not (ops/f"{f}.py").exists()]
    check("ops_scripts_present_on_branch",not miss,miss)
    # D-31: el bloque de entrada esta CONGELADO (freeze/VERBATIM). Se valida su SHA-256
    # contra el que registra el kernel (handoff.input_block_sha256): si cambia, el job falla.
    import hashlib as _h
    ibp=pathlib.Path(os.environ.get("KERNEL_DIR","kernel"))/"INPUT_BLOCK.yaml"
    try:
        cur=_h.sha256(ibp.read_bytes()).hexdigest()
        import yaml as _y
        rec=(_y.safe_load(pathlib.Path(os.environ.get("KERNEL_DIR","kernel")+"/KERNEL.yaml").read_text())
             .get("handoff",{}).get("input_block_sha256"))
        check("input_block_sha256_intacto",bool(rec) and cur==rec,f"actual={cur[:12]} registrado={(rec or '-')[:12]}")
    except Exception as e:check("input_block_sha256_intacto",False,str(e)[:120])
    from huggingface_hub import HfApi
    api=HfApi(token=os.environ.get("HF_TOKEN"))
    try:api.whoami();check("hf_token_valid",True)
    except Exception as e:check("hf_token_valid",False,str(e)[:100])
    try:api.create_repo(os.environ["DATASET_REPO"],repo_type="dataset",private=True,exist_ok=True);check("dataset_writable",True)
    except Exception as e:check("dataset_writable",False,str(e)[:100])
    finish()
if __name__=="__main__":run(main)
