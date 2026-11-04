#!/usr/bin/env python3
"""
ADAPTADOR DE TRANSPORTE (NO es el JOB 1 ni el JOB 2 de la guia).
Desviacion declarada del mecanismo de la guia (L24 "Clonar GitHub conservando el historial",
L535/L537 "git clone ... GH_TOKEN"): el repo canonico es privado y la cuenta HF no tiene
secret GH_TOKEN. La via sancionada por el contrato (references/conexiones.md L13, L29-31,
L70) es el Router RIU. Por eso el flujo se parte en dos fases sobre el MISMO archivo:

  --mode acquire  (se ejecuta donde hay clave del Router: el orquestador)
        Recoge la evidencia cruda (ramas, commits, deltas por commit, escaneo de contenido
        en el tip de cada rama, raiz) y la publica en el Dataset de informes.
  --mode analyze  (se ejecuta como Hugging Face Job, solo con HF_TOKEN)
        Consume la evidencia, produce los artefactos de la guia y los sube al Dataset.

DESVIACIONES DECLARADAS (van dentro de cada artefacto como "deviation_notes"):
 D1 transporte=api_github_via_router_riu en vez de git clone (repo privado, sin GH_TOKEN).
 D2 cobertura git-grep reducida: deltas por commit + escaneo en el tip de cada rama; se
    registra por ref: files_in_tree, files_scanned, files_skipped, truncations.
    COMPLETITUD: si files_scanned != files_in_tree hay truncamiento -> esa ref NO puede
    producir REMOVED ni BROKEN_CANDIDATE, solo UNKNOWN (guia L347, L1225).
 D3 semantica de fetch distinta por Job: JOB 1 = todas las ramas (L215/L222 --all);
    JOB 2 = solo la rama del proyecto (L386-387 --single-branch).
 D4 git bisect no disponible (requiere clon local).
 D5 MAX_COMMITS acota el alcance del audit (guia L168) -> se declara como techo.

CLASIFICACION (guia L84-91): PRESERVED | REMOVED | MODIFIED | NEW | BROKEN_CANDIDATE | UNKNOWN.
Bin de archivos (owner, taxonomia no literal): skill | plan | cableado_antes | cableado_despues
 | no_cableado | basura. "basura" es DESTINO/ESTADO, nunca borrado (guia L1091, L1088, L1457).
"""
import argparse, json, os, re, time
from datetime import datetime, timezone

ROUTER = os.environ.get("RIU_ROUTER_URL", "https://comand-center-1-riu-router.hf.space/mcp")
REPO = os.environ.get("GH_REPO", "maxbry123-commits/router-universal-router-inteligente-")
BRANCH = os.environ.get("GH_BRANCH", "main")
HF_REPORT_REPO = os.environ.get("HF_REPORT_REPO", "COMAND-CENTER-1/router-universal-router-inteligente-auditoria")
MAX_COMMITS = int(os.getenv("MAX_COMMITS", "500"))
SCAN_MAX = int(os.getenv("SCAN_MAX", "40"))
SCAN_EXT = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".py", ".js", ".ts", ".tsx",
            ".jsx", ".mjs", ".cjs", ".sh", ".bash", ".md", ".txt", ".env", ".example"}
WIRE_HINTS = ("manifest", "plugin", "cableado", "wiring", "loop", "watchdog", "cola", "router",
              "api", "config", "setting", "registry", "mcp", "deepseek", "hermes", "vercel",
              "huggingface", "hf_", "package.json", "requirements", "docker", "compose",
              "makefile", "workflow", "env", "skill", "agents.md")
PATTERNS = {
    "http": r"https?://|fetch\(|axios|requests\.|httpx|aiohttp",
    "mcp": r"\bMCP\b|tools/list|tools/call|streamable|stdio",
    "endpoints": r"BASE_URL|API_URL|ENDPOINT|SERVICE_URL|/api/",
    "agents": r"agent|orchestrator|specialist|handoff",
    "engines": r"hermes|deepseek|engine|provider",
    "imports": r"^\s*(import |from |require\()",
}
COMPILED = {k: re.compile(v, re.M) for k, v in PATTERNS.items()}
DEV = ["D1 transport=api_github_via_router_riu (sin git clone; repo privado y sin secret GH_TOKEN)",
       "D2 cobertura git-grep reducida + garantia de completitud (scan incompleto => UNKNOWN, nunca REMOVED)",
       "D3 JOB1=todas las ramas; JOB2=solo la rama del proyecto",
       "D4 git bisect no disponible (requiere clon local)",
       "D5 MAX_COMMITS=%d acota el alcance del audit (guia L168)" % MAX_COMMITS,
       "Nota guia L347: removed_candidates contiene candidatos, no conexiones rotas confirmadas"]
