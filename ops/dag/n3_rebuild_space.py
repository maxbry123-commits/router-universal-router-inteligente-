import os, sys, json, pathlib
if os.environ.get("OWNER_GATE")!="APPROVE_N3": sys.exit("N3: owner_gate no aprobado")
from huggingface_hub import HfApi, CommitOperationAdd
OUT=pathlib.Path("out/N3"); OUT.mkdir(parents=True,exist_ok=True)
if (OUT/"rebuild.json").exists(): sys.exit("N3: output exists, abort")
api=HfApi(token=os.environ["HF_TOKEN"])
# solo dispara rebuild, no empuja arbol
api.create_commit(repo_id=os.environ["SPACE_REPO"],repo_type="space",
    operations=[CommitOperationAdd(path_in_repo=".rebuild",path_or_fileobj=b"")],
    commit_message="rebuild via DAG N3")
(OUT/"rebuild.json").write_text(json.dumps({"ok":True,"triggered":True},indent=2))
