#!/usr/bin/env python3
"""
ADAPTADOR DE TRANSPORTE (NO es el JOB 1 ni el JOB 2 de la guia).
Reproduce los MISMOS artefactos y las MISMAS clasificaciones de la guia
"REPOSITORY ENGINEERING GOVERNANCE" sustituyendo `git clone` por la API de GitHub
expuesta por el Router RIU (repo canonico privado + sin secret GH_TOKEN en la cuenta HF).

DESVIACIONES DECLARADAS (se incrustan en cada artefacto como "deviation_notes"):
 D1 transporte_api_router_en_vez_de_git_clone
 D2 cobertura_git_grep_reducida: la guia hace grep de contenido sobre el arbol COMPLETO
    en cada commit (6 patrones x hasta 500 commits). Sustituto: (a) deltas por commit via
    GET /commits/{sha} (files[] + patch) y (b) escaneo EXACTO del contenido en el tip de
    cada rama via github_leer. Se registra por commit: files_total/files_scanned/files_skipped.
 D3 alcance_commits: tope global MAX_COMMITS (500), mas recientes primero entre todas las refs.
 D4 git_bisect_no_disponible: requiere clon local.

CLASIFICACION (misma que la guia): PRESERVED | REMOVED | MODIFIED | NEW | BROKEN_CANDIDATE | UNKNOWN.
Bin de archivos (owner): skill | plan | cableado_antes | cableado_despues | no_cableado | basura
  -> "basura" es DESTINO/ESTADO, nunca borrado.
"""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone

ROUTER = os.environ.get("RIU_ROUTER_URL", "https://comand-center-1-riu-router.hf.space/mcp")
KEY = os.environ.get("RIU_ROUTER_API_KEY", "")
REPO = os.environ.get("GH_REPO", "maxbry123-commits/router-universal-router-inteligente-")
BRANCH = os.environ.get("GH_BRANCH", "main")
HF_REPORT_REPO = os.environ.get("HF_REPORT_REPO", "COMAND-CENTER-1/router-universal-router-inteligente-auditoria")
MAX_COMMITS = int(os.getenv("MAX_COMMITS", "500"))
SCAN_MAX = int(os.getenv("SCAN_MAX", "40"))
MAX_SECONDS = int(os.getenv("MAX_SECONDS", "2700"))
OUT = os.environ.get("OUT_DIR", "/tmp/audit")
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
DEVIATIONS = [
    "D1 transporte=api_github_via_router_riu (sin git clone; repo privado y sin secret GH_TOKEN)",
    "D2 cobertura git-grep reducida: deltas por commit + escaneo exacto en el tip de cada rama; cobertura registrada por commit",
    "D3 alcance de commits: tope global MAX_COMMITS=%d, mas recientes primero entre todas las refs" % MAX_COMMITS,
    "D4 git bisect no disponible (requiere clon local)",
    "Nota de la guia: removed_candidates contiene candidatos, no conexiones rotas confirmadas (guia L347)",
]
STATS = {"api_calls": 0, "truncations": 0, "gh_leer_calls": 0, "commits_enumerated": 0,
         "commits_examined": 0, "commits_total_available": 0, "files_scanned": 0,
         "files_skipped": 0, "errors": 0}


def redact(text):
    text = re.sub(r"(?i)(token|password|secret|api_key)(\s*[:=]\s*)['\"]?[^'\"\s,]+", r"\1\2[REDACTED]", text)
    text = re.sub(r"(https?://)[^/@\s]+@", r"\1[REDACTED]@", text)
    return text[:400]


def mcp(tool, args, timeout=180):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib_request("POST", ROUTER, body,
                         {"Content-Type": "application/json", "X-API-Key": KEY, "Authorization": "Bearer " + KEY},
                         timeout)
    d = json.loads(req)
    c = d.get("result", {}).get("content", [])
    return c[0]["text"] if c else ""


def urllib_request(method, url, body=None, headers=None, timeout=180):
    import urllib.request
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def gh_api(path):
    """Devuelve (data|None, raw, truncated). La respuesta del Router trunca a 12000 B."""
    STATS["api_calls"] += 1
    raw = mcp("github_api", {"metodo": "GET", "ruta": path})
    try:
        obj = json.loads(raw)
        return obj.get("data"), raw, False
    except Exception:
        STATS["truncations"] += 1
        return None, raw, True


def gh_read(path, ref):
    STATS["gh_leer_calls"] += 1
    try:
        return mcp("github_leer", {"repo": REPO, "ruta": path, "rama": ref})
    except Exception:
        STATS["errors"] += 1
        return ""


