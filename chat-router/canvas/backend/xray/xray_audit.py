#!/usr/bin/env python3
"""X-RAY AUDITOR — fases 0-9 deterministas, reanudables y fail-closed.

Uso:
    python3 xray_audit.py --root <repo> --out <dir>

Salidas (en --out):
    STATE.json · MANIFEST.md · ARCHITECTURE.md · WIRING.json · INVENTORY.json ·
    CONTRACTS.md · GAPS.md · NEXT_ACTIONS.md · XRAY_REPORT.md · FINGERPRINT.json ·
    raw/{tree,symbols,imports,contracts,claims,comparison,gaps,actions,closure,validation}.json

Reglas duras implementadas:
  * PASS solo lo emite el validador (fase 9), nunca el analisis.
  * Todo nodo apunta a ruta:línea del codigo; si no hay ruta -> SIN_EVIDENCIA.
  * Sin porcentajes estimados: si no hay evidencia -> UNKNOWN.
  * Nunca escribe fuera de --out.
  * Cero secretos: se comprueba antes de emitir PASS.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constantes de esquema
# --------------------------------------------------------------------------- #

SCHEMA_STATE = "xray-state/1"
SCHEMA_INVENTORY = "xray-inventory/1"
SCHEMA_WIRING = "xray-wiring/1"
SCHEMA_FINGERPRINT = "xray-fingerprint/1"

PHASE_NAMES = {
    0: "preflight",
    1: "inventario determinista",
    2: "simbolos",
    3: "cableado (imports)",
    4: "contratos (endpoints/env vars)",
    5: "cruce docs vs code",
    6: "huecos",
    7: "acciones",
    8: "compresion",
    9: "fingerprint + validacion",
}

TASK_STATES = (
    "PENDING", "RESEARCHING", "EXECUTING", "VALIDATING", "GAP",
    "FIXING", "RETESTING", "STABLE", "BLOCKED", "CLOSED",
)
GAP_TYPES = ("GAP", "ERROR", "DRIFT", "BROKEN_CANDIDATE", "HUÉRFANO")
SEVERITIES = ("P0", "P1", "P2", "P3")
GAP_STATES = ("OPEN", "IN_PROGRESS", "FIXED", "WONTFIX")
COMPARE_STATES = ("PRESERVED", "REMOVED", "MODIFIED", "NEW", "BROKEN_CANDIDATE", "UNKNOWN")
VERDICTS = ("CONFIRMADO", "CONTRADICHO", "SIN_EVIDENCIA")

# Deteccion de secretos: prefijo + >=12 caracteres de token.
# Regla estricta a proposito: el patron literal del owner ("gh_|hf_|sk-")
# produce falsos positivos en prosa ("task-" contiene "sk-", "|hf_" es un patron
# alterno, no un token). El criterio de bloqueo es "prefijo + cuerpo de token".
SECRET_RE = re.compile(r"(?:gh[pousr]_|github_pat_|hf_|sk-)[A-Za-z0-9_\-]{12,}")
SECRET_PREFIXES = ("gh_", "hf_", "sk-")

LANG_BY_EXT = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".md": "Markdown", ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML",
    ".sh": "Shell", ".bash": "Shell", ".html": "HTML", ".htm": "HTML", ".css": "CSS",
    ".scss": "CSS", ".txt": "Text", ".cfg": "Config", ".ini": "Config", ".rs": "Rust",
    ".go": "Go", ".java": "Java", ".c": "C", ".h": "C", ".cpp": "C++", ".xml": "XML",
    ".sql": "SQL", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    ".vue": "Vue", ".svelte": "Svelte", ".bat": "Batch", ".ps1": "PowerShell",
}
CODE_LANGS = ("Python", "JavaScript", "TypeScript")
DOC_LANG = "Markdown"
CONSTITUTION_GLOBS = ("*FUENTE_DE_LA_VERDAD*.md", "CONSTITUCION*.md", "*CONSTITUTION*.md")

# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


class AuditError(RuntimeError):
    """Error fail-closed: el auditor no puede continuar sin evidencia."""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()


def git(root: Path, *args: str):
    """Ejecuta git en modo solo lectura. Devuelve (code, stdout, stderr)."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, env=env, timeout=180,
        )
    except FileNotFoundError:
        return 127, "", "git no disponible en el sandbox"
    except subprocess.TimeoutExpired:
        return 124, "", "git timeout: %s" % " ".join(args)
    return proc.returncode, proc.stdout, proc.stderr


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Escritura atomica: temporal en el mismo directorio + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".xray-tmp-", suffix=path.name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def write_json(path: Path, obj) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def count_lines(data: bytes) -> int:
    if not data:
        return 0
    n = data.count(b"\n")
    if not data.endswith(b"\n"):
        n += 1
    return n


def language_of(path: str, data: bytes) -> str:
    ext = Path(path).suffix.lower()
    if ext in LANG_BY_EXT:
        return LANG_BY_EXT[ext]
    if b"\x00" in data[:8192]:
        return "Binary"
    if not ext:
        return "Other"
    return "Other"


def derive_repo(remote: str, root: Path) -> str:
    if remote:
        cleaned = re.sub(r"\.git$", "", remote.strip())
        if cleaned.startswith("git@"):
            cleaned = cleaned.split(":", 1)[-1]
        if cleaned:
            return cleaned
    return root.name


