from common import *
import csv,collections,pathlib
HEAVY={"node_modules","venv",".venv","__pycache__","dist","build",".next",".cache","site-packages"}
CODE={".py",".js",".mjs",".ts",".tsx",".jsx",".html",".css",".sh"}
CONF={".json",".yaml",".yml",".toml",".md",".txt",".cfg",".ini"}
DATA={".bin",".safetensors",".pt",".pth",".onnx",".gguf",".parquet",".csv",".jsonl",".zip",".tar",".gz",".npy",".pkl",".sqlite",".db"}
def cls(p,sz):
    parts=set(p.split("/"));ext=pathlib.Path(p).suffix.lower()
    if HEAVY&parts:return "heavy"
    if ext in DATA:return "data"
    if ext in CODE:return "code"
    if ext in CONF:return "config"
    return "other_big" if sz>1<<20 else "other"
def main():
    d=clone(wd("r"));root=pathlib.Path(d)
    rows=[];low=collections.defaultdict(list);cnt=collections.Counter();byt=collections.Counter()
    hashes=collections.defaultdict(list);odd=[];sym=[]
    for p in sh(["git","ls-files","-z"],cwd=d).stdout.split("\0"):
        if not p:continue
        f=root/p
        if f.is_symlink():sym.append(p);rows.append((p,0,"symlink",""));continue
        try:sz=f.stat().st_size
        except OSError:continue
        c=cls(p,sz);top="/".join(p.split("/")[:2]);cnt[top]+=1;byt[top]+=sz;low[p.lower()].append(p)
        if " " in p or not p.isascii():odd.append(p)
        h=sha256(f) if sz<(5<<20) and c in("code","config") else ""
        if h:hashes[h].append(p)
        rows.append((p,sz,c,h))
    with open(OUT/"inventory.csv","w",newline="") as fh:
        w=csv.writer(fh);w.writerow(["path","size","class","sha256"]);w.writerows(rows)
    coll=[v for v in low.values() if len(v)>1]
    dups=[v for v in hashes.values() if len(v)>1]
    heavy=[r[0] for r in rows if r[2]=="heavy"]
    check("files_found",len(rows)>0,len(rows))
    check("case_collisions_zero",not coll,coll[:3])   # breaks Windows/macOS clones and moves
    finish({"files":len(rows),"top_by_files":cnt.most_common(15),"top_by_bytes":byt.most_common(15),
            "heavy_tracked":len(heavy),"heavy_sample":heavy[:20],"duplicates_groups":len(dups),"duplicates_sample":dups[:50],
            "odd_paths":len(odd),"odd_sample":odd[:20],"symlinks":sym[:20]},commit=head(d))
if __name__=="__main__":run(main)