STATS = {"api_calls": 0, "truncations": 0, "leer_calls": 0, "commits_examined": 0,
         "commits_total_available": 0, "files_scanned": 0, "files_skipped": 0, "errors": 0}


def redact(t):
    t = re.sub(r"(?i)(token|password|secret|api_key)(\s*[:=]\s*)['\"]?[^'\"\s,]+", r"\1\2[REDACTED]", t)
    t = re.sub(r"(https?://)[^/@\s]+@", r"\1[REDACTED]@", t)
    return t[:400]


def _req(method, url, body=None, headers=None, timeout=180):
    import urllib.request
    r = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def mcp(tool, args, timeout=180):
    key = os.environ.get("RIU_ROUTER_API_KEY") or os.environ.get("UNIVERSAL_KEY") or ""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    raw = _req("POST", ROUTER, body, {"Content-Type": "application/json", "X-API-Key": key,
                                      "Authorization": "Bearer " + key}, timeout)
    d = json.loads(raw)
    c = d.get("result", {}).get("content", [])
    return c[0]["text"] if c else ""


def gh_api(path):
    STATS["api_calls"] += 1
    raw = mcp("github_api", {"metodo": "GET", "ruta": path})
    try:
        return json.loads(raw).get("data"), raw, False
    except Exception:
        STATS["truncations"] += 1
        return None, raw, True


def gh_read(path, ref):
    STATS["leer_calls"] += 1
    try:
        return mcp("github_leer", {"repo": REPO, "ruta": path, "rama": ref})
    except Exception:
        STATS["errors"] += 1
        return ""


def scan_content(path, content):
    out = []
    if not content or path.endswith((".lock", ".map")):
        return out
    for cat, rx in COMPILED.items():
        for m in rx.finditer(content):
            ln = content.count("\n", 0, m.start()) + 1
            end = content.find("\n", m.start())
            line = content[m.start():end if end != -1 else len(content)]
            out.append({"category": cat, "reference": redact("%s:%d:%s" % (path, ln, line.strip()))})
    return out


def list_branches():
    data, raw, _ = gh_api("/repos/%s/branches?per_page=100" % REPO)
    out = []
    if isinstance(data, list):
        for b in data:
            out.append({"name": b.get("name"), "sha": (b.get("commit") or {}).get("sha")})
    else:
        for m in re.finditer(r'"name":\s*"([^"]+)"[^}]*?"sha":\s*"([0-9a-f]{40})"', raw):
            out.append({"name": m.group(1), "sha": m.group(2)})
    seen, uniq = set(), []
    for b in out:
        if b["name"] and b["name"] not in seen:
            seen.add(b["name"])
            uniq.append(b)
    return uniq


def list_commits(branch):
    commits, page = [], 1
    while page <= 400:
        data, raw, _ = gh_api("/repos/%s/commits?sha=%s&per_page=3&page=%d" % (REPO, branch, page))
        got = []
        if isinstance(data, list):
            for c in data:
                cm = c.get("commit", {})
                got.append({"sha": c.get("sha"), "date": (cm.get("author") or {}).get("date", ""),
                            "message": (cm.get("message") or "").split("\n")[0], "branch": branch})
        else:
            for m in re.finditer(r'"sha":\s*"([0-9a-f]{40})"(.{0,900}?)"date":\s*"([^"]+)"', raw, re.S):
                got.append({"sha": m.group(1), "date": m.group(3), "message": "", "branch": branch})
        if not got:
            break
        commits.extend(got)
        if len(got) < 3:
            break
        page += 1
    return commits


def tree_paths(sha):
    data, raw, trunc = gh_api("/repos/%s/git/trees/%s?recursive=1" % (REPO, sha))
    paths = []
    if isinstance(data, dict) and data.get("tree"):
        for e in data["tree"]:
            if e.get("type") == "blob":
                paths.append({"path": e.get("path"), "size": e.get("size", 0)})
    else:
        for m in re.finditer(r'"path":\s*"([^"]+)"\s*,\s*"mode":\s*"[^"]*"\s*,\s*"type":\s*"blob"\s*,\s*"sha":\s*"[0-9a-f]+"(?:\s*,\s*"size":\s*(\d+))?', raw):
            paths.append({"path": m.group(1), "size": int(m.group(2) or 0)})
    return paths, trunc


