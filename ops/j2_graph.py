from common import *
import ast,re,pathlib,posixpath,collections
JSRE=re.compile(r'''(?:import\s+(?:[^'"]*?from\s+)?|require\(\s*|import\(\s*)['"]([^'"]+)['"]''')
HTMLRE=re.compile(r'''(?:src|href)\s*=\s*['"]([^'"#?]+)''')
DYN=re.compile(r'importlib|__import__|eval\(|exec\(|require\(\s*[^\'"\s)]|import\(\s*[^\'"\s)]')
EXT=(".py",".js",".mjs",".ts",".tsx",".jsx",".html")
def build(root):
    root=pathlib.Path(root)
    files={p for p in sh(["git","ls-files","-z"],cwd=root).stdout.split("\0") if p}
    full={};idx=collections.defaultdict(list)
    for p in files:
        if p.endswith(".py"):
            parts=p[:-3].split("/")
            if parts[-1]=="__init__":parts=parts[:-1]
            if not parts:continue
            full[".".join(parts)]=p
            for i in range(len(parts)):idx[".".join(parts[i:])].append(p)
    def res_py(src,name,lvl,names):
        if lvl:
            pkg=src.split("/")[:-1];pkg=pkg[:len(pkg)-(lvl-1)]
            base=".".join(pkg+([name] if name else []))
            return [full[x] for x in [base]+[f"{base}.{n}" for n in names] if x in full] or None
        h=[x for k in [name]+[f"{name}.{n}" for n in names] for x in idx.get(k,[])]
        if h:return h
        return "EXT" if name.split(".")[0] not in idx else None
    def res_rel(src,spec,exts):
        n=posixpath.normpath(str(pathlib.PurePosixPath(src).parent/spec))
        for c in [n]+[n+e for e in exts]+[n+"/index"+e for e in exts]:
            if c in files:return c
    edges=set();unres=[];dyn=[];absrefs=0
    for p in sorted(files):
        ext=pathlib.Path(p).suffix
        if ext not in EXT:continue
        try:txt=(root/p).read_text(errors="ignore")
        except Exception:continue
        if len(txt)>2_000_000:continue
        if ext!=".html" and DYN.search(txt):dyn.append(p)
        if ext==".py":
            try:tree=ast.parse(txt)
            except SyntaxError:unres.append([p,"SYNTAX_ERROR"]);continue
            for n in ast.walk(tree):
                if isinstance(n,ast.Import):items=[(a.name,0,())for a in n.names]
                elif isinstance(n,ast.ImportFrom):items=[(n.module or "",n.level,tuple(a.name for a in n.names))]
                else:continue
                for name,lvl,names in items:
                    r=res_py(p,name,lvl,names)
                    if r=="EXT":continue
                    if r is None:unres.append([p,("."*lvl)+name])
                    else:edges.update((p,t) for t in r if t!=p)
        else:
            specs=HTMLRE.findall(txt) if ext==".html" else JSRE.findall(txt)
            for s in specs:
                if s.startswith("/") or "://" in s or s.startswith(("data:","mailto:","//")):
                    absrefs+=s.startswith("/");continue
                if ext!=".html" and not s.startswith("."):continue
                t=res_rel(p,s,[".js",".mjs",".ts",".tsx",".jsx",".html",".css"])
                if t:edges.add((p,t))
                else:unres.append([p,s])
    ent=set()
    k=root/"kernel/KERNEL.yaml"
    if k.exists():
        import yaml;ent.update((yaml.safe_load(k.read_text()) or {}).get("entrypoints",[]))
    ent.update(p for p in files if pathlib.PurePosixPath(p).name in("main.py","app.py","index.html","server.js","shell.html","shell.js","Dockerfile","vercel.json","package.json"))
    return {"nodes":len(files),"edges":sorted(map(list,edges)),"unresolved":unres,"dynamic":dyn,"entrypoints":sorted(ent),"abs_refs":absrefs}
def main():
    d=clone("/tmp/g");g=build(d)
    (OUT/"graph.json").write_text(json.dumps(g))
    (OUT/"baseline_unresolved.json").write_text(json.dumps(g["unresolved"]))  # commit to connections/ after review
    check("graph_built",len(g["edges"])>0,len(g["edges"]))
    check("no_syntax_errors",not [u for u in g["unresolved"] if u[1]=="SYNTAX_ERROR"],[u for u in g["unresolved"] if u[1]=="SYNTAX_ERROR"][:5])
    finish({"edges":len(g["edges"]),"unresolved":len(g["unresolved"]),"dynamic_hosts":len(g["dynamic"]),
            "entrypoints":g["entrypoints"][:30],"unresolved_sample":g["unresolved"][:30]},commit=head(d))
if __name__=="__main__":run(main)
