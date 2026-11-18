#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTOR DE DEPLOY · fail-closed · yaiwes.node/v2 · N4-D2

Reglas duras implementadas (INPUT BLOCK VERBATIM "MOTOR DE DEPLOY (reglas duras)"):
  · fail-closed
  · fast-forward NUNCA force
  · sin LFS (nada de punteros .lfs-ref ni .gitattributes con LFS)
  · sin GitHub Actions
  · sin Vercel/HF sin autorización
  · dry-run por defecto
  · expected HEAD obligatorio (si el HEAD no coincide -> CONFLICT y aborta)
  · read-back obligatorio (sha256 del bloque escrito == sha256 local)
  · el token va SOLO por variable de entorno, nunca en logs ni en el HTML

API publica:
  plan(files, root, repo, branch, expected_head)            -> dict  (sin ejecutar, sin escribir)
  validate_preconditions(...)                               -> dict  (checks, nunca lanza)
  execute(files, root, repo, branch, expected_head, ...)    -> dict  (dry-run o manifiesto)

PUSH TRANSACCIONAL (Git Data API): blobs -> tree -> commit -> ref produce UN SOLO
commit para todos los ficheros. El metodo anterior (PUT /contents/ por fichero)
generaba un commit por fichero. El resto del motor (10 checks fail-closed, dry-run
por defecto, expected HEAD, doble autorizacion, read-back, manifiesto, ledger) se
mantiene IDENTICO: el cambio es solo de transporte.

Cero dependencias externas (solo stdlib). Cero llamadas de red en el camino por defecto:
la unica ruta que sale a la red es `push_fast_forward()`, doblemente bloqueada
(DEPLOY_AUTHORIZED=1 + allow_push explicito) y NO se ejecuta en esta tarea.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------- #
# Constantes (ninguna proviene de fuera de la ley del brief)
# --------------------------------------------------------------------------- #

MAX_FILE_BYTES = int(os.environ.get("DEPLOY_MAX_FILE_BYTES", 5_000_000))
MAX_TOTAL_BYTES = int(os.environ.get("DEPLOY_MAX_TOTAL_BYTES", 12_582_912))

LFS_POINTER_MARKER = "version https://git-lfs.github.com/spec/v1"
LFS_REF_SUFFIX = ".lfs-ref"
GITATTRIBUTES = ".gitattributes"
WORKFLOWS_PREFIX = ".github/workflows"

# Variables de entorno donde puede vivir el token. NUNCA se escribe su valor.
TOKEN_ENV_VARS = ("GITHUB_TOKEN", "GH_TOKEN", "HF_TOKEN", "HF_TOKEN_1_NEW", "UNIVERSAL_KEY")
AUTH_ENV_VAR = "DEPLOY_AUTHORIZED"

# Claves prohibidas dentro de cualquier payload (contrato MCP: sin credenciales).
FORBIDDEN_PAYLOAD_KEYS = (
    "token", "secret", "password", "passwd", "api_key", "apikey",
    "authorization", "bearer", "credential", "private_key", "access_key",
)


class DeployAbort(Exception):
    """Abort fail-closed con codigo estable."""

    def __init__(self, code: str, message: str, detail=None):
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.detail = detail if detail is not None else {}

    def to_dict(self):
        return {"status": "ABORT", "code": self.code, "message": self.message, "detail": self.detail}


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _is_lfs_pointer(content: str) -> bool:
    """¿El contenido es un puntero LFS real?

    Un puntero LFS tiene el marcador en la PRIMERA linea seguido de
    "oid sha256:<hex>" y "size <n>". Buscar el marcador en cualquier parte
    daba un falso positivo con el propio codigo del motor (que contiene el
    literal para DETECTAR punteros) y con cualquier documentacion que lo cite.
    """
    lines = (content or "").strip().splitlines()
    if not lines or lines[0].strip() != LFS_POINTER_MARKER:
        return False
    return any(l.strip().startswith("oid sha256:") for l in lines[1:4])


def _env(env=None) -> dict:
    return dict(os.environ if env is None else env)


def _token_from_env(env=None) -> tuple:
    """Devuelve (nombre_variable, valor) del primer token presente. El valor NUNCA se loguea."""
    e = _env(env)
    for name in TOKEN_ENV_VARS:
        val = e.get(name)
        if val and val.strip():
            return name, val.strip()
    return None, None


