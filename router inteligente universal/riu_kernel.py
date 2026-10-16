"""RIU kernel RETIRADO a bootstrap-sin-Jobs (2026-10-16).

Antes este supervisor hacia HfApi.run_job/cancel_job del Router cpu-basic,
publicaba *.hf.jobs en LIVE_URL.json y tick() renovaba el Job (--watch).
Ahora solo queda la hidratacion del banco de claves para el Space permanente:
`python riu_kernel.py` -> pone los secretos del banco en el entorno del proceso.
"""
import os,json,io,tarfile,pathlib,sys,base64,gzip,urllib.request
from huggingface_hub import HfFileSystem
NS="COMAND-CENTER-1"
BASE="buckets/"+NS+"/yaiwes-memoria-storage/router-inteligente-universal"
def fs(): return HfFileSystem(token=os.environ["HF_TOKEN"],skip_instance_cache=True)
def _hf_token_vivo(v):
    # el nombre de la credencial no manda: se prueba cada token habilitado del provider huggingface contra whoami-v2 y
    # gana el primero que responda 200; si ninguno vale, fail-closed (nunca se imprime el token)
    for r in v.list():
        if r["provider"]=="huggingface" and r["enabled"] and "hash" not in r["account"]:
            try:
                tok=v.get_secret(r["credential_ref"])
                req=urllib.request.Request("https://huggingface.co/api/whoami-v2",headers={"Authorization":"Bearer "+tok})
                with urllib.request.urlopen(req,timeout=15) as r_:
                    if r_.status==200:return tok
            except Exception:pass
    raise RuntimeError("GAP_HF_SIN_TOKEN_VALIDO")
def hydrate():
    tar=tarfile.open(fileobj=io.BytesIO(fs().cat_file(BASE+"/codigo/router-bundle.tar.gz")),mode="r:gz")
    tar.extractall("/tmp/kernel-bank",filter="data")
    sys.path.insert(0,"/tmp/kernel-bank/router inteligente universal/Banco de claves")
    from secret_bank.vault import Vault
    p=pathlib.Path("/tmp/kernel-vault.db")
    p.write_bytes(gzip.decompress(base64.b64decode(fs().cat_file(BASE+"/banco/vault.db.gz.b64"))))
    v=Vault(p).unlock(os.environ["RIU_VAULT_PASSPHRASE"])
    os.environ["HF_TOKEN"]=_hf_token_vivo(v)  # sin hardcode: la primera credencial habilitada de huggingface que valide 200
    os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]=v.get_secret("github/director-full")
    os.environ["RIU_ROUTER_API_KEY"]=v.get_secret("router/runtime-admin-32gb")
    os.environ["RIU_DIRECTOR_KEY_HASH"]=v.get_secret("router/runtime-director-hash")
    keys={}
    for r in v.list():
        if r["enabled"] and r["provider"]=="router" and "hash" not in r["account"]:
            try:keys[v.get_secret(r["credential_ref"])]= "chat-ui" if "chat-ui" in r["account"] else r["account"]
            except Exception:pass
    os.environ["RIU_AGENT_API_KEYS"]=json.dumps(keys)
    os.environ["RIU_AGENT_API_KEYS_2"]="{}"
    os.environ["RIU_PUBLIC_CHAT_KEY"]=v.get_secret("router/chat-ui-director")
if __name__=="__main__":
    hydrate()
    print(json.dumps({"status":"HYDRATED","nota":"sin Jobs: bootstrap solo, el proceso padre lanza uvicorn"}),flush=True)
