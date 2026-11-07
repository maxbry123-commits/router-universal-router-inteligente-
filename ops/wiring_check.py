import sys,os,json,pathlib,re,fnmatch,yaml
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from j2_graph import build
# D-18/D-25: prefijos del codigo de TERCEROS vendorizado. Se evaluan en el codigo propio y
# en las referencias nuevas (los errores de terceros se INFORMAN, no bloquean).
# D-40: al mover chat-router/agentes -> agents/ los prefijos de TERCEROS deben seguir casando
# con la nueva ubicacion (si no, 38.405 referencias vendorizadas pasan a "propias" y bloquean).
# D-148: la clasificacion de TERCEROS pasa de SUBCADENA a RUTA EXACTA (la raiz debe aparecer como
# secuencia COMPLETA de componentes: "agentes-listos" ya no casa dentro de "ops/agentes-listos.txt"
# ni de "xagentes-listos/y"). Con la subcadena, un nombre de fichero que contenga el nombre de una
# raiz hacia pasar codigo PROPIO por TERCEROS y el gate `no_new_unresolved` se debilita en silencio.
# D-148 (b): se anaden las raices de los bundles publicados por la tuberia hf-combined
# (Main_Skills/_staging y Main_Skills/Frontend): 34.623 ficheros de codigo IMPORTADO de fuera
# (Recordly, DESIGN, awesome-design, context7, playwright, plasmic, onlook, webstudio, ...; cada uno
# con su DOWNLOAD_EXTRACT_MANIFEST.json), NO cableado (no estan en ninguna de las 11 entradas) y
# sin revisar por el owner. Sus referencias sin resolver se INFORMAN (tercero_unresolved_reported);
# el codigo PROPIO sigue bloqueando, que es la regla D-08/D-18/D-25/D-40 que ya regia.
VENDORED_ROOTS=(("agentes-listos",),("agentes","frameworks"),("agentes","investigacion"),
                ("agents","agentes-listos"),("agents","frameworks"),("agents","investigacion"),
                ("chatbot","componentes"),("memoria","componentes"),("otros","descartados"),
                ("otros","Prueba"),("descarga-copia",),
                ("Main_Skills","_staging"),("Main_Skills","Frontend"))
def es_tercero(p):
    parts=p.split("/")
    for r in VENDORED_ROOTS:
        n=len(r)
        for i in range(len(parts)-n+1):
            if parts[i:i+n]==list(r):return True
    return False
def run(root,graph=None):
    # D-39: si el job ya construyo el grafo, se reutiliza (el build son ~10 min sobre 374k ficheros).
    root=pathlib.Path(root);g=graph if graph is not None else build(root);res=[]
    def c(n,ok,d=""):res.append({"name":n,"ok":bool(ok),"detail":str(d)[:300]})
    kp=root/"kernel/KERNEL.yaml";k=yaml.safe_load(kp.read_text()) if kp.exists() else {}
    c("kernel_present",bool(k))
    cur={tuple(u) for u in g["unresolved"] if not u[0].startswith("_quarantine/")}
    # D-18 (misma regla que D-08 en j2_graph): los errores de sintaxis del codigo de TERCEROS
    # vendorizado se INFORMAN pero no BLOQUEAN el gate; el codigo propio sigue bloqueando.
    syn_all=[u for u in cur if u[1]=="SYNTAX_ERROR"]
    syn_own=[u for u in syn_all if not es_tercero(u[0])]
    c("no_syntax_errors",not syn_own,f"{len(syn_all)} de terceros (informativo), {len(syn_own)} propios")
    c("third_party_syntax_reported",True,f"{len(syn_all)} errores de sintaxis en codigo de terceros")
    bp=pathlib.Path(os.environ.get("BASELINE",root/"connections/baseline_unresolved.json"))
    if bp.exists():
        b={tuple(x) for x in json.load(open(bp))}
        # D-25: el untrack de los 37 directorios build/ (plan de j4) deja sin resolver referencias
        # del codigo de TERCEROS vendorizado (que importaba esos artefactos). Misma regla que D-18:
        # las referencias nuevas de terceros se INFORMAN; solo las del codigo propio bloquean.
        # D-41: el baseline esta indexado por ruta y un renombrado (lote R2) lo invalidaba.
        # Se compara por (basename, destino): el renombrado conserva el nombre de fichero, asi que
        # la comparacion sigue detectando referencias NUEVAS sin penalizar los movimientos.
        nb={(pathlib.Path(x[0]).name,x[1]) for x in b}
        new_all=sorted(cur-b)
        new_own=[u for u in new_all if not es_tercero(u[0]) and (pathlib.Path(u[0]).name,u[1]) not in nb]
        c("no_new_unresolved",not new_own,f"{len(new_all)} de terceros (informativo), {len(new_own)} propios: {new_own[:3]}")
        c("third_party_unresolved_reported",True,f"{len(new_all)} referencias nuevas en codigo de terceros")
    else:c("baseline_exists",False,"commit j2 baseline_unresolved.json to connections/")
    miss=[e for e in k.get("entrypoints",[]) if not (root/e).exists()]
    c("entrypoints_exist",bool(k.get("entrypoints")) and not miss,(miss or f"{len(k.get('entrypoints',[]))} entrypoints presentes"))
    rp=root/"connections/registry.yaml";conns=(yaml.safe_load(rp.read_text()) or {}).get("connections",[]) if rp.exists() else []
    # D-37: la guia §5 fija los 11 campos obligatorios de cada conexion del registro oficial.
    need=("id","name","source","target","protocol","direction","endpoint","status","dependencies",
          "verification","notes","from","to","via","provides","requires")
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