def _redact(text: str, env=None) -> str:
    """Elimina cualquier valor de token que pudiera aparecer en un texto de salida."""
    if text is None:
        return ""
    out = str(text)
    e = _env(env)
    for name in TOKEN_ENV_VARS:
        val = e.get(name)
        if val and len(val) >= 8:
            out = out.replace(val, "***REDACTED:%s***" % name)
    return out


def _norm_rel(path: str) -> str:
    """Normaliza una ruta relativa de fichero. Aborta si escapa o es absoluta."""
    raw = str(path if path is not None else "").replace("\\", "/").strip()
    if not raw:
        raise DeployAbort("RUTA_VACIA", "La ruta del fichero esta vacia.")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise DeployAbort("RUTA_ABSOLUTA", "Ruta absoluta no permitida: %s" % raw)
    parts = []
    for seg in raw.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            raise DeployAbort("RUTA_ESCAPE", "La ruta escapa de la raiz: %s" % raw)
        parts.append(seg)
    if not parts:
        raise DeployAbort("RUTA_VACIA", "La ruta normalizada esta vacia: %s" % raw)
    return "/".join(parts)


def _abs(root: str, rel: str) -> str:
    return os.path.normpath(os.path.join(os.path.abspath(root), rel.replace("/", os.sep)))


def _inside(child: str, parent: str) -> bool:
    child = os.path.abspath(child)
    parent = os.path.abspath(parent)
    if child == parent:
        return True
    return child.startswith(parent.rstrip(os.sep) + os.sep)


