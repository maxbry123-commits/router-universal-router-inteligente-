import sys,os,json,pathlib,re,fnmatch,yaml
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from j2_graph import build
def run(root):
    root=pathlib.Path(root);g=build(root);res=[]
    def c(n,ok,d=""):res.append({"name":n,"ok":bool(ok),"detail":str(d)[:300]})
    kp=root/"kernel/KERNEL.yaml";k=yaml.safe_load(kp.read_text()) if kp.exists() else {}
    c("kernel_present",bool(k))
    cur={tuple(u) for u in g["unresolved"] if not u[0].startswith("_quarantine/")}
    # D-18 (misma regla que D-08 en j2_graph): los errores de sintaxis del codigo de TERCEROS
    # vendorizado se INFORMAN pero no BLOQUEAN el gate; el codigo propio sigue bloqueando.
    VENDORED=("agentes-listos/","agentes/frameworks/","agentes/investigacion/","chatbot/componentes/",
              "memoria/componentes/","otros/descartados/","otros/Prueba/","descarga-copia/")
    es_tercero=lambda p:any(k in p for k in VENDORED)
    syn_all=[u for u in cur if u[1]=="SYNTAX_ERROR"]
    syn_own=[u for u in syn_all if not es_tercero(u[0])]
    c("no_syntax_errors",not syn_own,f"{len(syn_all)} de terceros (informativo), {len(syn_own)} propios")
    c("third_party_syntax_reported",True,f"{len(syn_all)} errores de sintaxis en codigo de terceros")
    bp=pathlib.Path(os.environ.get("BASELINE",root/"connections/baseline_unresolved.json"))
    if bp.exists():
        b={tuple(x) for x in json.load(open(bp))};c("no_new_unresolved",cur<=b,sorted(cur-b)[:5])
    else:c("baseline_exists",False,"commit j2 baseline_unresolved.json to connections/")
    miss=[e for e in k.get("entrypoints",[]) if not (root/e).exists()]
    c("entrypoints_exist",bool(k.get("entrypoints")) and not miss,miss or "entrypoints empty")
    rp=root/"connections/registry.yaml";conns=(yaml.safe_load(rp.read_text()) or {}).get("connections",[]) if rp.exists() else []
    need=("id","from","to","via","provides","requires","status")
    bad=[x.get("id") for x in conns if not all(q in x for q in need) or x["status"] not in("pending_audit","active","broken") or (x["status"]=="active" and not x.get("evidence"))]
    c("registry_valid",rp.exists() and not bad,bad[:5] or ("missing registry" if not rp.exists() else ""))
    dom=k.get("domains",{});decl={(x["from"],x["to"]) for x in conns if "from" in x}
    dom_of=lambda p:next((n for n,pre in dom.items() if p.startswith(pre+"/") or p==pre),None)
    viol=sorted({(dom_of(a),dom_of(b)) for a,b in g["edges"] if dom_of(a) and dom_of(b) and dom_of(a)!=dom_of(b) and (dom_of(a),dom_of(b)) not in decl})
    c("architecture_lint",k.get("lint_mode","warn")=="warn" or not viol,f"{len(viol)} undeclared cross-domain: {viol[:5]}")
    vj=root/"vercel.json"
    if vj.exists():
        try:
            rw=json.load(open(vj)).get("rewrites",[]);dead=[r["destination"] for r in rw if isinstance(r.get("destination"),str) and not r["destination"].startswith("http") and not re.search(r"[:*(]",r["destination"]) and not (root/r["destination"].lstrip("/")).exists()]
            c("vercel_destinations_exist",not dead,dead[:5])
        except Exception as e:c("vercel_json_parse",False,str(e))
    rd=root/"README.md"
    if rd.exists():
        m=re.search(r"^app_file:\s*(\S+)",rd.read_text(errors="ignore"),re.M)
        if m:c("space_app_file_exists",(root/m.group(1)).exists(),m.group(1))
    return {"ok":all(x["ok"] for x in res),"checks":res}
if __name__=="__main__":
    r=run(sys.argv[1] if len(sys.argv)>1 else ".");print(json.dumps(r,indent=1));sys.exit(0 if r["ok"] else 1)
