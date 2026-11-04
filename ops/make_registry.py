# ops/make_registry.py — ROADMAP R1 (job: manual+agent): escribe connections/registry.yaml
# desde el grafo REAL de j2_graph. Nada se declara activo sin evidencia (§5 L1225): todo pending_audit.
import json,sys,pathlib,yaml,collections
sys.path.insert(0,str(pathlib.Path(__file__).parent))
GRAPH=sys.argv[1] if len(sys.argv)>1 else "/tmp/out/j2_graph/graph.json"
K=pathlib.Path("kernel/KERNEL.yaml")
k=yaml.safe_load(K.read_text());dom=k.get("domains",{})
def dom_of(p):
    best=None
    for n,pre in dom.items():
        if p==pre or p.startswith(pre+"/"):
            if best is None or len(pre)>len(dom[best]):best=n
    return best
g=json.load(open(GRAPH))
pairs=collections.defaultdict(list)
for a,b in g["edges"]:
    da,db=dom_of(a),dom_of(b)
    if da and db and da!=db:pairs[(da,db)].append([a,b])
out=[]
for i,((a,b),paths) in enumerate(sorted(pairs.items()),1):
    out.append({"id":f"CON-{i:03d}","from":a,"to":b,"via":"gateway_pending_audit",
        "provides":b,"requires":a,"status":"pending_audit","evidence":None,
        "observed_paths":paths[:5],"observed_edges":len(paths)})
doc={"generated_by":"ops/make_registry.py","source_graph":"j2_graph",
     "rule":"todo pending_audit hasta verificacion con evidencia (§5)","connections":out}
pathlib.Path("connections/registry.yaml").write_text(yaml.safe_dump(doc,sort_keys=False,allow_unicode=True))
print(json.dumps({"connections":len(out),"cross_domain_pairs":len(pairs),
                  "from":sorted({p[0] for p in pairs}),"to":sorted({p[1] for p in pairs})},indent=1))