def _local_head(root: str) -> str:
    """HEAD local del repo git bajo root (solo lectura). None si no se puede determinar."""
    git_dir = os.path.join(os.path.abspath(root), ".git")
    if not os.path.exists(git_dir):
        return None
    head_file = os.path.join(git_dir, "HEAD")
    try:
        with open(head_file, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
    except OSError:
        return None
    if content.startswith("ref:"):
        ref = content.split(" ", 1)[1].strip()
        ref_file = os.path.join(git_dir, ref.replace("/", os.sep))
        try:
            with open(ref_file, "r", encoding="utf-8") as fh:
                return fh.read().strip()
        except OSError:
            return None
    return content or None


def _scan_payload_keys(payload) -> list:
    """Rutas de claves prohibidas dentro de un payload anidado."""
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, val in node.items():
                low = str(key).lower()
                if any(low == bad or low.endswith("_" + bad) or low.endswith(bad) for bad in FORBIDDEN_PAYLOAD_KEYS):
                    found.append((path + "." + str(key)).lstrip("."))
                walk(val, path + "." + str(key))
        elif isinstance(node, list):
            for idx, val in enumerate(node):
                walk(val, "%s[%d]" % (path, idx))

    walk(payload, "")
    return found


def _normalize_files(files) -> list:
    """Normaliza la entrada de ficheros a [{path, content, sha256, bytes}]."""
    if files is None:
        raise DeployAbort("SIN_FICHEROS", "No se han recibido ficheros que desplegar.")
    if isinstance(files, dict):
        files = [files]
    if not isinstance(files, (list, tuple)) or len(files) == 0:
        raise DeployAbort("SIN_FICHEROS", "La lista de ficheros esta vacia.")
    out = []
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise DeployAbort("FICHERO_INVALIDO", "Cada fichero debe ser un objeto {path, content}.")
        if item.get("type") == "symlink" or item.get("symlink"):
            raise DeployAbort("SYMLINK_PROHIBIDO", "Los symlinks no se pueden desplegar.")
        rel = _norm_rel(item.get("path"))
        if rel in seen:
            raise DeployAbort("FICHERO_DUPLICADO", "Ruta de fichero duplicada: %s" % rel)
        seen.add(rel)
        content = item.get("content")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise DeployAbort("CONTENT_INVALIDO", "El contenido de %s debe ser texto." % rel)
        raw = content.encode("utf-8")
        out.append({
            "path": rel,
            "content": content,
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
        })
    return out


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def _chk(cid, ok, level, detail):
    return {"id": cid, "ok": bool(ok), "level": level, "detail": detail}


def validate_preconditions(files, root, repo=None, branch=None, expected_head=None,
                           current_head=None, env=None) -> dict:
    """
    Checks fail-closed. NUNCA lanza: devuelve el estado real de cada check.
    level 'block' -> impide plan/execute. level 'warn' -> informativo/verificacion pendiente.
    """
    checks = []
    e = _env(env)

    # --- 0. forma de la entrada -------------------------------------------------
    try:
        norm = _normalize_files(files)
    except DeployAbort as exc:
        checks.append(_chk("ENTRADA_VALIDA", False, "block", exc.code + ": " + exc.message))
        return {"ok": False, "checks": checks, "failed": ["ENTRADA_VALIDA"], "total_bytes": 0,
                "files": [], "created_at": _now_iso()}
    checks.append(_chk("ENTRADA_VALIDA", True, "info", "%d fichero(s) normalizado(s)." % len(norm)))

    # --- 1. LFS ------------------------------------------------------------------
    lfs_hits = []
    for f in norm:
        rel = f["path"]
        if rel.endswith(LFS_REF_SUFFIX):
            lfs_hits.append(rel + " (puntero .lfs-ref)")
        if rel == GITATTRIBUTES or rel.endswith("/" + GITATTRIBUTES):
            low = f["content"].lower()
            if "filter=lfs" in low or "lfs" in low:
                lfs_hits.append(rel + " (.gitattributes con LFS)")
        if LFS_POINTER_MARKER in f["content"] and _is_lfs_pointer(f["content"]):
            lfs_hits.append(rel + " (puntero LFS en contenido)")
    checks.append(_chk("NO_LFS", not lfs_hits, "block",
                       "LFS detectado: " + "; ".join(lfs_hits) if lfs_hits else "sin punteros LFS ni .gitattributes LFS."))

    # --- 2. GitHub Actions -------------------------------------------------------
    wf_hits = [f["path"] for f in norm
               if f["path"] == WORKFLOWS_PREFIX or f["path"].startswith(WORKFLOWS_PREFIX + "/")]
    checks.append(_chk("NO_GITHUB_ACTIONS", not wf_hits, "block",
                       "workflows detectados: " + "; ".join(wf_hits) if wf_hits else "sin workflows."))

    # --- 3. rutas dentro de la raiz --------------------------------------------
    root_abs = os.path.abspath(root or ".")
    escape = []
    for f in norm:
        target = _abs(root_abs, f["path"])
        if not _inside(target, root_abs):
            escape.append(f["path"])
    checks.append(_chk("RUTAS_DENTRO_DE_RAIZ", not escape, "block",
                       "rutas fuera de raiz: " + "; ".join(escape) if escape else "todas dentro de la raiz."))

    # --- 4. symlinks ------------------------------------------------------------
    sym_hits = []
    for f in norm:
        target = _abs(root_abs, f["path"])
        cur = os.path.dirname(target)
        while _inside(cur, root_abs) and cur != root_abs:
            if os.path.islink(cur):
                sym_hits.append(f["path"])
                break
            cur = os.path.dirname(cur)
    checks.append(_chk("SIN_SYMLINKS", not sym_hits, "block",
                       "symlink en la ruta: " + "; ".join(sorted(set(sym_hits))) if sym_hits else "sin symlinks."))

    # --- 5. tamano --------------------------------------------------------------
    total = sum(f["bytes"] for f in norm)
    big = [f["path"] for f in norm if f["bytes"] > MAX_FILE_BYTES]
    checks.append(_chk("TAMANO_MAXIMO", (not big) and total <= MAX_TOTAL_BYTES, "block",
                       "supera el maximo por fichero: " + "; ".join(big) if big
                       else ("total %d B (max %d B)" % (total, MAX_TOTAL_BYTES))))

    # --- 6. credenciales dentro de los ficheros ---------------------------------
    secret_hits = []
    for f in norm:
        for name in TOKEN_ENV_VARS:
            val = e.get(name)
            if val and len(val) >= 8 and val in f["content"]:
                secret_hits.append("%s (token de %s)" % (f["path"], name))
    checks.append(_chk("SIN_CREDENCIALES_EN_FICHEROS", not secret_hits, "block",
                       "credenciales detectadas: " + "; ".join(secret_hits) if secret_hits
                       else "ningun token de entorno aparece en el contenido."))

    # --- 7. HEAD esperado -------------------------------------------------------
    if expected_head and current_head:
        head_ok = hmac.compare_digest(str(expected_head), str(current_head))
        checks.append(_chk("HEAD_ESPERADO", head_ok, "block",
                           "HEAD esperado %s / actual %s" % (expected_head, current_head)))
    elif expected_head and not current_head:
        checks.append(_chk("HEAD_ESPERADO", False, "warn",
                           "HEAD actual no verificable en este momento."))
    else:
        checks.append(_chk("HEAD_ESPERADO", False, "warn",
                           "expected HEAD no informado (obligatorio solo en execute)."))

    # --- 8. autorizacion (informativa en plan) ----------------------------------
    authorized = str(e.get(AUTH_ENV_VAR, "")).strip() == "1"
    token_name, _token = _token_from_env(env)
    checks.append(_chk("AUTORIZACION_DESPLIEGUE", authorized, "warn",
                       "DEPLOY_AUTHORIZED=1 presente" if authorized else "DEPLOY_AUTHORIZED!=1 (dry-run)"))
    checks.append(_chk("TOKEN_POR_ENTORNO", bool(token_name), "warn",
                       "token disponible via %s" % token_name if token_name else "sin token en el entorno"))

    failed = [c["id"] for c in checks if not c["ok"] and c["level"] == "block"]
    return {
        "ok": not failed,
        "checks": checks,
        "failed": failed,
        "total_bytes": total,
        "files": [{"path": f["path"], "bytes": f["bytes"], "sha256": f["sha256"]} for f in norm],
        "created_at": _now_iso(),
    }


# --------------------------------------------------------------------------- #
# Plan
# --------------------------------------------------------------------------- #

def plan(files, root, repo=None, branch=None, expected_head=None, current_head=None, env=None) -> dict:
    """
    Devuelve el plan SIN ejecutar y SIN escribir nada en disco.
    Aborta (DeployAbort) si un check de nivel 'block' falla.
    """
    norm = _normalize_files(files)
    root_abs = os.path.abspath(root or ".")
    pre = validate_preconditions(norm, root_abs, repo, branch, expected_head, current_head, env)
    if not pre["ok"]:
        bad = [c for c in pre["checks"] if not c["ok"] and c["level"] == "block"]
        # El HEAD distinto del esperado se reporta siempre como CONFLICT (regla dura).
        abort_code = {"HEAD_ESPERADO": "CONFLICT"}.get(
            bad[0]["id"] if bad else "", bad[0]["id"] if bad else "PRECONDICIONES_FALLIDAS")
        raise DeployAbort(
            abort_code,
            "Precondiciones de plan fallidas: " + ", ".join(c["id"] for c in bad),
            {"failed": pre["failed"], "checks": pre["checks"]},
        )
    return {
        "status": "PLAN",
        "dry_run": True,
        "created_at": _now_iso(),
        "root": root_abs,
        "repo": repo,
        "branch": branch,
        "expected_head": expected_head,
        "current_head": current_head,
        "total_bytes": pre["total_bytes"],
        "files": [
            {
                "path": f["path"],
                "target": _abs(root_abs, f["path"]),
                "bytes": f["bytes"],
                "sha256": f["sha256"],
            }
            for f in norm
        ],
        "manifest_name": "deploy_manifest_%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "checks": pre["checks"],
        "push": {"enabled": False, "reason": "dry-run por defecto; el push exige DEPLOY_AUTHORIZED=1 + allow_push explicito."},
        "notes": [
            "plan no escribe nada en disco",
            "sin LFS, sin GitHub Actions, sin symlinks",
            "el token solo puede venir del entorno",
        ],
    }


# --------------------------------------------------------------------------- #
# Push (bloqueado; no se usa en esta tarea)
# --------------------------------------------------------------------------- #

def _github_ref_path(branch: str) -> str:
    """Ruta de ref para la Git Data API con ramas que contienen '/'."""
    return "heads/" + str(branch).strip().strip("/")


def push_fast_forward(repo, branch, expected_head, files, token=None, env=None, message=None) -> dict:
    """
    Push a GitHub SOLO fast-forward (nunca force). Exige:
      · DEPLOY_AUTHORIZED=1 en el entorno
      · token en el entorno (GITHUB_TOKEN / GH_TOKEN)
      · expected_head == HEAD remoto
    Escribe UN SOLO COMMIT para todos los ficheros (Git Data API: blobs -> tree
    -> commit -> ref). El metodo anterior (PUT /contents/ por fichero) generaba
    un commit por fichero: 50 ficheros = 50 commits, y en un Space efimero eso
    es lento y ensucia el historial.

    Tras mover la ref se hace READ-BACK: se relee el commit nuevo y se comprueba
    que el padre es el HEAD esperado (fast-forward real) y que cada blob escrito
    esta en el arbol del commit.
    """
    e = _env(env)
    if str(e.get(AUTH_ENV_VAR, "")).strip() != "1":
        raise DeployAbort("PUSH_SIN_AUTORIZACION", "DEPLOY_AUTHORIZED!=1: push prohibido.")
    name, tok = _token_from_env(env)
    if token:
        tok = token
    if not tok:
        raise DeployAbort("PUSH_SIN_TOKEN", "No hay token de entorno para el push.")
    if not expected_head:
        raise DeployAbort("PUSH_SIN_HEAD", "expected HEAD obligatorio para el push fast-forward.")

    api = "https://api.github.com/repos/%s" % repo
    hdrs = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json",
            "User-Agent": "yaiwes-deploy-engine"}

    def _req(method, url, payload=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}

    ref_path = _github_ref_path(branch)
    ref = _req("GET", api + "/git/ref/" + urllib.parse.quote(ref_path, safe="/"))
    remote_head = (ref.get("object") or {}).get("sha")
    if not remote_head:
        raise DeployAbort("PUSH_RAMA_INEXISTENTE", "La rama remota no existe: %s" % branch,
                          {"branch": branch})
    if not hmac.compare_digest(str(remote_head), str(expected_head)):
        raise DeployAbort("CONFLICT", "HEAD remoto %s != esperado %s" % (remote_head, expected_head),
                          {"remote_head": remote_head, "expected_head": expected_head})

    # --- arbol base: conserva los ficheros que ya existen en el repo ---------
    base_commit = _req("GET", api + "/git/commits/" + remote_head)
    base_tree = (base_commit.get("tree") or {}).get("sha")

    # --- 1) un blob por fichero (contenido en utf-8, sin base64) -------------
    tree_items = []
    blobs = []
    for f in files:
        blob = _req("POST", api + "/git/blobs",
                    {"content": f["content"], "encoding": "utf-8"})
        blob_sha = blob.get("sha")
        if not blob_sha:
            raise DeployAbort("PUSH_BLOB_FALLIDO", "GitHub no devolvio sha para el blob de %s" % f["path"],
                              {"path": f["path"]})
        tree_items.append({"path": f["path"], "mode": "100644", "type": "blob", "sha": blob_sha})
        blobs.append({"path": f["path"], "blob": blob_sha, "sha256": f["sha256"]})

    # --- 2) un arbol con TODOS los ficheros en una sola entrada --------------
    tree_payload = {"tree": tree_items}
    if base_tree:
        tree_payload["base_tree"] = base_tree
    new_tree = _req("POST", api + "/git/trees", tree_payload)
    tree_sha = new_tree.get("sha")
    if not tree_sha:
        raise DeployAbort("PUSH_ARBOL_FALLIDO", "GitHub no devolvio sha para el arbol.")

    # --- 3) un commit con TODOS los ficheros ---------------------------------
    commit_message = message or ("deploy: %d fichero(s) [yaiwes.node/v2]" % len(files))
    new_commit = _req("POST", api + "/git/commits", {
        "message": commit_message,
        "tree": tree_sha,
        "parents": [remote_head],
    })
    commit_sha = new_commit.get("sha")
    if not commit_sha:
        raise DeployAbort("PUSH_COMMIT_FALLIDO", "GitHub no devolvio sha para el commit.")

    # --- 4) mover la ref (force=False: jamas force-push) ----------------------
    _req("PATCH", api + "/git/refs/" + urllib.parse.quote(ref_path, safe="/"),
         {"sha": commit_sha, "force": False})

    # --- 5) READ-BACK ---------------------------------------------------------
    new_ref = _req("GET", api + "/git/ref/" + urllib.parse.quote(ref_path, safe="/"))
    new_head = (new_ref.get("object") or {}).get("sha")
    if new_head != commit_sha:
        raise DeployAbort("PUSH_READBACK_HEAD",
                          "La ref no apunta al commit creado.",
                          {"expected": commit_sha, "actual": new_head})
    read_commit = _req("GET", api + "/git/commits/" + new_head)
    parents = read_commit.get("parents") or []
    if not parents or parents[0].get("sha") != remote_head:
        raise DeployAbort("PUSH_NO_FAST_FORWARD",
                          "El commit no es fast-forward respecto al HEAD esperado.",
                          {"parent": (parents[0] or {}).get("sha") if parents else None,
                           "remote_head": remote_head})
    # El arbol hay que pedirlo RECURSIVO: sin ?recursive=1 GitHub devuelve solo
    # las entradas de primer nivel (p.ej. "chat-router"), no las rutas anidadas,
    # y la comparacion de blobs no encontraria nunca los ficheros escritos.
    read_tree = _req("GET", api + "/git/trees/"
                     + ((read_commit.get("tree") or {}).get("sha") or tree_sha)
                     + "?recursive=1")
    read_entries = {e.get("path"): e.get("sha") for e in (read_tree.get("tree") or [])
                    if e.get("type") == "blob"}
    missing = [b["path"] for b in blobs if read_entries.get(b["path"]) != b["blob"]]
    if missing:
        raise DeployAbort("PUSH_READBACK_BLOBS",
                          "Ficheros que no aparecen en el arbol del commit nuevo.",
                          {"missing": missing})

    return {
        "performed": True,
        "method": "git_data_api",
        "commits": 1,
        "old_head": remote_head,
        "new_head": new_head,
        "tree_sha": tree_sha,
        "fast_forward": True,
        "files": blobs,
        "readback": "OK",
        "token_var": name,
    }