def prioritize(paths):
    def score(p):
        path = p["path"].lower()
        s = 0
        if any(h in path for h in WIRE_HINTS):
            s -= 100
        if path.count("/") == 0:
            s -= 40
        if os.path.splitext(path)[1] not in SCAN_EXT:
            s += 60
        if p.get("size", 0) > 400000:
            s += 50
        return s
    return sorted(paths, key=score)


def commit_detail(sha):
    data, raw, trunc = gh_api("/repos/%s/commits/%s" % (REPO, sha))
    files, patches = [], []
    if isinstance(data, dict) and data.get("files"):
        for f in data["files"]:
            files.append({"filename": f.get("filename"), "status": f.get("status")})
            if f.get("patch"):
                patches.append({"filename": f.get("filename"), "patch": f.get("patch")})
    else:
        for m in re.finditer(r'"filename":\s*"([^"]+)"\s*,\s*"status":\s*"([A-Z])"', raw):
            files.append({"filename": m.group(1), "status": m.group(2)})
        for m in re.finditer(r'"patch":\s*"((?:[^"\\]|\\.){0,2500})"', raw):
            patches.append({"filename": None, "patch": m.group(1)})
    return files, patches, trunc


def acquire():
    t0 = time.time()
    branches = list_branches()
    head = next((b["sha"] for b in branches if b["name"] == BRANCH), "")
    allc = []
    for b in branches:
        allc.extend(list_commits(b["name"]))
    seen = {}
    for c in allc:
        seen.setdefault(c["sha"], c)
    ordered = sorted(seen.values(), key=lambda c: c.get("date") or "", reverse=True)[:MAX_COMMITS]
    STATS["commits_total_available"] = len(seen)
    deleted, renamed, hist = [], [], []
    for c in ordered:
        files, patches, _ = commit_detail(c["sha"])
        STATS["commits_examined"] += 1
        for f in files:
            if f["status"] == "D":
                deleted.append({"file": f["filename"], "commit": c["sha"], "date": c.get("date")})
            elif f["status"] == "R":
                renamed.append({"file": f["filename"], "commit": c["sha"], "date": c.get("date")})
        hist.append("%s|%s|%s" % (c["sha"], c.get("date", ""), c.get("message", "")))
        for p in patches:
            if p.get("patch"):
                for line in p["patch"].split("\n"):
                    if line.startswith("+") and not line.startswith("+++"):
                        for cat, rx in COMPILED.items():
                            if rx.search(line[1:]):
                                hist.append("PATCH\t%s\t%s\t%s" % (cat, c["sha"], redact(line[1:])))
    branch_scans = {}
    for b in branches:
        paths, trunc = tree_paths(b["sha"])
        cand = prioritize(paths)[:SCAN_MAX]
        refs, scanned = [], 0
        for p in cand:
            content = gh_read(p["path"], b["name"])
            if content and not content.startswith("ERROR"):
                scanned += 1
                STATS["files_scanned"] += 1
                refs.extend(scan_content(p["path"], content))
            else:
                STATS["files_skipped"] += 1
        skipped = len(paths) - scanned
        STATS["files_skipped"] += skipped
        branch_scans[b["name"]] = {"sha": b["sha"], "refs": refs, "files_in_tree": len(paths),
                                   "files_scanned": scanned, "files_skipped": skipped,
                                   "tree_truncated": trunc,
                                   "complete": (not trunc) and scanned == len(paths)}
    data, raw, trunc = gh_api("/repos/%s/contents/" % REPO)
    root = []
    if isinstance(data, list):
        for e in data:
            root.append({"name": e.get("name"), "type": e.get("type"), "size": e.get("size"), "sha": e.get("sha")})
    else:
        for m in re.finditer(r'"name":\s*"([^"]+)"\s*,\s*"path":\s*"[^"]*"\s*,\s*"sha":\s*"([0-9a-f]{40})"(?:\s*,\s*"size":\s*(\d+))?', raw):
            root.append({"name": m.group(1), "type": "file", "size": int(m.group(3) or 0), "sha": m.group(2)})
    root_files = []
    for e in root:
        if e["type"] == "file" and (e.get("size") or 0) < 200000:
            c = gh_read(e["name"], BRANCH)
            root_files.append({"name": e["name"], "size": e.get("size"), "sha": e.get("sha"),
                               "content": c if c and not c.startswith("ERROR") else ""})
    pack = {"repository": REPO, "branch": BRANCH, "head": head,
            "transport": "api_github_via_router_riu", "deviation_notes": DEV,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "branches": branches, "commits": ordered, "commits_total_available": STATS["commits_total_available"],
            "commits_examined": STATS["commits_examined"], "deleted_files": deleted,
            "renamed_files": renamed, "history": hist, "branch_scans": branch_scans,
            "root": root, "root_files": root_files, "stats": STATS, "elapsed_sec": int(time.time() - t0)}
    path = os.environ.get("PACK_PATH", "/tmp/pack.json")
    open(path, "w").write(json.dumps(pack, ensure_ascii=False))
    print("ACQUIRE DONE: commits=%d branches=%d refs=%d files_scanned=%d skipped=%d -> %s"
          % (STATS["commits_examined"], len(branches), sum(len(v["refs"]) for v in branch_scans.values()),
             STATS["files_scanned"], STATS["files_skipped"], path))
    return pack


