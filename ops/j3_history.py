from common import *
import re,collections
WIRE=re.compile(r'(^|/)(vercel\.json|package\.json|requirements[^/]*\.txt|Dockerfile|README\.md|pyproject\.toml)$|(router|route|api|config|connection|registry|endpoint|gateway|motor|engine|shell)[^/]*\.(py|js|ts|json|ya?ml)$|^connections/|^kernel/',re.I)
def main():
    days=os.environ.get("HISTORY_DAYS","30")
    d=clone(wd("h"),since=f"{days} days ago",blobless=True)
    log=sh(["git","log","--since",f"{days} days ago","--name-status","-M","--pretty=format:@@%H|%aI|%an|%s"],cwd=d).stdout
    ev=[];cur=None
    for line in log.splitlines():
        if line.startswith("@@"):
            h,dt,au,sub=line[2:].split("|",3);cur={"commit":h,"date":dt,"author":au,"subject":sub,"changes":[]};ev.append(cur)
        elif line.strip() and cur is not None:
            parts=line.split("\t");cur["changes"].append({"s":parts[0][0],"paths":parts[1:],"wiring":any(WIRE.search(p) for p in parts[1:])})
    if ev:ev[-1]["boundary"]=True   # oldest commit of a shallow window shows whole tree as added: ignore
    ev=[e for e in ev if not e.get("boundary")]
    touched=set();suspects=[];perday=collections.Counter()
    with open(OUT/"wiring_history.jsonl","w") as f:
        for e in ev:
            for c in e["changes"]:touched.update(c["paths"])
            w=[c for c in e["changes"] if c["wiring"]]
            perday[e["date"][:10]]+=len(w)
            if w:
                f.write(json.dumps({**e,"changes":w})+"\n")
                risky=[c for c in w if c["s"] in "DR"]
                if risky:suspects.append({"commit":e["commit"],"date":e["date"],"subject":e["subject"],"risky":risky[:10],"n":len(risky)})
    (OUT/"touched.txt").write_text("\n".join(sorted(touched)))
    suspects.sort(key=lambda s:-s["n"])
    md=["# wiring changelog (auto)",f"window: last {days} days, commits: {len(ev)}",""]
    for day,n in sorted(perday.items(),reverse=True):md.append(f"- {day}: {n} wiring changes")
    md+=["","## suspects (deleted/renamed wiring files)"]+[f"- {s['date'][:10]} {s['commit'][:10]} {s['subject']} ({s['n']})" for s in suspects[:30]]
    (OUT/"wiring_changelog.md").write_text("\n".join(md))
    check("history_loaded",len(ev)>0,len(ev))
    finish({"commits":len(ev),"suspects_top":suspects[:10],"window_days":days},commit=head(d))
if __name__=="__main__":run(main)