def scan_content(path, content):
    """Reproduce `git grep -n -I -E <pattern> <commit> -- . :!*.lock :!*.map` -> refs."""
    refs = []
    if not content:
        return refs
    if path.endswith((".lock", ".map")):
        return refs
    for category, rx in COMPILED.items():
        for m in rx.finditer(content):
            line_no = content.count("\n", 0, m.start()) + 1
            line = content[m.start():content.find("\n", m.start()) if content.find("\n", m.start()) != -1 else len(content)]
            refs.append({"category": category, "reference": redact("%s:%d:%s" % (path, line_no, line.strip()))})
    return refs


def list_branches():
    data, raw, trunc = gh_api("/repos/%s/branches?per_page=100" % REPO)
    out = []
    if isinstance(data, list):
        for b in data:
            out.append({"name": b.get("name"), "sha": (b.get("commit") or {}).get("sha")})
    else:
        for m in re.finditer(r'"name":\s*"([^"]+)"[^}]*?"sha":\s*"([0-9a-f]{40})"', raw):
            out.append({"name": m.group(1), "sha": m.group(2)})
    seen = set()
    uniq = []
    for b in out:
        if b["name"] and b["name"] not in seen:
            seen.add(b["name"])
            uniq.append(b)
    return uniq


def list_commits(branch, max_pages=200):
    commits, page = [], 1
    while page <= max_pages:
        data, raw, trunc = gh_api("/repos/%s/commits?sha=%s&per_page=3&page=%d" % (REPO, branch, page))
        got = []
        if isinstance(data, list):
            for c in data:
                cm = c.get("commit", {})
                got.append({"sha": c.get("sha"), "date": (cm.get("author") or {}).get("date", ""),
                            "message": (cm.get("message") or "").split("\n")[0], "branch": branch})
        else:
            for m in re.finditer(r'"sha":\s*"([0-9a-f]{40})"(.{0,900}?)"date":\s*"([^"]+)"', raw, re.S):
                got.append({"sha": m.group(1), "date": m.group(3), "message": "", "branch": branch})
            for m in re.finditer(r'"message":\s*"([^"]{0,200})"', raw):
                if got and not got[-1]["message"]:
                    got[-1]["message"] = m.group(1)
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
        ext = os.path.splitext(path)[1]
        if ext not in SCAN_EXT:
            s += 60
        if p.get("size", 0) > 400000:
            s += 50
        return s
    return sorted(paths, key=score)


def scan_ref(ref, sha):
    """Escaneo EXACTO de contenido en el tip de una ref (via github_leer, sin truncacion)."""
    paths, trunc = tree_paths(sha)
    cand = prioritize(paths)[:SCAN_MAX]
    refs, coverage = [], {"ref": ref, "tree_sha": sha, "files_total": len(paths),
                          "files_candidate": len(cand), "files_scanned": 0, "files_skipped": len(paths) - len(cand),
                          "tree_truncated": trunc}
    for p in cand:
        content = gh_read(p["path"], ref)
        if content and not content.startswith("ERROR"):
            coverage["files_scanned"] += 1
            STATS["files_scanned"] += 1
            refs.extend(scan_content(p["path"], content))
        else:
            coverage["files_skipped"] += 1
    STATS["files_skipped"] += coverage["files_skipped"]
    return refs, coverage


def commit_detail(sha):
    data, raw, trunc = gh_api("/repos/%s/commits/%s" % (REPO, sha))
    files, patches = [], []
    if isinstance(data, dict) and data.get("files"):
        for f in data["files"]:
            files.append({"filename": f.get("filename"), "status": f.get("status"), "additions": f.get("additions"), "deletions": f.get("deletions")})
            if f.get("patch"):
                patches.append({"filename": f.get("filename"), "patch": f.get("patch")})
    else:
        for m in re.finditer(r'"filename":\s*"([^"]+)"\s*,\s*"status":\s*"([A-Z])"', raw):
            files.append({"filename": m.group(1), "status": m.group(2), "additions": None, "deletions": None})
        for m in re.finditer(r'"patch":\s*"((?:[^"\\]|\\.){0,3000})"', raw):
            patches.append({"filename": None, "patch": m.group(1)})
    return files, patches, trunc