def analyze(pack, prefix_wiring=True, prefix_root=True):
    OUT = os.environ.get("OUT_DIR", "/tmp/audit")
    os.makedirs(OUT, exist_ok=True)
    head = pack.get("head") or "head"
    scans = pack.get("branch_scans", {})
    complete = {k: v for k, v in scans.items() if v.get("complete")}
    incomplete = [k for k, v in scans.items() if not v.get("complete")]
    hist_set = {}
    for bname, sc in scans.items():
        for r in sc.get("refs", []):
            key = r["category"] + "|" + r["reference"].split(":", 1)[-1]
            hist_set.setdefault(key, []).append(bname)
    cur_refs = []
    main_scan = scans.get(BRANCH) or {}
    for r in main_scan.get("refs", []):
        cur_refs.append(r)
    cur_set = set(r["category"] + "|" + r["reference"].split(":", 1)[-1] for r in cur_refs)
    comp_keys = set()
    for bname, sc in complete.items():
        for r in sc.get("refs", []):
            comp_keys.add(r["category"] + "|" + r["reference"].split(":", 1)[-1])
    rows = []
    for key, brs in sorted(hist_set.items()):
        if key in cur_set:
            status = "PRESERVED"
        elif key in comp_keys:
            status = "REMOVED"
        else:
            status = "UNKNOWN"
        rows.append({"reference": key, "status": status, "branches": sorted(set(brs))})
    removed = [r for r in rows if r["status"] == "REMOVED"]
    candidates = [r for r in rows if r["status"] in ("REMOVED", "UNKNOWN")]
    cov = [{"branch": b, "files_in_tree": v.get("files_in_tree"), "files_scanned": v.get("files_scanned"),
            "files_skipped": v.get("files_skipped"), "tree_truncated": v.get("tree_truncated"),
            "complete": v.get("complete")} for b, v in scans.items()]
    meta = {"transport": "api_github_via_router_riu", "deviation_notes": DEV,
            "artifact_mapping": {
                "narrativo_guia_L51_57": ["commits.json->summary.json", "connections.jsonl->historical_connections.json",
                                          "deleted_files.json->deleted_files.json", "renamed_files.json->renamed_files.json",
                                          "historical_topology.json->historical_connections.json(per_branch)"],
                "narrativo_guia_L96_101": ["current_connections.json", "historical_connections.json",
                                           "comparison.json->summary.json", "recovery_candidates.json->removed_candidates.json"]},
            "completeness": {"branches_complete": sorted(complete), "branches_incomplete": incomplete,
                             "incomplete_branches_cannot_produce_REMOVED": True},
            "generated_at": datetime.now(timezone.utc).isoformat()}
    def dump(n, d):
        open(os.path.join(OUT, n), "w").write(json.dumps(d, indent=2, ensure_ascii=False))
    if prefix_wiring:
        dump("historical_connections.json", dict(meta, per_branch={k: v["refs"] for k, v in scans.items()}, coverage=cov))
        dump("current_connections.json", dict(meta, head=head, references=cur_refs))
        dump("removed_candidates.json", dict(meta, note="candidatos, no conexiones rotas confirmadas (guia L347)",
                                             removed_candidates=candidates))
        dump("comparison.json", dict(meta, rows=rows))
        dump("deleted_files.json", {"deleted": pack.get("deleted_files", [])})
        dump("renamed_files.json", {"renamed": pack.get("renamed_files", [])})
        dump("summary.json", dict(meta, repository=REPO, branch=BRANCH, head=head,
                                   commits_examined=pack.get("commits_examined"),
                                   commits_total_available=pack.get("commits_total_available"),
                                   historical_references=len(hist_set), current_references=len(cur_refs),
                                   removed_candidates=len(candidates), stats=pack.get("stats")))
        open(os.path.join(OUT, "file_history.txt"), "w").write("\n".join(pack.get("history", [])))
        reg = {"connections": [], "transport": "api_github_via_router_riu", "deviation_notes": DEV}
        for i, r in enumerate(rows, 1):
            cat, ref = r["reference"].split("|", 1)
            reg["connections"].append({
                "id": "CON-%03d" % i, "name": "%s_%s" % (cat, re.sub(r"[^a-z0-9]+", "_", ref.lower())[:40]),
                "source": "repo:" + REPO, "target": ref[:160], "protocol": cat.upper(),
                "direction": "unknown", "endpoint": ref[:160], "status": r["status"],
                "branches": r["branches"], "healthcheck": "required",
                "observations": "detectado por escaneo de contenido; requiere verificacion runtime (guia L14/L347)"})
        dump("registry.json", reg)
        open(os.path.join(OUT, "git_history.txt"), "w").write("\n".join(pack.get("history", [])))
        open(os.path.join(OUT, "branches.txt"), "w").write("\n".join("%s\t%s" % (b["name"], b["sha"]) for b in pack.get("branches", [])))
    if prefix_root:
        manifest = ""
        for rf in pack.get("root_files", []):
            if rf["name"] == "cableado.manifest.json":
                manifest = rf.get("content", "")
        entries = []
        for e in pack.get("root", []):
            name, low = e["name"], e["name"].lower()
            content = next((rf.get("content", "") for rf in pack.get("root_files", []) if rf["name"] == name), "")
            bin_ = "estructura" if e["type"] == "dir" else (
                "skill" if "skill" in low else
                "plan" if re.search(r"(plan|checkpoint|stated|bitacora|roadmap|guia|instruction|agents\.md)", low) else
                "cableado_despues" if ("cableado" in low or "wiring" in low or "manifest" in low or "loop" in low) else
                "no_cableado")
            if e["type"] == "file":
                entries.append({"name": name, "type": "file", "size": e.get("size"), "sha": e.get("sha"),
                                "bin": bin_, "referenced_in_manifest": name in manifest,
                                "content_excerpt": redact(content)[:400],
                                "proposed_location": "ROOT_KEEP" if name == "AGENTS.md" else (
                                    "docs/" if name.endswith(".md") else "backend/" if name.endswith(".py") else "config/"),
                                "action": "MANUAL_REVIEW", "automatic_move": False,
                                "deletion": "PROHIBIDA (guia L1091: no eliminar sin comprobar referencias)"})
            else:
                entries.append({"name": name, "type": "dir", "bin": "estructura", "automatic_move": False,
                                "action": "VERIFICAR_RESPONSABILIDAD (guia L893)"})
        dump("root_structure.json", dict(meta, root_entries=entries, root_listing_truncated=bool(pack.get("root_truncated"))))
    return {"out": OUT, "removed": len(removed), "rows": len(rows)}


def upload(prefixes):
    try:
        from huggingface_hub import upload_folder
        for pfx in prefixes:
            upload_folder(folder_path=os.environ.get("OUT_DIR", "/tmp/audit"),
                         repo_id=HF_REPORT_REPO, repo_type="dataset", path_in_repo=pfx)
            print("UPLOADED", pfx)
        return True
    except Exception as e:
        print("UPLOAD_SKIPPED:", e)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["acquire", "analyze"], required=True)
    ap.add_argument("--pack", default="/tmp/pack.json")
    ap.add_argument("--phase", choices=["wiring", "root"], default="wiring")
    a = ap.parse_args()
    if a.mode == "acquire":
        acquire()
        return
    pack = json.loads(open(a.pack, encoding="utf-8").read())
    analyze(pack, prefix_wiring=(a.phase == "wiring"), prefix_root=(a.phase == "root"))
    head = (pack.get("head") or "head")[:12]
    if a.phase == "wiring":
        upload(["wiring/%s" % head, "audits/%s" % head])
    else:
        upload(["root-audit/%s" % head])
    print("ANALYZE DONE phase=%s" % a.phase)


if __name__ == "__main__":
    main()