# --------------------------------------------------------------------------- #
# Execute
# --------------------------------------------------------------------------- #

def execute(files, root, repo=None, branch=None, expected_head=None, current_head=None,
            authorization_token=None, dry_run=False, workdir=None, env=None,
            allow_push=False, allow_create_root=True) -> dict:
    """
    Ejecuta el deploy con las reglas duras. Por defecto NO hace push.
    - sin autorizacion (DEPLOY_AUTHORIZED=1)            -> abort
    - sin token de entorno                              -> abort
    - expected HEAD ausente o distinto del actual        -> abort / CONFLICT
    - dry_run=True                                       -> no escribe NADA
    - authorised                                         -> escribe ficheros + read-back + MANIFEST (sin push)
    """
    e = _env(env)
    workdir_abs = os.path.abspath(workdir or os.getcwd())
    root_abs = os.path.abspath(root or ".")

    # --- 1. ficheros y forma ---------------------------------------------------
    norm = _normalize_files(files)

    # --- 2. expected HEAD obligatorio ------------------------------------------
    if not expected_head:
        raise DeployAbort("EXPECTED_HEAD_OBLIGATORIO", "expected HEAD obligatorio para ejecutar el deploy.")
    head_now = current_head if current_head is not None else _local_head(root_abs)
    if not head_now:
        raise DeployAbort("HEAD_NO_VERIFICABLE",
                          "No se pudo verificar el HEAD actual: indica current_head o usa un repo git local.",
                          {"root": root_abs})
    if not hmac.compare_digest(str(expected_head), str(head_now)):
        raise DeployAbort("CONFLICT", "El HEAD no coincide con el esperado: se aborta.",
                          {"expected_head": expected_head, "current_head": head_now})

    # --- 3. precondiciones ------------------------------------------------------
    pre = validate_preconditions(norm, root_abs, repo, branch, expected_head, head_now, env)
    if not pre["ok"]:
        bad = [c for c in pre["checks"] if not c["ok"] and c["level"] == "block"]
        raise DeployAbort(bad[0]["id"], "Precondiciones fallidas: " + ", ".join(c["id"] for c in bad),
                          {"failed": pre["failed"], "checks": pre["checks"]})

    # --- 4. autorizacion --------------------------------------------------------
    authorized = str(e.get(AUTH_ENV_VAR, "")).strip() == "1"
    token_name, env_token = _token_from_env(env)
    if not authorized:
        raise DeployAbort("AUTORIZACION_REQUERIDA",
                          "DEPLOY_AUTHORIZED!=1: despliegue no autorizado (dry-run obligatorio).")
    if not env_token:
        raise DeployAbort("TOKEN_AUSENTE", "No hay token en el entorno: usa GITHUB_TOKEN o GH_TOKEN.")
    if not authorization_token:
        raise DeployAbort("AUTORIZACION_INVALIDA", "Falta el authorization_token de la sesion.")
    if not hmac.compare_digest(str(authorization_token), str(env_token)):
        raise DeployAbort("AUTORIZACION_INVALIDA", "El authorization_token no coincide con el token del entorno.")

    # --- 5. la raiz debe estar dentro del directorio de trabajo ----------------
    if not _inside(root_abs, workdir_abs):
        raise DeployAbort("RAIZ_FUERA_DEL_TRABAJO",
                          "La raiz de destino esta fuera del directorio de trabajo.",
                          {"root": root_abs, "workdir": workdir_abs})

    manifest = {
        "status": "DRY_RUN" if dry_run else "MANIFEST_ONLY_NO_PUSH",
        "dry_run": bool(dry_run),
        "created_at": _now_iso(),
        "root": root_abs,
        "workdir": workdir_abs,
        "repo": repo,
        "branch": branch,
        "expected_head": expected_head,
        "current_head": head_now,
        "token_env_var": token_name,
        "files": [{"path": f["path"], "bytes": f["bytes"], "sha256": f["sha256"]} for f in norm],
        "checks": pre["checks"],
        "push": {"enabled": False, "performed": False,
                 "reason": "push solo con DEPLOY_AUTHORIZED=1 + allow_push explicito; en esta tarea jamas se ejecuta."},
    }
    manifest["tree_sha256"] = sha256_text(
        "\n".join("%s %s" % (f["sha256"], f["path"]) for f in manifest["files"])
    )

    # --- 6. dry-run: no escribe nada -------------------------------------------
    if dry_run:
        manifest["written"] = []
        manifest["manifest_path"] = None
        manifest["note"] = "dry-run: no se ha escrito nada en disco."
        return manifest

    # --- 7. escritura + read-back ----------------------------------------------
    if not os.path.isdir(root_abs):
        if not allow_create_root:
            raise DeployAbort("RAIZ_NO_EXISTE", "La raiz no existe y no se permite crearla.", {"root": root_abs})
        os.makedirs(root_abs, exist_ok=True)

    written = []
    for f in norm:
        target = _abs(root_abs, f["path"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as fh:
            fh.write(f["content"].encode("utf-8"))
        with open(target, "rb") as fh:
            readback = fh.read()
        rb_hash = sha256_bytes(readback)
        if rb_hash != f["sha256"]:
            raise DeployAbort("READBACK_MISMATCH",
                              "El sha256 del bloque escrito no coincide con el local.",
                              {"path": f["path"], "local": f["sha256"], "written": rb_hash})
        written.append({"path": f["path"], "sha256": f["sha256"], "readback_sha256": rb_hash,
                        "bytes": f["bytes"], "readback": "OK"})

    # --- 8. manifiesto ----------------------------------------------------------
    manifest_dir = os.path.join(workdir_abs, "deploy_manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, manifest["manifest_name"]
                                 if "manifest_name" in manifest else
                                 "deploy_manifest_%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    manifest["written"] = written
    manifest["manifest_path"] = manifest_path
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)

    # --- 9. push solo con doble autorizacion explicita ------------------------
    if allow_push:
        try:
            manifest["push"] = push_fast_forward(repo, branch, expected_head, norm, env=env)
            manifest["status"] = "PUSHED_FAST_FORWARD"
        except DeployAbort as exc:
            manifest["push"] = {"enabled": True, "performed": False,
                                 "reason": exc.code + ": " + exc.message}
            manifest["status"] = "ABORT"
    return manifest


# --------------------------------------------------------------------------- #
# CLI de diagnostico (no despliega: solo plan / checks)
# --------------------------------------------------------------------------- #

def _cli(argv):
    if len(argv) < 2:
        print("uso: deploy_engine.py plan|check <fichero.json>")
        return 2
    mode = argv[1]
    try:
        with open(argv[2], "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError) as exc:
        print("ERROR lectura: %s" % exc)
        return 2
    files = payload.get("files") or []
    root = payload.get("root") or "."
    if mode == "plan":
        try:
            out = plan(files, root, payload.get("repo"), payload.get("branch"), payload.get("expected_head"))
        except DeployAbort as exc:
            print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2))
            return 3
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if mode == "check":
        out = validate_preconditions(files, root, payload.get("repo"), payload.get("branch"),
                                     payload.get("expected_head"), payload.get("current_head"))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["ok"] else 3
    print("modo desconocido: %s" % mode)
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