def md_escape(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def evidence_str(path: str, line, sha: str = "") -> str:
    """ruta:línea (+ sha256). Si no hay ruta -> SIN_EVIDENCIA."""
    if not path:
        return "SIN_EVIDENCIA"
    base = "%s:%s" % (path, line if line else 1)
    return "%s sha256:%s" % (base, sha) if sha else base


# --------------------------------------------------------------------------- #
# Reglas de parsing
# --------------------------------------------------------------------------- #

KEYWORD_RE = re.compile(r"\b(m[oó]dulo|module|flujo|flow|componente|component)\b", re.IGNORECASE)
PATH_TOKEN_RE = re.compile(
    r"[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(?:py|js|jsx|mjs|cjs|ts|tsx|md|json|yml|yaml|toml|sh|html|css|txt|cfg|ini|sql|rs|go|java)\b"
)
BACKTICK_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_\.]*)`")
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")

PY_FROM_RE = re.compile(r"^\s*from\s+([.\w]+)\s+import\s+(.+?)\s*$")
PY_IMPORT_RE = re.compile(r"^\s*import\s+([.\w]+(?:\s*,\s*[.\w]+)*)")
JS_IMPORT_RE = re.compile(r"""^\s*(?:import|export)\s[^'"]*from\s+['"]([^'"]+)['"]""")
JS_BARE_RE = re.compile(r"""^\s*import\s+['"]([^'"]+)['"]""")
JS_REQUIRE_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")

ENDPOINT_DECOR_RE = re.compile(
    r"@\s*(?:app|router|api|blueprint|bp|server)\s*\.\s*(get|post|put|delete|patch|head|options)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
FLASK_ROUTE_RE = re.compile(r"@\s*\w+\s*\.\s*route\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
EXPRESS_RE = re.compile(
    r"\b(?:app|router|server)\s*\.\s*(get|post|put|delete|patch|options)\s*\(\s*['\"](/[^'\"]*)['\"]",
    re.IGNORECASE,
)
LINE_REF_RE = re.compile(r"[\w./\-]+\.[A-Za-z0-9_]+:\d+")
ENV_OS_RE = re.compile(r"os\s*\.\s*getenv\s*\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]")
ENV_ENVIRON_GET_RE = re.compile(r"os\s*\.\s*environ\s*\.\s*get\s*\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]")
ENV_ENVIRON_IDX_RE = re.compile(r"os\s*\.\s*environ\s*\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]")
ENV_PROCESS_RE = re.compile(r"process\s*\.\s*env\s*\.\s*([A-Z][A-Z0-9_]*)")
ENV_PY_GETENV_RE = re.compile(r"(?<![\w.])getenv\s*\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]")

SYM_PATTERNS = (
    ("def", re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("class", re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("constant", re.compile(r"^\s*([A-Z][A-Z0-9_]{2,})\s*=")),
    ("function", re.compile(r"^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("export function", re.compile(r"^\s*export\s+(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("const", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_])\s*=")),
    ("const", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\(")),
)

def looks_like_symbol(token: str) -> bool:
    """¿El token es un símbolo de código (y no una palabra en prosa)?

    El extractor de claims recoge cualquier palabra seguida de "(" (CALL_RE) y
    cualquier cosa entre acentos graves. Con una prosa normal eso produce
    falsos simbolos: "funcionando (", "auto (", "OMITIDO" ... y cada uno se
    convertia en un gap P3 SIN_EVIDENCIA que no se podia cerrar (ruido puro).

    Regla: un simbolo de codigo es snake_case, CamelCase, una CONSTANTE en
    mayusculas con guion bajo, o un nombre de fichero con extension.
    """
    if not token:
        return False
    if "." in token:
        return True                      # nombre de fichero o simbolo con punto
    if token.isupper():
        # CONSTANTE de codigo (WINDOW_ALLOWLIST) si, literal de estado
        # (OMITIDO, ERROR, PLAN) no: no es una afirmacion sobre el codigo.
        return "_" in token
    if "_" in token:
        return True                      # snake_case
    return any(ch.isupper() for ch in token[1:])   # CamelCase


PY_SUFFIXES = (".py",)
JS_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")


# --------------------------------------------------------------------------- #
# Auditor
# --------------------------------------------------------------------------- #


class Auditor:
    def __init__(self, root: str, out: str, gaps: str = None, resume: bool = True,
                 force: bool = False, exclude=None, max_rows: int = 200, quiet: bool = False):
        self.root = Path(root).expanduser().resolve()
        self.out = Path(out).expanduser().resolve()
        self.resume = resume and not force
        self.exclude_globs = list(exclude or [])
        self.max_rows = max_rows
        self.quiet = quiet
        self.script_dir = Path(__file__).resolve().parent

        self.out_rel = None
        try:
            self.out_rel = self.out.relative_to(self.root).as_posix()
        except ValueError:
            self.out_rel = None

        self.gaps_path = Path(gaps).expanduser().resolve() if gaps else None

        self.state = None
        self.branch = "UNKNOWN"
        self.commit_sha = "UNKNOWN"
        self.commit_date = "UNKNOWN"
        self.tree_sha = "UNKNOWN"
        self.repo = self.root.name
        self.remote = ""
        self.constitution_ref = "UNKNOWN"

        self.inventory = {}
        self.symbols = {}
        self.wiring = {}
        self.contracts = {}
        self.claims = []
        self.comparison = []
        self.gaps = []
        self.actions = []
        self.store_gaps = []

    # ---------------------------------------------------------------- util --
    def log(self, msg: str) -> None:
        if not self.quiet:
            print("[xray] %s" % msg, flush=True)

    def p(self, *parts: str) -> None:
        path = self.out.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def fail(self, msg: str) -> None:
        raise AuditError(msg)

    # --------------------------------------------------------------- state --
    def load_state(self) -> None:
        path = self.p("STATE.json")
        data = read_json(path)
        if isinstance(data, dict) and data.get("schema") == SCHEMA_STATE:
            self.state = data
            self.log("STATE.json cargado (reanudable) desde %s" % path)
        else:
            self.state = {
                "schema": SCHEMA_STATE,
                "root": str(self.root),
                "out": str(self.out),
                "created_at": utcnow(),
                "updated_at": utcnow(),
                "current_phase": -1,
                "phases": {},
            }

    def save_state(self) -> None:
        """Persistencia de cada cambio de fase (bug 3 del codigo de referencia)."""
        if self.state is None:
            return
        self.state["updated_at"] = utcnow()
        write_json(self.p("STATE.json"), self.state)

    def phase_state(self, idx: int) -> dict:
        return self.state.setdefault("phases", {}).setdefault(str(idx), {
            "name": PHASE_NAMES[idx], "status": "PENDING", "evidence": {},
        })

    def mark_phase(self, idx: int, status: str, evidence=None) -> None:
        st = self.phase_state(idx)
        st["name"] = PHASE_NAMES[idx]
        st["status"] = status
        st["evidence"] = evidence or {}
        st["updated_at"] = utcnow()
        self.state["current_phase"] = idx
        self.save_state()

    # Fases que SIEMPRE se re-ejecutan: dependen de estado externo mutable
    # (gaps.json de la VENTANA GAPS) o son las que validan el resultado final.
    ALWAYS_RUN = (6, 7, 8, 9)

    def phase_done(self, idx: int) -> bool:
        if idx in self.ALWAYS_RUN:
            return False
        st = self.state.get("phases", {}).get(str(idx), {})
        return bool(self.resume and st.get("status") == "COMPLETED")

    # ---------------------------------------------------------------- run ---
    def run(self) -> bool:
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "raw").mkdir(parents=True, exist_ok=True)
        self.load_state()
        self.log("root=%s out=%s" % (self.root, self.out))
        try:
            self.phase0()
            self.phase1()
            self.phase2()
            self.phase3()
            self.phase4()
            self.phase5()
            self.phase6()
            self.phase7()
            self.phase8()
            self.phase9()
        except AuditError as exc:
            self.fail_closed(exc)
            return False
        return True

    def fail_closed(self, exc: Exception) -> None:
        msg = "%s: %s" % (type(exc).__name__, exc)
        self.log("FALLO FAIL-CLOSED: %s" % msg)
        report = {
            "schema": "xray-validation/1",
            "PASS": False,
            "errors": [{"check": "runtime", "detail": msg}],
            "checks": [],
            "generated_at": utcnow(),
        }
        write_json(self.p("raw", "validation.json"), report)
        self.state["current_phase"] = self.state.get("current_phase", -1)
        self.state["error"] = msg
        self.save_state()

    # ------------------------------------------------------------- fase 0 ---
    def phase0(self) -> None:
        ev = {}
        if not self.root.is_dir():
            self.fail("root no existe: %s" % self.root)
        code, out, err = git(self.root, "rev-parse", "--show-toplevel")
        if code != 0:
            self.fail("root no es repositorio git (%s): %s" % (self.root, err.strip()[:160]))
        self.git_toplevel = Path(out.strip()).resolve()
        _, branch, _ = git(self.root, "rev-parse", "--abbrev-ref", "HEAD")
        self.branch = branch.strip() or "UNKNOWN"
        _, sha, _ = git(self.root, "rev-parse", "HEAD")
        self.commit_sha = sha.strip() or "UNKNOWN"
        _, cdate, _ = git(self.root, "log", "-1", "--format=%cI")
        self.commit_date = cdate.strip() or "UNKNOWN"
        _, tsha, _ = git(self.root, "rev-parse", "HEAD^{tree}")
        self.tree_sha = tsha.strip() or "UNKNOWN"
        _, remote, _ = git(self.root, "config", "--get", "remote.origin.url")
        self.remote = remote.strip()
        self.repo = derive_repo(self.remote, self.root)
        self.constitution_ref = self.find_constitution()
        ev.update({
            "root": str(self.root),
            "git_toplevel": str(self.git_toplevel),
            "repo": self.repo,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "commit_date": self.commit_date,
            "tree_sha": self.tree_sha,
            "remote": self.remote or "(sin remote)",
            "constitution_ref": self.constitution_ref,
            "python": sys.version.split()[0],
            "out": str(self.out),
        })
        self.mark_phase(0, "COMPLETED", ev)
        self.log("fase 0 preflight OK commit=%s" % self.commit_sha[:12])

    def find_constitution(self) -> str:
        for pattern in CONSTITUTION_GLOBS:
            for path in sorted(self.root.rglob(pattern)):
                if self.out_rel and path.is_relative_to(self.out):
                    continue
                return path.relative_to(self.root).as_posix()
        return "UNKNOWN"

    # ------------------------------------------------------------- fase 1 ---
    def phase1(self) -> None:
        if self.phase_done(1):
            data = read_json(self.p("INVENTORY.json"))
            if isinstance(data, dict) and data.get("files"):
                self.inventory = {f["path"]: f for f in data["files"]}
                self.mark_phase(1, "COMPLETED", data.get("coverage", {}))
                self.log("fase 1 inventario reanudado (%d ficheros)" % len(self.inventory))
                return
        code, out, err = git(self.root, "ls-files", "-z")
        if code != 0:
            self.fail("git ls-files fallo: %s" % err.strip()[:160])
        tracked = [p for p in out.split("\0") if p]
        files, excluded, missing = [], [], []
        for rel in tracked:
            if self.out_rel and (rel == self.out_rel or rel.startswith(self.out_rel + "/")):
                excluded.append(rel)
                continue
            if any(fnmatch.fnmatch(rel, g) for g in self.exclude_globs):
                excluded.append(rel)
                continue
            full = self.root / rel
            if not full.is_file():
                missing.append(rel)
                continue
            try:
                data = full.read_bytes()
            except OSError:
                missing.append(rel)
                continue
            files.append({
                "path": rel,
                "sha256": sha256_bytes(data),
                "bytes": len(data),
                "lines": count_lines(data),
                "language": language_of(rel, data),
            })
        files.sort(key=lambda f: f["path"])
        coverage = {
            "tracked_files": len(tracked),
            "inventoried": len(files),
            "excluded": sorted(excluded),
            "missing": sorted(missing),
            "coverage_complete": len(files) + len(excluded) == len(tracked),
        }
        payload = {
            "schema": SCHEMA_INVENTORY,
            "root": str(self.root),
            "commit_sha": self.commit_sha,
            "generated_at": utcnow(),
            "coverage": coverage,
            "files": files,
        }
        write_json(self.p("INVENTORY.json"), payload)
        self.inventory = {f["path"]: f for f in files}

        tree = {}
        for f in files:
            top = f["path"].split("/", 1)[0] if "/" in f["path"] else "(root)"
            node = tree.setdefault(top, {"files": 0, "bytes": 0, "languages": {}})
            node["files"] += 1
            node["bytes"] += f["bytes"]
            node["languages"][f["language"]] = node["languages"].get(f["language"], 0) + 1
        write_json(self.p("raw", "tree.json"), {
            "schema": "xray-tree/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "roots": tree,
        })
        ev = dict(coverage)
        ev["excluded"] = len(excluded)
        ev["missing"] = len(missing)
        self.mark_phase(1, "COMPLETED", ev)
        self.log("fase 1 inventario: %d ficheros, %d excluidos, %d ausentes"
                 % (len(files), len(excluded), len(missing)))

    # ------------------------------------------------------------- fase 2 ---
    def phase2(self) -> None:
        if self.phase_done(2):
            data = read_json(self.p("raw", "symbols.json"))
            if isinstance(data, dict) and data.get("symbols"):
                self.symbols = data["symbols"]
                self.mark_phase(2, "COMPLETED", {"files_with_symbols": len(self.symbols)})
                self.log("fase 2 simbolos reanudados")
                return
        symbols = {}
        for rel, meta in sorted(self.inventory.items()):
            if meta["language"] not in CODE_LANGS:
                continue
            try:
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            found = []
            for idx, line in enumerate(text.splitlines(), start=1):
                if len(line) > 4000:
                    continue
                for kind, rx in SYM_PATTERNS:
                    m = rx.match(line)
                    if m:
                        found.append({"name": m.group(1), "kind": kind, "line": idx})
            if found:
                symbols[rel] = found
        write_json(self.p("raw", "symbols.json"), {
            "schema": "xray-symbols/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "symbols": symbols,
        })
        self.symbols = symbols
        total = sum(len(v) for v in symbols.values())
        self.mark_phase(2, "COMPLETED", {"files_with_symbols": len(symbols), "symbols": total})
        self.log("fase 2 simbolos: %d en %d ficheros" % (total, len(symbols)))

    # ------------------------------------------------------------- fase 3 ---
    def phase3(self) -> None:
        if self.phase_done(3):
            data = read_json(self.p("WIRING.json"))
            if isinstance(data, dict) and data.get("imports"):
                self.wiring = data
                self.mark_phase(3, "COMPLETED", data.get("counts", {}))
                self.log("fase 3 cableado reanudado")
                return
        imports, edges = [], []
        for rel, meta in sorted(self.inventory.items()):
            lang = meta["language"]
            if lang not in CODE_LANGS:
                continue
            try:
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                rec = None
                if lang == "Python":
                    rec = self._parse_py_import(rel, line, idx)
                else:
                    rec = self._parse_js_import(rel, line, idx)
                if rec:
                    imports.append(rec)
                    if rec["target_path"]:
                        edges.append({
                            "from": rel, "to": rec["target_path"], "module": rec["module"],
                            "line": idx, "kind": rec["kind"],
                        })
        counts = {
            "imports_total": len(imports),
            "resolved": sum(1 for i in imports if i["status"] == "RESOLVED"),
            "broken_local": sum(1 for i in imports if i["status"] == "BROKEN_CANDIDATE"),
            "unverified_third_party": sum(1 for i in imports if i["status"] == "UNKNOWN"),
        }
        self.wiring = {
            "schema": SCHEMA_WIRING,
            "commit_sha": self.commit_sha,
            "generated_at": utcnow(),
            "counts": counts,
            "imports": imports,
            "edges": edges,
        }
        write_json(self.p("WIRING.json"), self.wiring)
        write_json(self.p("raw", "imports.json"), {
            "schema": "xray-imports/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "imports": imports, "edges": edges,
        })
        self.mark_phase(3, "COMPLETED", counts)
        self.log("fase 3 cableado: %d imports (%d resueltos, %d rotos, %d no verificables)"
                 % (counts["imports_total"], counts["resolved"],
                    counts["broken_local"], counts["unverified_third_party"]))

    def _parse_py_import(self, rel: str, line: str, idx: int):
        m = PY_FROM_RE.match(line)
        if m:
            module, names_raw = m.group(1), m.group(2)
            names = [n.strip().split(" as ")[0].strip() for n in names_raw.split(",") if n.strip()]
            return self._resolve_import(rel, idx, "python", module, names)
        m = PY_IMPORT_RE.match(line)
        if m:
            modules = [x.strip() for x in m.group(1).split(",") if x.strip()]
            return self._resolve_import(rel, idx, "python", modules[0], modules)
        return None

    def _parse_js_import(self, rel: str, line: str, idx: int):
        for rx in (JS_IMPORT_RE, JS_BARE_RE, JS_REQUIRE_RE):
            m = rx.search(line)
            if m:
                module = m.group(1)
                return self._resolve_import(rel, idx, "js", module, [])
        return None

    def _resolve_import(self, rel: str, idx: int, kind: str, module: str, names):
        sha = self.inventory.get(rel, {}).get("sha256", "")
        rec = {
            "from_path": rel, "from_sha256": sha, "line": idx, "kind": kind,
            "module": module, "names": names, "target_path": None,
            "resolved": False, "status": "UNKNOWN", "reason": "",
        }
        if not module:
            rec["status"] = "UNKNOWN"
            rec["reason"] = "modulo vacio"
            return rec
        if kind == "python":
            if module.startswith("."):
                base = (self.root / rel).parent
                parts = module.lstrip(".").split(".")
                rel_mod = module.count(".") - 1
                up = base
                for _ in range(rel_mod):
                    up = up.parent
                cand_dir = up.joinpath(*parts) if parts else up
                for cand in (cand_dir.with_suffix(".py"), cand_dir / "__init__.py"):
                    if cand.is_file():
                        rec["target_path"] = cand.relative_to(self.root).as_posix()
                        rec["resolved"] = True
                        rec["status"] = "RESOLVED"
                        return rec
                rec["status"] = "BROKEN_CANDIDATE"
                rec["reason"] = "import relativo no resoluble en el repo"
                return rec
            parts = module.split(".")
            cand = self.root.joinpath(*parts).with_suffix(".py")
            cand2 = self.root.joinpath(*parts) / "__init__.py"
            for c in (cand, cand2):
                if c.is_file():
                    rec["target_path"] = c.relative_to(self.root).as_posix()
                    rec["resolved"] = True
                    rec["status"] = "RESOLVED"
                    return rec
            if self.root.joinpath(*parts).is_dir():
                rec["status"] = "UNKNOWN"
                rec["reason"] = "paquete local sin modulo indexado"
                return rec
            rec["status"] = "UNKNOWN"
            rec["reason"] = "modulo externo: no verificable offline"
            return rec
        # javascript / typescript
        if module.startswith("."):
            base = (self.root / rel).parent
            target = (base / module).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                rec["status"] = "BROKEN_CANDIDATE"
                rec["reason"] = "import relativo fuera del repo"
                return rec
            for suffix in JS_SUFFIXES + ("/index.js", "/index.ts"):
                cand = Path(str(target) + suffix)
                if cand.is_file():
                    rec["target_path"] = cand.relative_to(self.root).as_posix()
                    rec["resolved"] = True
                    rec["status"] = "RESOLVED"
                    return rec
            rec["status"] = "BROKEN_CANDIDATE"
            rec["reason"] = "import relativo no resoluble en el repo"
            return rec
        rec["status"] = "UNKNOWN"
        rec["reason"] = "modulo externo: no verificable offline"
        return rec

    # ------------------------------------------------------------- fase 4 ---
    def phase4(self) -> None:
        if self.phase_done(4):
            data = read_json(self.p("raw", "contracts.json"))
            if isinstance(data, dict) and "endpoints" in data:
                self.contracts = data
                self.mark_phase(4, "COMPLETED", {"endpoints": len(data["endpoints"]),
                                                "env_vars": len(data["env_vars"])})
                self.log("fase 4 contratos reanudados")
                return
        endpoints, env_vars = [], []
        seen_ep, seen_env = set(), set()
        for rel, meta in sorted(self.inventory.items()):
            lang = meta["language"]
            if lang not in CODE_LANGS:
                continue
            try:
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            sha = meta["sha256"]
            for idx, line in enumerate(text.splitlines(), start=1):
                for rx in (ENDPOINT_DECOR_RE, EXPRESS_RE):
                    for m in rx.finditer(line):
                        if rx is ENDPOINT_DECOR_RE:
                            method, path = m.group(1).upper(), m.group(2)
                        else:
                            method, path = m.group(1).upper(), m.group(2)
                        key = (rel, method, path)
                        if key in seen_ep:
                            continue
                        seen_ep.add(key)
                        endpoints.append({
                            "method": method, "path": path, "file": rel, "line": idx,
                            "sha256": sha, "evidence": evidence_str(rel, idx, sha),
                        })
                for m in FLASK_ROUTE_RE.finditer(line):
                    path = m.group(1)
                    key = (rel, "ROUTE", path)
                    if key in seen_ep:
                        continue
                    seen_ep.add(key)
                    endpoints.append({
                        "method": "ROUTE", "path": path, "file": rel, "line": idx,
                        "sha256": sha, "evidence": evidence_str(rel, idx, sha),
                    })
                for rx in (ENV_OS_RE, ENV_ENVIRON_GET_RE, ENV_ENVIRON_IDX_RE,
                           ENV_PROCESS_RE, ENV_PY_GETENV_RE):
                    for m in rx.finditer(line):
                        name = m.group(1)
                        key = (rel, name)
                        if key in seen_env:
                            continue
                        seen_env.add(key)
                        env_vars.append({
                            "name": name, "file": rel, "line": idx, "sha256": sha,
                            "evidence": evidence_str(rel, idx, sha),
                        })
        self.contracts = {
            "schema": "xray-contracts/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "endpoints": endpoints, "env_vars": env_vars,
        }
        write_json(self.p("raw", "contracts.json"), self.contracts)
        self.p("CONTRACTS.md").write_text(self.render_contracts(), encoding="utf-8")
        self.mark_phase(4, "COMPLETED", {"endpoints": len(endpoints), "env_vars": len(env_vars)})
        self.log("fase 4 contratos: %d endpoints, %d env vars" % (len(endpoints), len(env_vars)))

    def render_contracts(self) -> str:
        lines = [
            "# CONTRACTS — endpoints y variables de entorno",
            "",
            "- commit: `%s`" % self.commit_sha,
            "- branch: `%s`" % self.branch,
            "- generado: %s" % utcnow(),
            "- evidencia: cada fila apunta a `ruta:línea` + `sha256` del fichero.",
            "",
            "## ENDPOINTS (%d)" % len(self.contracts.get("endpoints", [])),
            "",
        ]
        eps = self.contracts.get("endpoints", [])
        if eps:
            lines += ["| método | ruta | evidencia | sha256 |", "|---|---|---|---|"]
            for e in eps:
                lines.append("| %s | `%s` | %s:%s | `%s` |" % (
                    e["method"], md_escape(e["path"]), e["file"], e["line"], e["sha256"]))
        else:
            lines.append("Sin endpoints detectados en el codigo: no hay evidencia de contrato HTTP "
                         "(UNKNOWN por ausencia de evidencia, no estimacion).")
        lines += ["", "## ENV VARS (%d)" % len(self.contracts.get("env_vars", [])), ""]
        envs = self.contracts.get("env_vars", [])
        if envs:
            lines += ["| variable | evidencia | sha256 |", "|---|---|---|"]
            for e in envs:
                lines.append("| `%s` | %s:%s | `%s` |" % (
                    e["name"], e["file"], e["line"], e["sha256"]))
        else:
            lines.append("Sin variables de entorno detectadas en el codigo: no hay evidencia "
                         "(UNKNOWN por ausencia de evidencia, no estimacion).")
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------- fase 5 ---
    def phase5(self) -> None:
        if self.phase_done(5):
            claims = read_json(self.p("raw", "claims.json"))
            comp = read_json(self.p("raw", "comparison.json"))
            if isinstance(claims, dict) and isinstance(comp, dict):
                self.claims = claims.get("claims", [])
                self.comparison = comp.get("rows", [])
                self.mark_phase(5, "COMPLETED", {"claims": len(self.claims),
                                                "rows": len(self.comparison)})
                self.log("fase 5 cruce reanudado")
                return
        claims = []
        for rel, meta in sorted(self.inventory.items()):
            if meta["language"] != DOC_LANG:
                continue
            try:
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                if not KEYWORD_RE.search(line):
                    continue
                paths = sorted({m.group(0).strip(".,;:()[]{}") for m in PATH_TOKEN_RE.finditer(line)})
                symbols = sorted({m.group(1) for m in BACKTICK_RE.finditer(line)})
                symbols += sorted({m.group(1) for m in CALL_RE.finditer(line)})
                symbols = sorted({s for s in set(symbols) if looks_like_symbol(s)})
                # FIX 3: una linea de prosa que contiene la palabra clave pero
                # NO declara ninguna ruta ni ningun simbolo no es una claim:
                # no hay nada que verificar. Antes cada frase con la palabra
                # "modulo" generaba un gap P3 SIN_EVIDENCIA (ruido puro).
                if not paths and not symbols:
                    continue
                claims.append({
                    "id": "CLM-%04d" % (len(claims) + 1),
                    "doc": rel, "line": idx, "sha256": meta["sha256"],
                    "text": line.strip()[:400],
                    "paths": paths, "symbols": symbols,
                })
        write_json(self.p("raw", "claims.json"), {
            "schema": "xray-claims/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "claims": claims,
        })
        self.claims = claims
        rows = self.build_comparison(claims)
        write_json(self.p("raw", "comparison.json"), {
            "schema": "xray-comparison/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "states": list(COMPARE_STATES), "rows": rows,
        })
        self.comparison = rows
        counts = {}
        for r in rows:
            counts[r["estado"]] = counts.get(r["estado"], 0) + 1
        self.mark_phase(5, "COMPLETED", {"claims": len(claims), "rows": len(rows),
                                        "by_state": counts})
        self.log("fase 5 cruce: %d claims, %d filas de comparacion %s"
                 % (len(claims), len(rows), counts))

    def resolve_path_claim(self, candidate: str):
        """Resuelve una ruta mencionada en docs contra INVENTORY. Devuelve (path, line) o (None, None)."""
        if not candidate:
            return None, None
        cand = candidate.replace("\\", "/").lstrip("./")
        if not cand:
            return None, None
        if cand in self.inventory:
            return cand, 1
        suffix = "/" + cand
        hits = [p for p in self.inventory if p.endswith(suffix)]
        if len(hits) == 1:
            return hits[0], 1
        if len(hits) > 1:
            hits.sort()
            return hits[0], 1
        base = cand.rsplit("/", 1)[-1]
        hits = [p for p in self.inventory if p.rsplit("/", 1)[-1] == base]
        if len(hits) == 1:
            return hits[0], 1
        if len(hits) > 1:
            hits.sort()
            return hits[0], 1
        return None, None

    def find_symbol(self, path: str, names):
        """Busca un simbolo declarado en un fichero concreto. Devuelve (nombre, linea) o (None, None)."""
        if not path or not names:
            return None, None
        syms = self.symbols.get(path, [])
        for name in names:
            base = name.split(".")[-1]
            for s in syms:
                if s["name"] == name or s["name"] == base:
                    return s["name"], s["line"]
        return None, None

    def find_symbol_anywhere(self, names):
        if not names:
            return None, None, None
        for path in sorted(self.symbols):
            syms = self.symbols[path]
            for name in names:
                base = name.split(".")[-1]
                for s in syms:
                    if s["name"] == name or s["name"] == base:
                        return path, s["name"], s["line"]
        return None, None, None

    def build_comparison(self, claims):
        """COMPARADOR: PRESERVED | REMOVED | MODIFIED | NEW | BROKEN_CANDIDATE | UNKNOWN."""
        rows = []
        documented = set()
        for claim in claims:
            for cand in claim["paths"]:
                path, _ = self.resolve_path_claim(cand)
                if path:
                    documented.add(path)
                    break
        for claim in claims:
            resolved = None
            declared_path = None
            for cand in claim["paths"]:
                path, _ = self.resolve_path_claim(cand)
                if path:
                    resolved = path
                    break
                if declared_path is None:
                    declared_path = cand
            sym_name, sym_line = self.find_symbol(resolved, claim["symbols"])
            if resolved is None:
                other_path, other_name, other_line = self.find_symbol_anywhere(claim["symbols"])
                if other_path:
                    estado = "PRESERVED"
                    ev = evidence_str(other_path, other_line, self.inventory.get(other_path, {}).get("sha256", ""))
                    code_path, code_line = other_path, other_line
                elif declared_path:
                    # declarado en la doc, ausente en el codigo -> REMOVED
                    estado = "REMOVED"
                    ev = evidence_str(claim["doc"], claim["line"], claim["sha256"])
                    code_path, code_line = None, None
                else:
                    estado = "UNKNOWN"
                    ev = "SIN_EVIDENCIA"
                    code_path, code_line = None, None
            else:
                code_path, code_line = resolved, (sym_line or 1)
                sha = self.inventory.get(resolved, {}).get("sha256", "")
                if claim["symbols"] and sym_name is None:
                    # FIX 1: si el simbolo declarado ES el propio fichero
                    # (p.ej. el doc cita `api.py` y el fichero es backend/api.py),
                    # la claim esta verificada por la existencia de la ruta.
                    base_names = {Path(resolved).name, Path(resolved).stem}
                    declared = {str(s) for s in claim["symbols"]}
                    # FIX 2: los ficheros que no son codigo (md, json, txt...)
                    # no tienen simbolos que verificar: la existencia de la
                    # ruta ES la verificacion (una tabla de deps no declara
                    # funciones: declarar MODIFIED aqui es un falso positivo).
                    language = self.inventory.get(resolved, {}).get("language")
                    if (declared & base_names) or (language not in CODE_LANGS):
                        estado = "PRESERVED"
                    else:
                        estado = "MODIFIED"
                else:
                    estado = "PRESERVED"
                ev = evidence_str(resolved, sym_line or 1, sha)
            rows.append({
                "kind": "DOC_CLAIM",
                "id": claim["id"],
                "estado": estado,
                "doc_path": claim["doc"], "doc_line": claim["line"],
                "code_path": code_path, "code_line": code_line,
                "simbolo": sym_name,
                "evidencia": ev,
                "detalle": claim["text"],
            })
        # Codigo huerfano (NEW) y imports rotos (BROKEN_CANDIDATE)
        for path in sorted(self.inventory):
            if self.inventory[path]["language"] not in CODE_LANGS:
                continue
            if path in documented:
                continue
            rows.append({
                "kind": "CODE_FILE",
                "id": "ORF-%s" % hashlib.sha256(path.encode()).hexdigest()[:8],
                "estado": "NEW",
                "doc_path": None, "doc_line": None,
                "code_path": path, "code_line": 1,
                "simbolo": None,
                "evidencia": evidence_str(path, 1, self.inventory[path]["sha256"]),
                "detalle": "fichero de codigo sin mencion en ningun documento del repo (HUÉRFANO)",
            })
        for imp in self.wiring.get("imports", []):
            if imp["status"] != "BROKEN_CANDIDATE":
                continue
            rows.append({
                "kind": "BROKEN_IMPORT",
                "id": "BRK-%s-%d" % (hashlib.sha256(imp["from_path"].encode()).hexdigest()[:6], imp["line"]),
                "estado": "BROKEN_CANDIDATE",
                "doc_path": None, "doc_line": None,
                "code_path": imp["from_path"], "code_line": imp["line"],
                "simbolo": imp["module"],
                "evidencia": evidence_str(imp["from_path"], imp["line"], imp["from_sha256"]),
                "detalle": imp["reason"] or "import no resoluble",
            })
        # Recorte determinista por estado (evidencia completa en raw/comparison.json)
        capped, counts = [], {}
        for row in rows:
            estado = row["estado"]
            counts[estado] = counts.get(estado, 0) + 1
            if counts[estado] <= self.max_rows:
                capped.append(row)
        self._comparison_total = counts
        return capped

    # ------------------------------------------------------------- fase 6 ---
    def phase6(self) -> None:
        if self.phase_done(6):
            data = read_json(self.p("raw", "gaps.json"))
            if isinstance(data, dict) and "gaps" in data:
                self.gaps = data["gaps"]
                self.mark_phase(6, "COMPLETED", {"gaps": len(self.gaps)})
                self.log("fase 6 huecos reanudados")
                return
        gaps = []
        verifications = []
        # 1) Claims: veredicto real (bug 1 del codigo de referencia).
        #    CONFIRMADO  = el simbolo/ruta declarado existe con su linea.
        #    CONTRADICHO = la ruta existe pero el simbolo declarado no.
        #    SIN_EVIDENCIA = no hay ruta/simbolo verificable.
        estado_to_verdict = {
            "PRESERVED": "CONFIRMADO",
            "MODIFIED": "CONTRADICHO",
            "REMOVED": "CONTRADICHO",
            "UNKNOWN": "SIN_EVIDENCIA",
        }
        claim_rows = {r["id"]: r for r in self.comparison if r["kind"] == "DOC_CLAIM"}
        for claim in self.claims:
            row = claim_rows.get(claim["id"], {})
            verdict = estado_to_verdict.get(row.get("estado", "UNKNOWN"), "SIN_EVIDENCIA")
            ev = row.get("evidencia", "SIN_EVIDENCIA")
            verifications.append({
                "id": claim["id"],
                "doc": claim["doc"], "doc_line": claim["line"],
                "estado": row.get("estado", "UNKNOWN"),
                "veredicto": verdict,
                "evidencia": ev,
                "notas": claim["text"][:500],
            })
        # 2) Filas del comparador que implican accion
        for row in self.comparison:
            if row["estado"] in ("PRESERVED",):
                continue
            tipo, sev, ver = {
                "REMOVED": ("DRIFT", "P1", "CONTRADICHO"),
                "MODIFIED": ("DRIFT", "P1", "CONTRADICHO"),
                "NEW": ("HUÉRFANO", "P2", "CONFIRMADO"),
                "BROKEN_CANDIDATE": ("BROKEN_CANDIDATE", "P0", "CONFIRMADO"),
                "UNKNOWN": ("GAP", "P3", "SIN_EVIDENCIA"),
            }[row["estado"]]
            gaps.append({
                "id": "AUD-%04d" % (len(gaps) + 1),
                "origen": "COMPARADOR",
                "tipo": tipo,
                "severidad": sev,
                "titulo": "%s: %s" % (row["estado"], row.get("detalle", "")[:120]),
                "componente": row.get("code_path") or row.get("doc_path") or "UNKNOWN",
                "estado": "OPEN",
                "veredicto": ver,
                "evidencia": row["evidencia"],
                "notas": str(row.get("detalle", ""))[:500],
                "creado": utcnow(),
                "resuelto": None,
                "doc": row.get("doc_path"), "doc_line": row.get("doc_line"),
            })
        # 3) Gaps capturados por la VENTANA GAPS (gaps.json) -> revalidados
        store = self.load_store_gaps()
        for gap in store:
            ev = gap.get("evidencia", "")
            ver = self.verdict_for_evidence(ev)
            gaps.append({
                "id": gap.get("id", "GAP-UNKNOWN"),
                "origen": "VENTANA_GAPS",
                "tipo": gap.get("tipo", "GAP"),
                "severidad": gap.get("severidad", "P3"),
                "titulo": gap.get("titulo", ""),
                "componente": gap.get("componente", "UNKNOWN"),
                "estado": gap.get("estado", "OPEN"),
                "veredicto": ver,
                "evidencia": ev,
                "notas": str(gap.get("notas", ""))[:500],
                "creado": gap.get("creado"),
                "resuelto": gap.get("resuelto"),
            })
        self.gaps = gaps
        self.verifications = verifications
        write_json(self.p("raw", "gaps.json"), {
            "schema": "xray-gaps/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "gaps": gaps, "verifications": verifications,
        })
        self.p("GAPS.md").write_text(self.render_gaps(), encoding="utf-8")
        by_verdict = {}
        for g in gaps:
            by_verdict[g["veredicto"]] = by_verdict.get(g["veredicto"], 0) + 1
        self.mark_phase(6, "COMPLETED", {"gaps": len(gaps), "by_verdict": by_verdict,
                                        "store_gaps": len(store)})
        self.log("fase 6 huecos: %d gaps %s" % (len(gaps), by_verdict))

    def verdict_for_row(self, row) -> str:
        ev = row.get("evidencia", "")
        if ev == "SIN_EVIDENCIA":
            return "SIN_EVIDENCIA"
        return self.verdict_for_evidence(ev)

    def verdict_for_evidence(self, ev: str) -> str:
        """Re-validacion de evidencia contra INVENTORY (ruta:línea + sha256)."""
        if not ev:
            return "SIN_EVIDENCIA"
        m = re.match(r"^(?P<path>[^:\s]+):(?P<line>\d+)", ev.strip())
        if not m:
            return "SIN_EVIDENCIA"
        path, line = m.group("path"), int(m.group("line"))
        meta = self.inventory.get(path)
        if not meta:
            return "SIN_EVIDENCIA"
        if line < 1 or line > max(meta["lines"], 1):
            return "CONTRADICHO"
        sha_m = re.search(r"sha256:([0-9a-f]{64})", ev)
        if sha_m and sha_m.group(1) != meta["sha256"]:
            return "CONTRADICHO"
        return "CONFIRMADO"

    def load_store_gaps(self):
        candidates = []
        if self.gaps_path:
            candidates.append(self.gaps_path)
        else:
            candidates.append(self.out / "gaps.json")
            candidates.append(self.script_dir / "gaps.json")
        for path in candidates:
            data = read_json(path)
            if isinstance(data, dict) and isinstance(data.get("gaps"), list):
                return data["gaps"]
            if isinstance(data, list):
                return data
        return []

    def render_gaps(self) -> str:
        counts = {}
        for g in self.gaps:
            counts[g["veredicto"]] = counts.get(g["veredicto"], 0) + 1
        ver_counts = {}
        for v in getattr(self, "verifications", []):
            ver_counts[v["veredicto"]] = ver_counts.get(v["veredicto"], 0) + 1
        lines = [
            "# GAPS — auditoría X-Ray",
            "",
            "- commit: `%s`" % self.commit_sha,
            "- branch: `%s`" % self.branch,
            "- generado: %s" % utcnow(),
            "- origen: fases 0-9 (comparador determinista) + VENTANA GAPS (`gaps.json`)",
            "- veredictos admitidos: %s" % " | ".join(VERDICTS),
            "",
            "## RESUMEN POR VEREDICTO (conteo evidenced, sin porcentaje estimado)",
            "",
            "| veredicto | gaps | verificaciones |", "|---|---|---|",
        ]
        for v in VERDICTS:
            lines.append("| %s | %d | %d |" % (v, counts.get(v, 0), ver_counts.get(v, 0)))
        lines += ["", "## VERIFICACIONES DOCS vs CODE (cada fila con veredicto)", "",
                  "| id | doc | estado comparador | veredicto | evidencia | notas |",
                  "|---|---|---|---|---|---|"]
        for v in getattr(self, "verifications", []):
            lines.append("| %s | %s:%s | %s | %s | `%s` | %s |" % (
                v["id"], v["doc"], v["doc_line"], v["estado"], v["veredicto"],
                md_escape(v["evidencia"]), md_escape(v.get("notas", ""))))
        if not getattr(self, "verifications", []):
            lines.append("| — | — | — | SIN_EVIDENCIA | SIN_EVIDENCIA | sin claims en la doc |")
        lines += ["", "## GAPS", "",
                  "| id | tipo | sev | estado | veredicto | componente | evidencia | notas |",
                  "|---|---|---|---|---|---|---|---|"]
        for g in self.gaps:
            lines.append("| %s | %s | %s | %s | %s | %s | `%s` | %s |" % (
                g["id"], g["tipo"], g["severidad"], g["estado"], g["veredicto"],
                md_escape(g["componente"]), md_escape(g["evidencia"]),
                md_escape(g.get("notas", ""))))
        if not self.gaps:
            lines.append("| — | — | — | — | SIN_EVIDENCIA | — | SIN_EVIDENCIA | sin gaps detectados |")
        lines += ["", "## FIJAR (fixes) por estado", ""]
        lines += ["| id | estado | componente |", "|---|---|---|"]
        for g in self.gaps:
            lines.append("| %s | %s | %s |" % (g["id"], g["estado"], md_escape(g["componente"])))
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------- fase 7 ---
    def phase7(self) -> None:
        if self.phase_done(7):
            data = read_json(self.p("raw", "actions.json"))
            if isinstance(data, dict) and "actions" in data:
                self.actions = data["actions"]
                self.mark_phase(7, "COMPLETED", {"actions": len(self.actions)})
                self.log("fase 7 acciones reanudadas")
                return
        actions = []
        ordered = sorted(self.gaps, key=lambda g: (SEVERITIES.index(g["severidad"]), g["id"]))
        for gap in ordered:
            acts = []
            if gap["tipo"] == "BROKEN_CANDIDATE":
                acts.append("reparar el import roto y re-ejecutar la auditoria")
            elif gap["tipo"] == "HUÉRFANO":
                acts.append("documentar el componente en el README/arquitectura o retirarlo del alcance")
            elif gap["tipo"] == "DRIFT":
                acts.append("alinear documentacion y codigo (claim %s)" % gap["veredicto"])
            else:
                acts.append("anadir evidencia verificable (ruta:línea) al gap")
            for act in acts:
                actions.append({
                    "id": "ACT-%04d" % (len(actions) + 1),
                    "prioridad": gap["severidad"],
                    "estado": "PENDING" if gap["estado"] == "OPEN" else gap["estado"],
                    "origen": gap["id"],
                    "tipo": gap["tipo"],
                    "accion": act,
                    "componente": gap["componente"],
                    "evidencia": gap["evidencia"],
                    "veredicto": gap["veredicto"],
                })
        self.actions = actions
        write_json(self.p("raw", "actions.json"), {
            "schema": "xray-actions/1", "commit_sha": self.commit_sha,
            "generated_at": utcnow(), "actions": actions,
        })
        self.p("NEXT_ACTIONS.md").write_text(self.render_actions(), encoding="utf-8")
        counts = {}
        for a in actions:
            counts[a["prioridad"]] = counts.get(a["prioridad"], 0) + 1
        self.mark_phase(7, "COMPLETED", {"actions": len(actions), "by_priority": counts})
        self.log("fase 7 acciones: %d %s" % (len(actions), counts))

    def render_actions(self) -> str:
        counts = {}
        for a in self.actions:
            counts[a["prioridad"]] = counts.get(a["prioridad"], 0) + 1
        lines = [
            "# NEXT_ACTIONS — acciones priorizadas P0-P3",
            "",
            "- commit: `%s`" % self.commit_sha,
            "- branch: `%s`" % self.branch,
            "- generado: %s" % utcnow(),
            "- estados de tarea admitidos: %s" % " | ".join(TASK_STATES),
            "",
            "| prioridad | acciones |", "|---|---|",
        ]
        for s in SEVERITIES:
            lines.append("| %s | %d |" % (s, counts.get(s, 0)))
        lines += ["", "| id | prioridad | estado | origen | accion | evidencia |",
                  "|---|---|---|---|---|---|"]
        for a in self.actions:
            lines.append("| %s | %s | %s | %s | %s | `%s` |" % (
                a["id"], a["prioridad"], a["estado"], a["origen"],
                md_escape(a["accion"]), md_escape(a["evidencia"])))
        if not self.actions:
            lines.append("| — | — | — | — | sin acciones (no hay gaps con evidencia) | SIN_EVIDENCIA |")
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------- fase 8 ---
    def phase8(self) -> None:
        if self.phase_done(8):
            if self.p("XRAY_REPORT.md").exists() and self.p("ARCHITECTURE.md").exists():
                self.mark_phase(8, "COMPLETED", {"report": "reusado"})
                self.log("fase 8 compresion reanudada")
                return
        self.p("ARCHITECTURE.md").write_text(self.render_architecture(), encoding="utf-8")
        self.p("XRAY_REPORT.md").write_text(self.render_report(), encoding="utf-8")
        self.mark_phase(8, "COMPLETED", {"report": "XRAY_REPORT.md", "arch": "ARCHITECTURE.md"})
        self.log("fase 8 compresion OK")

    def render_architecture(self) -> str:
        langs = {}
        roots = {}
        for f in self.inventory.values():
            langs[f["language"]] = langs.get(f["language"], 0) + 1
            top = f["path"].split("/", 1)[0] if "/" in f["path"] else "(root)"
            roots[top] = roots.get(top, 0) + 1
        lines = [
            "# ARCHITECTURE — estructura detectada (determinista)",
            "",
            "- commit: `%s` · branch: `%s`" % (self.commit_sha, self.branch),
            "- generado: %s" % utcnow(),
            "- evidencia: recuentos derivados de `INVENTORY.json` (sin estimacion).",
            "",
            "## RAICES (path · files)",
            "",
            "| path | files |", "|---|---|",
        ]
        for top in sorted(roots):
            lines.append("| `%s` | %d |" % (top, roots[top]))
        lines += ["", "## LENGUAJES (conteo por fichero)", "", "| lenguaje | ficheros |", "|---|---|"]
        for lang in sorted(langs, key=lambda k: (-langs[k], k)):
            lines.append("| %s | %d |" % (lang, langs[lang]))
        counts = self.wiring.get("counts", {})
        lines += ["", "## CABLEADO", "",
                  "| metrica | valor |", "|---|---|",
                  "| imports totales | %s |" % counts.get("imports_total", 0),
                  "| imports resueltos | %s |" % counts.get("resolved", 0),
                  "| imports rotos (BROKEN_CANDIDATE) | %s |" % counts.get("broken_local", 0),
                  "| imports no verificables offline | %s |" % counts.get("unverified_third_party", 0),
                  "", "## CONTRATOS", "",
                  "| metrica | valor |", "|---|---|",
                  "| endpoints | %d |" % len(self.contracts.get("endpoints", [])),
                  "| env vars | %d |" % len(self.contracts.get("env_vars", [])),
                  "", "Evidencia: `WIRING.json`, `CONTRACTS.md`, `raw/contracts.json`.",
                  ""]
        return "\n".join(lines)

    def render_report(self) -> str:
        counts = {}
        for g in self.gaps:
            counts[g["tipo"]] = counts.get(g["tipo"], 0) + 1
        verdict_counts = {}
        for g in self.gaps:
            verdict_counts[g["veredicto"]] = verdict_counts.get(g["veredicto"], 0) + 1
        cov = read_json(self.p("INVENTORY.json")) or {}
        coverage = cov.get("coverage", {})
        lines = [
            "# XRAY_REPORT — compresión de la auditoría (fases 0-9)",
            "",
            "- commit: `%s`" % self.commit_sha,
            "- branch: `%s`" % self.branch,
            "- tree: `%s`" % self.tree_sha,
            "- generado: %s" % utcnow(),
            "- constitution_ref: `%s`" % self.constitution_ref,
            "",
            "## 1 · IDENTIDAD (evidencia: FINGERPRINT.json)",
            "",
            "| campo | valor |", "|---|---|",
            "| repo | %s |" % md_escape(self.repo),
            "| commit_sha | `%s` |" % self.commit_sha,
            "| tree_sha | `%s` |" % self.tree_sha,
            "| ficheros inventariados | %s |" % coverage.get("inventoried", "UNKNOWN"),
            "| ficheros rastreados por git | %s |" % coverage.get("tracked_files", "UNKNOWN"),
            "| excluidos | %s |" % len(coverage.get("excluded", [])),
            "| ausentes | %s |" % len(coverage.get("missing", [])),
            "",
            "## 2 · COBERTURA (solo con evidencia; sin porcentajes estimados)",
            "",
            "| metrica | valor | evidencia |", "|---|---|---|",
            "| inventario | %s/%s ficheros | `INVENTORY.json`.coverage |" % (
                coverage.get("inventoried", "UNKNOWN"), coverage.get("tracked_files", "UNKNOWN")),
            "| simbolos | %s | `raw/symbols.json` |" % sum(len(v) for v in self.symbols.values()),
            "| imports | %s | `WIRING.json`.counts |" % self.wiring.get("counts", {}).get("imports_total", "UNKNOWN"),
            "| endpoints | %s | `CONTRACTS.md` |" % len(self.contracts.get("endpoints", [])),
            "| env vars | %s | `CONTRACTS.md` |" % len(self.contracts.get("env_vars", [])),
            "| gaps | %s | `GAPS.md` |" % len(self.gaps),
            "| acciones | %s | `NEXT_ACTIONS.md` |" % len(self.actions),
            "",
            "## 3 · GAPS por tipo (conteo evidenced)",
            "",
            "| tipo | gaps |", "|---|---|",
        ]
        for t in GAP_TYPES:
            lines.append("| %s | %d |" % (t, counts.get(t, 0)))
        lines += ["", "## 4 · Veredictos docs vs code", "",
                  "| veredicto | filas |", "|---|---|"]
        for v in VERDICTS:
            lines.append("| %s | %d |" % (v, verdict_counts.get(v, 0)))
        lines += ["", "## 5 · CONSTITUCIÓN (checklist binario: se cumple o no; no se pondera)", "",
                  "| item | estado | evidencia |", "|---|---|---|"]
        closure = read_json(self.p("raw", "closure.json")) or {}
        for item in closure.get("items", []):
            lines.append("| %s | %s | %s |" % (
                item["id"], "OK" if item["status"] == "PASS" else "FALLA",
                md_escape(item.get("evidence", ""))))
        lines += ["", "## 6 · ESTADO DE LA TAREA", "",
                  "| campo | valor |", "|---|---|",
                  "| estado | VALIDATING (cierre en fase 9) |",
                  "| fase actual | %s |" % PHASE_NAMES.get(self.state.get("current_phase", -1), "UNKNOWN"),
                  "| gaps abiertos | %d |" % sum(1 for g in self.gaps if g["estado"] == "OPEN"),
                  "", "## 7 · Artefactos", ""]
        for name in ("STATE.json", "MANIFEST.md", "ARCHITECTURE.md", "WIRING.json", "INVENTORY.json",
                     "CONTRACTS.md", "GAPS.md", "NEXT_ACTIONS.md", "XRAY_REPORT.md", "FINGERPRINT.json"):
            lines.append("- `%s`" % name)
        lines.append("- `raw/`")
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------- fase 9 ---
    def phase9(self) -> None:
        self.mark_phase(9, "EXECUTING", {"stage": "fingerprint + validacion"})
        fingerprint = self.build_fingerprint()
        write_json(self.p("FINGERPRINT.json"), fingerprint)
        report = self.validate(fingerprint)
        write_json(self.p("raw", "validation.json"), report)
        # item 8: el fichero de validacion existe y es coherente
        item8_ok = report["PASS"]
        closure = self.build_closure(report, item8_ok)
        write_json(self.p("raw", "closure.json"), closure)
        report["checks"] = closure["items"]
        report["closure"] = {"total": len(closure["items"]),
                             "passed": sum(1 for i in closure["items"] if i["status"] == "PASS")}
        write_json(self.p("raw", "validation.json"), report)
        # el informe comprimido se re-renderiza con el checklist binario de cierre
        self.p("XRAY_REPORT.md").write_text(self.render_report(), encoding="utf-8")
        self.p("MANIFEST.md").write_text(self.render_manifest(), encoding="utf-8")
        self.mark_phase(9, "COMPLETED" if report["PASS"] else "FAILED",
                        {"PASS": report["PASS"], "errors": len(report["errors"])})
        if report["PASS"]:
            print("XRAY COMPLETE")
            self.log("validacion PASS=true (%d checks, 0 errores)" % len(closure["items"]))
        else:
            print("XRAY INCOMPLETE")
            for err in report["errors"][:20]:
                self.log("ERROR %s :: %s" % (err.get("check"), err.get("detail")))

    def build_fingerprint(self) -> dict:
        langs = {}
        roots = {}
        for f in self.inventory.values():
            langs[f["language"]] = langs.get(f["language"], 0) + 1
            top = f["path"].split("/", 1)[0] if "/" in f["path"] else "(root)"
            node = roots.setdefault(top, {"path": top, "files": 0, "sha256": hashlib.sha256()})
            node["files"] += 1
        for top in sorted(roots):
            parts = []
            for f in sorted(self.inventory.values(), key=lambda x: x["path"]):
                if (f["path"].split("/", 1)[0] if "/" in f["path"] else "(root)") != top:
                    continue
                parts.append("%s:%s" % (f["path"], f["sha256"]))
            roots[top]["sha256"] = sha256_bytes("\n".join(parts).encode("utf-8"))
        bytes_total = sum(f["bytes"] for f in self.inventory.values())
        return {
            "schema": SCHEMA_FINGERPRINT,
            "repo": self.repo,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "commit_date": self.commit_date,
            "tree_sha": self.tree_sha,
            "languages": langs,
            "file_count": len(self.inventory),
            "bytes_total": bytes_total,
            "roots": [roots[k] for k in sorted(roots)],
            "constitution_ref": self.constitution_ref,
            "generated_at": utcnow(),
        }

    # ------------------------------------------------------------ validate --
    def validate(self, fingerprint: dict) -> dict:
        errors, checks = [], []

        def check(cid: str, ok: bool, detail: str) -> None:
            checks.append({"id": cid, "status": "PASS" if ok else "FAIL", "evidence": detail})
            if not ok:
                errors.append({"check": cid, "detail": detail})

        # 1 STATE.json + fases 0-9 completas
        phases = (self.state or {}).get("phases", {})
        missing_phases = [str(i) for i in range(9)
                          if phases.get(str(i), {}).get("status") != "COMPLETED"]
        phase9 = phases.get("9", {}).get("status")
        ok1 = (not missing_phases and self.p("STATE.json").exists()
               and phase9 in ("COMPLETED", "EXECUTING"))
        check("1_STATE_FASES_0_9", ok1,
              "STATE.json presente; fases 0-8 completas=%d/9; fase9=%s (se marca COMPLETED al cerrar la fase)" % (
                  9 - len(missing_phases), phase9))

        # 2 FINGERPRINT con commit_sha + tree_sha
        ok2 = bool(re.fullmatch(r"[0-9a-f]{40,64}", str(fingerprint.get("commit_sha", "")))) and \
              bool(re.fullmatch(r"[0-9a-f]{40,64}", str(fingerprint.get("tree_sha", ""))))
        check("2_FINGERPRINT_COMMIT_TREE", ok2,
              "commit_sha=%s tree_sha=%s commit_date=%s" % (
                  fingerprint.get("commit_sha"), fingerprint.get("tree_sha"),
                  fingerprint.get("commit_date")))

        # 3 INVENTORY cubre 100% de git ls-files (menos excluidos)
        code, out, _ = git(self.root, "ls-files", "-z")
        tracked = {p for p in out.split("\0") if p}
        inv = set(self.inventory)
        excluded = set((read_json(self.p("INVENTORY.json")) or {}).get("coverage", {}).get("excluded", []))
        missing = sorted(tracked - inv - excluded)
        check("3_INVENTARIO_COBRE_100", not missing,
              "tracked=%d inventariados=%d excluidos=%d ausentes=%d" % (
                  len(tracked), len(inv), len(excluded), len(missing)))

        # 4 WIRING.json con imports reales, no vacios
        imports = self.wiring.get("imports", [])
        real = [i for i in imports if i.get("from_path") and i.get("line")]
        check("4_WIRING_IMPORTS_NO_VACIOS", bool(imports) and len(real) == len(imports),
              "imports=%d con_ruta_linea=%d" % (len(imports), len(real)))

        # 5 CONTRACTS.md con endpoints/env + ruta:línea
        contracts_md = self.p("CONTRACTS.md")
        md_text = contracts_md.read_text(encoding="utf-8") if contracts_md.exists() else ""
        rows = [l for l in md_text.splitlines() if l.startswith("| ") and "|" in l[2:]]
        bad_rows = []
        for row in rows:
            if "|---" in row:
                continue
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            low = [c.strip("`* ").lower() for c in cells]
            # fila de cabecera (metodo/ruta/evidencia/sha256/variable/...) -> no se valida
            if any(h in ("metodo", "variable", "evidencia", "sha256", "ruta", "ruta:linea") for h in low):
                continue
            # una fila es valida si CUALQUIER celda contiene una referencia ruta:línea
            if not any(LINE_REF_RE.search(c) for c in cells):
                bad_rows.append(row[:80])
        check("5_CONTRACTS_RUTA_LINEA", contracts_md.exists() and not bad_rows,
              "CONTRACTS.md presente; endpoints=%d env_vars=%d filas_sin_ruta_linea=%d" % (
                  len(self.contracts.get("endpoints", [])), len(self.contracts.get("env_vars", [])),
                  len(bad_rows)))

        # 6 GAPS.md todos con veredicto
        gaps_md = self.p("GAPS.md")
        gtext = gaps_md.read_text(encoding="utf-8") if gaps_md.exists() else ""
        gap_rows, ver_rows, bad_verdicts = [], [], []
        for table in self.parse_md_tables(gtext):
            header = table["header"]
            if "veredicto" not in header:
                continue
            vidx = header.index("veredicto")
            for cells in table["rows"]:
                verdict = cells[vidx].strip().strip("`")
                if verdict not in VERDICTS:
                    bad_verdicts.append(cells[0])
                if re.fullmatch(r"AUD-\d{4}|GAP-\d{4}", cells[0] or ""):
                    gap_rows.append(cells)
                elif re.fullmatch(r"CLM-\d{4}", cells[0] or ""):
                    ver_rows.append(cells)
        check("6_GAPS_VEREDICTOS", not bad_verdicts and bool(gap_rows or ver_rows),
              "filas_gap=%d filas_verificacion=%d veredictos_invalidos=%d" % (
                  len(gap_rows), len(ver_rows), len(bad_verdicts)))

        # 7 NEXT_ACTIONS.md con evidencia + prioridad
        na = self.p("NEXT_ACTIONS.md")
        ntext = na.read_text(encoding="utf-8") if na.exists() else ""
        act_rows, bad_actions = [], []
        for table in self.parse_md_tables(ntext):
            header = table["header"]
            if "prioridad" not in header or "evidencia" not in header:
                continue
            pidx = header.index("prioridad")
            eidx = header.index("evidencia")
            for cells in table["rows"]:
                if not re.fullmatch(r"ACT-\d{4}", cells[0] or ""):
                    continue
                act_rows.append(cells)
                prio = cells[pidx].strip()
                ev = cells[eidx].strip().strip("`")
                if prio not in SEVERITIES or (":" not in ev and ev != "SIN_EVIDENCIA"):
                    bad_actions.append(cells[0])
        # Si no hay gaps abiertos, la ausencia de acciones es el estado correcto:
        # el check debe pasar con la nota explicita (no con un falso FAIL).
        check("7_NEXT_ACTIONS_EVIDENCIA", not bad_actions and (bool(act_rows) or not self.gaps),
              "acciones=%d invalidas=%d gaps=%d" % (len(act_rows), len(bad_actions), len(self.gaps)))

        # 8 raw/validation.json PASS=true (se verifica tras escribir)
        check("8_VALIDATION_PASS", True, "verificado tras la escritura de raw/validation.json")

        # 9 gaps.json con evidencia ruta:línea válida
        store = self.load_store_gaps()
        bad_store = []
        for gap in store:
            ev = gap.get("evidencia", "")
            if self.verdict_for_evidence(ev) != "CONFIRMADO":
                bad_store.append(gap.get("id"))
        check("9_GAPS_JSON_EVIDENCIA", not bad_store,
              "gaps_json=%d invalidos=%d" % (len(store), len(bad_store)))

        # 10 ningún gap sin estado
        no_state = [g.get("id") for g in store if g.get("estado") not in GAP_STATES]
        no_state += [g["id"] for g in self.gaps if g.get("estado") not in GAP_STATES]
        check("10_GAPS_CON_ESTADO", not no_state,
              "gaps_sin_estado=%d (%s)" % (len(no_state), no_state[:5]))

        # 11 cero secretos en las salidas
        leaks, literal_notes = self.scan_secrets()
        check("11_CERO_SECRETOS", not leaks,
              "fugas=%d %s; ocurrencias_literal_prefijo=%d" % (
                  len(leaks), leaks[:3], literal_notes))

        # 12 V4 AUDIT: fingerprint + GAPS + NEXT_ACTIONS del mismo commit
        gaps_commit = self._commit_in_file(self.p("GAPS.md"))
        na_commit = self._commit_in_file(self.p("NEXT_ACTIONS.md"))
        ok12 = (gaps_commit == fingerprint["commit_sha"] == na_commit)
        check("12_V4_MISMO_COMMIT", ok12,
              "fingerprint=%s GAPS.md=%s NEXT_ACTIONS.md=%s" % (
                  fingerprint["commit_sha"][:12], gaps_commit[:12], na_commit[:12]))

        # sha256 de cada fichero inventariado (recomprobacion)
        bad_sha, absent = [], []
        for path, meta in sorted(self.inventory.items()):
            full = self.root / path
            if not full.is_file():
                absent.append(path)
                continue
            if sha256_file(full) != meta["sha256"]:
                bad_sha.append(path)
        check("13_SHA256_RECOMPROBADO", not bad_sha and not absent,
              "ficheros=%d sha_distinto=%d ausentes=%d" % (
                  len(self.inventory), len(bad_sha), len(absent)))

        return {
            "schema": "xray-validation/1",
            "PASS": not errors,
            "errors": errors,
            "checks": checks,
            "generated_at": utcnow(),
        }

    def _commit_in_file(self, path: Path) -> str:
        if not path.exists():
            return ""
        m = re.search(r"commit:\s*`([0-9a-f]{7,64})`", path.read_text(encoding="utf-8"))
        return m.group(1) if m else ""

    @staticmethod
    def parse_md_tables(text: str):
        """Parsea tablas markdown -> [{section, header, rows}] (determinista)."""
        tables, section, header = [], "", None
        for line in text.splitlines():
            if line.startswith("#"):
                section = line.strip("# ").strip()
                header = None
                continue
            if not line.startswith("|"):
                header = None
                continue
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if not cells or set("".join(cells)) <= set("-: "):
                continue
            if header is None:
                header = [c.lower() for c in cells]
                tables.append({"section": section, "header": header, "rows": []})
                continue
            if len(cells) != len(header):
                continue
            tables[-1]["rows"].append(cells)
        return tables

    def scan_secrets(self):
        """Busca secretos en las salidas. Bloqueante: prefijo + cuerpo de token."""
        leaks, literal = [], 0
        for path in sorted(self.out.rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                for m in SECRET_RE.finditer(line):
                    leaks.append({"file": path.relative_to(self.out).as_posix(),
                                  "line": idx, "pattern": m.group(0)[:8] + "..."})
                    break
            literal += sum(text.count(prefix) for prefix in SECRET_PREFIXES)
        return leaks, literal

    def build_closure(self, report: dict, item8_ok: bool) -> dict:
        items = list(report["checks"])
        for item in items:
            if item["id"] == "8_VALIDATION_PASS":
                item["status"] = "PASS" if item8_ok else "FAIL"
                item["evidence"] = ("raw/validation.json escrito con PASS=%s" % report["PASS"])
                if not item8_ok:
                    report["errors"].append({"check": "8_VALIDATION_PASS", "detail": "PASS=false"})
        return {"schema": "xray-closure/1", "commit_sha": self.commit_sha,
                "generated_at": utcnow(), "items": items}

    def render_manifest(self) -> str:
        names = ["STATE.json", "MANIFEST.md", "ARCHITECTURE.md", "WIRING.json", "INVENTORY.json",
                 "CONTRACTS.md", "GAPS.md", "NEXT_ACTIONS.md", "XRAY_REPORT.md", "FINGERPRINT.json",
                 "raw/tree.json", "raw/symbols.json", "raw/imports.json", "raw/contracts.json",
                 "raw/claims.json", "raw/comparison.json", "raw/gaps.json", "raw/actions.json",
                 "raw/closure.json", "raw/validation.json"]
        lines = ["# MANIFEST — artefactos de la auditoría X-Ray", "",
                 "- commit: `%s` · branch: `%s`" % (self.commit_sha, self.branch),
                 "- generado: %s" % utcnow(),
                 "- `MANIFEST.md` (este fichero) se auto-declara y no incluye su propio sha256.", "",
                 "| artefacto | bytes | sha256 |", "|---|---|---|"]
        for name in names:
            path = self.out / name
            if not path.exists():
                lines.append("| `%s` | — | MISSING |" % name)
                continue
            data = path.read_bytes()
            lines.append("| `%s` | %d | `%s` |" % (name, len(data), sha256_bytes(data)))
        lines.append("")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="xray_audit.py",
                                 description="Auditor X-Ray determinista (fases 0-9)")
    ap.add_argument("--root", required=True, help="raiz del repo a auditar")
    ap.add_argument("--out", required=True, help="directorio de salida")
    ap.add_argument("--gaps", default=None, help="gaps.json a recoger (por defecto <out>/gaps.json o <script_dir>/gaps.json)")
    ap.add_argument("--force", action="store_true", help="rehacer todas las fases ignorando STATE.json")
    ap.add_argument("--no-resume", action="store_true", help="ignorar checkpoints de STATE.json")
    ap.add_argument("--exclude", action="append", default=[], help="glob extra excluido del inventario")
    ap.add_argument("--max-rows", type=int, default=200, help="maximo de filas por estado en la comparacion")
    ap.add_argument("--quiet", action="store_true", help="silenciar el log de progreso")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    auditor = Auditor(args.root, args.out, gaps=args.gaps,
                      resume=not args.no_resume, force=args.force,
                      exclude=args.exclude, max_rows=args.max_rows, quiet=args.quiet)
    ok = auditor.run()
    if not ok:
        return 3
    report = read_json(auditor.out / "raw" / "validation.json") or {}
    return 0 if report.get("PASS") else 4


if __name__ == "__main__":
    sys.exit(main())
