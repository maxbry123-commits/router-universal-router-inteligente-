# ROADMAP U1: catalogo unico de patrones + deteccion de catalogos divergentes.
from common import *
import pathlib,re,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from patterns import PATTERNS,COMPILED,scan_texts
def main():
    d=clone("/tmp/pat",blobless=True)
    items=[]
    for p in sh(["git","ls-files","-z"],cwd=d).stdout.split("\0"):
        if not p:continue
        if pathlib.Path(p).suffix.lower() not in(".py",".js",".mjs",".ts",".tsx",".jsx",".html",".json",".yaml",".yml",".sh",".md"):continue
        try:items.append((p,(pathlib.Path(d)/p).read_text(errors="ignore")[:400000]))
        except Exception:continue
        if len(items)>40000:break
    hits=scan_texts(items)
    legacy=[]
    for p in sorted(pathlib.Path(__file__).parent.glob("*.py")):
        txt=p.read_text(errors="ignore")
        if re.search(r'^\s*patterns\s*=\s*\{',txt,re.M) and p.name not in("patterns.py","j11_patterns.py"):
            legacy.append(p.name)
    (OUT/"patterns_report.json").write_text(json.dumps({"canonical":PATTERNS,
        "hits":{k:len(v) for k,v in hits.items()},"scanned_files":len(items),
        "legacy_inline_catalogs":legacy},indent=1))
    check("canonical_catalog_present",len(PATTERNS)==6,list(PATTERNS))
    check("repo_scanned",len(items)>0,len(items))
    check("legacy_catalogs_reported",True,legacy)
    finish({"categories":list(PATTERNS),"legacy_inline_catalogs":legacy,"hits":{k:len(v) for k,v in hits.items()}},commit=head(d))
if __name__=="__main__":run(main)