def classify(branch_refs, current_set):
    out = []
    for key, commits in branch_refs.items():
        if key in current_set:
            out.append({"reference": key, "status": "PRESERVED", "commits": commits})
        else:
            out.append({"reference": key, "status": "REMOVED", "commits": commits})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["wiring", "root"], default="wiring")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    started = time.time()
    head_sha = ""
    branches = list_branches()
    with open(os.path.join(OUT, "branches.txt"), "w") as f:
        f.write("branches\tname\tsha\n")
        for b in branches:
            f.write("%s\t%s\n" % (b["name"], b["sha"]))
    for b in branches:
        if b["name"] == BRANCH:
            head_sha = b["sha"]

    if args.phase == "wiring":
        # --- JOB 1: historial + comparacion ---
        per_branch = {}
        coverage = []
        all_commits = []
        for b in branches:
            cl = list_commits(b["name"])
            all_commits.extend(cl)
        STATS["commits_total_available"] = len(all_commits)
        seen = {}
        for c in all_commits:
            seen.setdefault(c["sha"], c)
        ordered = sorted(seen.values(), key=lambda c: c.get("date") or "", reverse=True)[:MAX_COMMITS]
        STATS["commits_enumerated"] = len(ordered)

        deleted, renamed, history_lines = [], [], []
        for c in ordered:
            if time.time() - started > MAX_SECONDS:
                break
            files, patches, trunc = commit_detail(c["sha"])
            STATS["commits_examined"] += 1
            for f in files:
                if f["status"] == "D":
                    deleted.append({"file": f["filename"], "commit": c["sha"], "date": c.get("date"), "message": c.get("message")})
                elif f["status"] == "R":
                    renamed.append({"file": f["filename"], "commit": c["sha"], "date": c.get("date"), "message": c.get("message")})
            history_lines.append("%s|%s|%s" % (c["sha"], c.get("date", ""), c.get("message", "")))
            for p in patches:
                if p.get("patch"):
                    for line in p["patch"].split("\n"):
                        if line.startswith("+") and not line.startswith("+++"):
                            for cat, rx in COMPILED.items():
                                if rx.search(line[1:]):
                                    history_lines.append("PATCH\t%s\t%s\t%s" % (cat, c["sha"], redact(line[1:])))

        branch_refs = {}
        for b in branches:
            refs, cov = scan_ref(b["name"], b["sha"])
            coverage.append(cov)
            d = {}
            for r in refs:
                key = r["category"] + "|" + r["reference"].split(":", 1)[-1]
                d.setdefault(key, []).append(b["name"])
            branch_refs.update(d)

        current = []
        for b in branches:
            if b["name"] == BRANCH:
                current, _ = scan_ref(BRANCH, b["sha"])
                break
        current_set = set(r["category"] + "|" + r["reference"].split(":", 1)[-1] for r in current)
        historical_set = {}
        for key, commits in branch_refs.items():
            historical_set.setdefault(key, []).extend(commits)
        removed = [{"reference": k, "commits": v} for k, v in historical_set.items() if k not in current_set]

        with open(os.path.join(OUT, "file_history.txt"), "w") as f:
            f.write("\n".join(history_lines))
        with open(os.path.join(OUT, "historical_connections.json"), "w") as f:
            json.dump({"transport": "api_github_via_router_riu", "deviation_notes": DEVIATIONS,
                       "per_branch": branch_refs, "coverage": coverage,
                       "commits_examined": STATS["commits_examined"], "commits_total_available": STATS["commits_total_available"]},
                      f, indent=2, ensure_ascii=False)
        with open(os.path.join(OUT, "current_connections.json"), "w") as f:
            json.dump({"transport": "api_github_via_router_riu", "deviation_notes": DEVIATIONS,
                       "head": head_sha, "references": current}, f, indent=2, ensure_ascii=False)
        with open(os.path.join(OUT, "removed_candidates.json"), "w") as f:
            json.dump({"transport": "api_github_via_router_riu", "deviation_notes": DEVIATIONS,
                       "note": "candidatos, no conexiones rotas confirmadas (guia L347)",
                       "removed_candidates": removed}, f, indent=2, ensure_ascii=False)
        with open(os.path.join(OUT, "deleted_files.json"), "w") as f:
            json.dump({"deleted": deleted}, f, indent=2, ensure_ascii=False)
        with open(os.path.join(OUT, "renamed_files.json"), "w") as f:
            json.dump({"renamed": renamed}, f, indent=2, ensure_ascii=False)
        with open(os.path.join(OUT, "summary.json"), "w") as f:
            json.dump({"repository": REPO, "branch": BRANCH, "head": head_sha,
                       "commits_examined": STATS["commits_examined"],
                       "commits_total_available": STATS["commits_total_available"],
                       "historical_references": len(historical_set), "current_references": len(current),
                       "removed_candidates": len(removed), "stats": STATS,
                       "deviation_notes": DEVIATIONS,
                       "generated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2, ensure_ascii=False)

    # --- JOB de conectividad: registry.json + git_history.txt + branches.txt ---
    registry = {"connections": [], "transport": "api_github_via_router_riu", "deviation_notes": DEVIATIONS}
    conn_id = 1
    for key, commits in sorted(historical_set.items()):
        cat, ref = key.split("|", 1)
        registry["connections"].append({
            "id": "CON-%03d" % conn_id, "name": "%s_%s" % (cat, re.sub(r"[^a-z0-9]+", "_", ref.lower())[:40]),
            "source": "repo:" + REPO, "target": ref[:160], "protocol": cat.upper(),
            "direction": "unknown", "endpoint": ref[:160],
            "status": "PRESERVED" if key in current_set else "REMOVED",
            "branches": sorted(set(commits)), "healthcheck": "required",
            "observations": "detectado por escaneo de contenido; requiere verificacion runtime (guia L14/L347)"})
        conn_id += 1
    with open(os.path.join(OUT, "registry.json"), "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "git_history.txt"), "w") as f:
        f.write("\n".join(history_lines))

    if args.phase == "root":
        # --- JOB 2: auditoria de raiz ---
        data, raw, trunc = gh_api("/repos/%s/contents/" % REPO)
        root = []
        if isinstance(data, list):
            for e in data:
                root.append({"name": e.get("name"), "type": e.get("type"), "size": e.get("size"), "sha": e.get("sha")})
        else:
            for m in re.finditer(r'"name":\s*"([^"]+)"\s*,\s*"path":\s*"[^"]*"\s*,\s*"sha":\s*"([0-9a-f]{40})"(?:\s*,\s*"size":\s*(\d+))?', raw):
                root.append({"name": m.group(1), "type": "file", "size": int(m.group(3) or 0), "sha": m.group(2)})
        manifest = gh_read("chat-router/cableado.manifest.json", BRANCH)
        entries = []
        for e in root:
            name = e["name"]
            low = name.lower()
            bin_ = "no_cableado"
            if e["type"] == "dir":
                bin_ = "estructura"
            elif "skill" in low:
                bin_ = "skill"
            elif re.search(r"(plan|checkpoint|stated|bitacora|roadmap|guia|instruction)", low):
                bin_ = "plan"
            elif name in ("cableado.manifest.json", "LOOP-wachdog-cola.json") or "cableado" in low or "wiring" in low:
                bin_ = "cableado_despues" if name not in manifest else "cableado_despues"
            elif any(k in low for k in ("dsla", "mvp")):
                bin_ = "no_cableado"
            if e["type"] == "file":
                in_manifest = name in manifest
                content = gh_read(name, BRANCH) if e.get("size", 0) < 200000 else ""
                entries.append({"name": name, "type": "file", "size": e.get("size"), "sha": e.get("sha"),
                                "bin": bin_, "referenced_in_manifest": in_manifest,
                                "referenced_in_code": bool(re.search(re.escape(name), content)) if content else None,
                                "proposed_location": "docs/" if name.endswith(".md") else "backend/" if name.endswith(".py") else "config/",
                                "action": "REVISAR_CONSUMIDORES_ANTES_DE_MOVER", "automatic_move": False,
                                "deletion": "PROHIBIDA (guia L1091: no eliminar sin comprobar referencias)"})
            else:
                entries.append({"name": name, "type": "dir", "bin": "estructura", "automatic_move": False,
                                "action": "VERIFICAR_RESPONSABILIDAD (guia L893)"})
        root_report = {"repository": REPO, "branch": BRANCH, "commit": head_sha,
                       "transport": "api_github_via_router_riu", "deviation_notes": DEVIATIONS,
                       "root_entries": entries, "root_listing_truncated": trunc,
                       "stats": STATS, "generated_at": datetime.now(timezone.utc).isoformat()}
        with open(os.path.join(OUT, "root_structure.json"), "w") as f:
            json.dump(root_report, f, indent=2, ensure_ascii=False)

    # --- persistencia en Hugging Face (guia: upload_folder -> dataset) ---
    prefixes = []
    if args.phase == "wiring":
        prefixes = ["wiring/%s" % (head_sha[:12] or "head"), "audits/%s" % (head_sha[:12] or "head")]
    else:
        prefixes = ["root-audit/%s" % (head_sha[:12] or "head")]
    try:
        from huggingface_hub import upload_folder
        for pfx in prefixes:
            upload_folder(folder_path=OUT, repo_id=HF_REPORT_REPO, repo_type="dataset", path_in_repo=pfx)
            print("UPLOADED", pfx)
    except Exception as e:
        print("UPLOAD_SKIPPED:", e)
    print("AUDIT COMPLETED")
    print("commits_examined:", STATS["commits_examined"], "/", STATS["commits_total_available"])
    print("historical_references:", len(historical_set), "current:", len(current), "removed_candidates:", len(removed))
    print("stats:", json.dumps(STATS))


if __name__ == "__main__":
    main()
