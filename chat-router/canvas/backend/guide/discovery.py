"""discovery.py · N4-C · GUÍA VIVA — MOTOR DE DESCUBRIMIENTO (RAG sobre 10 dominios).

NO hay crawler propio. Este módulo DELEGA en el motor de búsqueda real del repo
(`motores de descarga y extracción/➡️📂 motor de búsqueda/websearch_engine.py`,
rama `main`, 9.171 B) mediante import por ruta configurable, o mediante un
`search_provider` inyectado con LA MISMA FIRMA:

    provider(query: str, providers: str, limit: int, root: str) -> dict

El payload del motor se normaliza igual que en el repo (`websearch_engine.canon`),
se filtra por dominio (relevancia), se acota (2..5 resultados por dominio, máximo
10 dominios por ciclo) y se cachea por hash.

Si el motor no está, o el provider falla, o no hay resultados ⇒ `NO_EVIDENCE`.
Nunca se inventa evidencia, nunca se marca PASS por ranking.

Uso:
    from discovery import discover
    r = discover("añadir reintento con backoff")             # usa el motor del repo
    r = discover("...", provider=mi_provider_falso)         # sin red, para pruebas
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import urllib.parse
from typing import Any, Callable

SCHEMA = "yaiwes.guide.discovery.v1"

MAX_DOMAINS = 10
MIN_PER_DOMAIN = 2
MAX_PER_DOMAIN = 5
DEFAULT_PER_DOMAIN = 3
DEFAULT_PROVIDERS = os.getenv("GUIDE_SEARCH_PROVIDERS", "duckduckgo,ddgs")
DEFAULT_TIMEOUT_S = int(os.getenv("GUIDE_SEARCH_TIMEOUT_SECONDS", "15"))
DEFAULT_BUDGET_TOKENS = int(os.getenv("GUIDE_DISCOVERY_BUDGET_TOKENS", "5000"))
DEFAULT_CACHE_TTL_S = int(os.getenv("GUIDE_DISCOVERY_CACHE_TTL_SECONDS", "21600"))

ENGINE_RELATIVE = "motores de descarga y extracción/➡️📂 motor de búsqueda/websearch_engine.py"
SOURCES_RELATIVE = "chat-router/Loop cola wachdog/Loop/config/investigation_sources.json"

# Dominios nombrados en el INPUT BLOCK VERBATIM (usados sólo si el repo no está
# disponible en el sandbox; se marca el origen como fallback, nunca como fuente).
FALLBACK_SOURCES: list[dict] = [
    {"source_id": "github", "domain": "github.com"},
    {"source_id": "huggingface", "domain": "huggingface.co"},
    {"source_id": "stackoverflow", "domain": "stackoverflow.com"},
    {"source_id": "python_discourse", "domain": "discuss.python.org"},
    {"source_id": "python_docs", "domain": "docs.python.org"},
    {"source_id": "mdn", "domain": "developer.mozilla.org"},
    {"source_id": "fastapi", "domain": "fastapi.tiangolo.com"},
    {"source_id": "gitlab", "domain": "gitlab.com"},
    {"source_id": "pypi", "domain": "pypi.org"},
    {"source_id": "npm", "domain": "npmjs.com"},
]

# Peso de evidencia por clase de dominio (0..1) — determinista, sin LLM.
PESO_EVIDENCIA = {
    "docs.python.org": 1.0,
    "fastapi.tiangolo.com": 1.0,
    "developer.mozilla.org": 1.0,
    "docs.pytest.org": 1.0,
    "sqlite.org": 1.0,
    "pypi.org": 0.95,
    "npmjs.com": 0.95,
    "github.com": 0.9,
    "huggingface.co": 0.9,
    "stackoverflow.com": 0.85,
    "discuss.python.org": 0.85,
    "gitlab.com": 0.85,
    "owasp.org": 0.9,
}

FORBIDDEN_PATTERNS = (
    r"(?i)\bpip\s+install\b",
    r"(?i)\bnpm\s+install\b",
    r"(?i)\bcurl\b[^\n]*\|\s*(ba)?sh",
    r"(?i)\bssh\b",
    r"(?i)\bsudo\b",
    r"(?i)\brm\s+-rf\b",
    r"(?i)\bchmod\s+777\b",
)

APROBACION_RE = re.compile(
    r"(?i)(autoriz|aprobaci|permiso|permission|approv|advertencia|warning|"
    r"credencial|secret|token|rotar|rotate)"
)

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
VERSION_RE = re.compile(r"\b(v?\d+\.\d+(?:\.\d+)?)\b")
LICENSE_RE = re.compile(r"(?i)\b(MIT|Apache-?2\.0|BSD-?3|GPL-?3|MPL-?2\.0)\b")


# ── Utilidades de ruta / carga ───────────────────────────────────────────────
def _grammar():
    """Carga el motor gramatical hermano (mismo directorio) sin tocar sys.path."""
    try:
        import grammar as _g  # noqa: PLC0415
        return _g
    except ImportError:
        import importlib.util
        import pathlib

        spec = importlib.util.spec_from_file_location(
            "grammar", pathlib.Path(__file__).resolve().parent / "grammar.py"
        )
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


def _repo_roots() -> list[pathlib.Path]:
    roots: list[pathlib.Path] = []
    env_root = os.getenv("GUIDE_REPO_ROOT", "").strip()
    if env_root:
        roots.append(pathlib.Path(env_root))
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        roots.append(parent)
        if len(roots) > 8:
            break
    roots.append(pathlib.Path.cwd())
    out: list[pathlib.Path] = []
    for r in roots:
        if r not in out:
            out.append(r)
    return out


def _resolve(relative: str, env_var: str) -> pathlib.Path | None:
    direct = os.getenv(env_var, "").strip()
    if direct:
        p = pathlib.Path(direct)
        return p if p.exists() else None
    for root in _repo_roots():
        cand = root / relative
        if cand.exists():
            return cand
    return None


def load_sources(path: str | None = None) -> dict:
    """Carga los 10 dominios desde `investigation_sources.json` del repo."""
    target: pathlib.Path | None = None
    if path:
        cand = pathlib.Path(path)
        target = cand if cand.exists() else None
    if target is None:
        target = _resolve(SOURCES_RELATIVE, "GUIDE_INVESTIGATION_SOURCES")
    if target is None:
        return {
            "sources": [dict(s) for s in FALLBACK_SOURCES],
            "origin": "input_block_fallback",
            "path": None,
            "sha256": None,
            "guardrails": {"read_only": True, "require_evidence": True, "max_results": 100},
        }
    raw = target.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    sources = data.get("sources") or []
    if not sources:
        raise ValueError("INVESTIGATION_SOURCES_EMPTY")
    return {
        "sources": sources[:MAX_DOMAINS],
        "origin": str(target),
        "path": str(target),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "guardrails": data.get("guardrails", {}),
    }


def load_engine(path: str | None = None):
    """Importa el motor de búsqueda real del repo por ruta configurable."""
    target: pathlib.Path | None = None
    if path:
        cand = pathlib.Path(path)
        target = cand if cand.exists() else None
    if target is None:
        target = _resolve(ENGINE_RELATIVE, "GUIDE_WEBSEARCH_ENGINE_PATH")
    if target is None:
        return None, None
    spec = importlib.util.spec_from_file_location("yaiwes_websearch_engine", str(target))
    if spec is None or spec.loader is None:
        return None, str(target)
    module = importlib.util.module_from_spec(spec)
    # El módulo debe estar registrado en sys.modules ANTES de ejecutarse:
    # @dataclass (como usa websearch_engine.Result) resuelve cls.__module__ en sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, str(target)


def default_provider(engine) -> Callable[..., dict]:
    """Adapter con LA MISMA FIRMA que `websearch_engine.run`."""
    def provider(query: str, providers: str, limit: int, root: str) -> dict:
        return engine.run(query, providers, limit, pathlib.Path(root))
    return provider


# ── Normalización / validación ───────────────────────────────────────────────
def canon_url(url: str, engine=None) -> str | None:
    """Normaliza una URL (equivalente a `websearch_engine.canon` + filtros)."""
    if not isinstance(url, str) or not url.strip():
        return None
    try:
        raw = url.strip()
        if raw.startswith("//"):
            raw = "https:" + raw
        parts = urllib.parse.urlsplit(raw)
        if parts.scheme not in ("http", "https"):
            return None
        if parts.username or parts.password:      # credenciales en la URL: fuera
            return None
        host = (parts.hostname or "").lower()
        if not host:
            return None
        if engine is not None and hasattr(engine, "canon"):
            try:
                out = engine.canon(raw)
                parts = urllib.parse.urlsplit(out)
                host = (parts.hostname or "").lower()
                if not host:
                    return None
                return out
            except Exception:
                pass
        pairs = [
            (k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith(("utm_", "fbclid", "gclid"))
        ]
        path = re.sub(r"/+$", "", parts.path or "/") or "/"
        return urllib.parse.urlunsplit(
            (parts.scheme.lower(), host, path, urllib.parse.urlencode(pairs, doseq=True), "")
        )
    except Exception:
        return None


def hostname_matches(url: str, domain: str) -> bool:
    """Mismo criterio que `research_prepass.hostname_matches` (relevancia)."""
    try:
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
    except Exception:
        return False
    domain = (domain or "").lower()
    return bool(host) and (host == domain or host.endswith("." + domain))


def _records_from_payload(payload: Any) -> list[dict]:
    """Normaliza el payload del motor a lista de registros {title,url,snippet,...}."""
    rows: list[dict] = []
    if payload is None:
        return rows
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = payload.get("results") or payload.get("records") or []
    else:
        candidates = []
    for item in candidates or []:
        if isinstance(item, str):
            rows.append({"title": "", "url": item, "snippet": "", "provider": "", "rank": len(rows) + 1})
        elif isinstance(item, dict):
            providers = item.get("providers")
            if isinstance(providers, list):
                provider_name = str(providers[0]) if providers else ""
            else:
                provider_name = str(item.get("provider") or "")
            rows.append({
                "title": str(item.get("title") or ""),
                "url": str(item.get("url") or item.get("href") or item.get("link") or ""),
                "snippet": str(item.get("snippet") or item.get("body") or item.get("description") or item.get("content") or ""),
                "provider": provider_name,
                "rank": int(item.get("rank") or item.get("best_rank") or (len(rows) + 1)),
            })
    return rows


def _sanitize_steps(steps: list[str]) -> list[str]:
    """El motor NUNCA propone instalación automática ni shell remoto."""
    out: list[str] = []
    for step in steps:
        if any(re.search(pat, step) for pat in FORBIDDEN_PATTERNS):
            out.append("Revisar manualmente la fuente: el motor no ejecuta instalaciones ni shell remoto.")
        else:
            out.append(step)
    return out


def _prioridad(option: dict, domain: str) -> dict:
    """0..100 = 30 reproducibilidad + 25 evidencia oficial/upstream + 20 compatibilidad
    + 15 tests propuestos + 10 coste/impacto. El ranking NUNCA marca PASS."""
    repro = 0.3
    repro += 0.3 if option.get("versions") else 0.0
    repro += 0.2 if option.get("license") not in (None, "", "NO_EVIDENCE") else 0.0
    repro += 0.2 if len(option.get("steps_proposed", [])) >= 2 else 0.0
    evidencia = PESO_EVIDENCIA.get(domain, 0.6)
    if not option.get("confidence_evidence"):
        evidencia = 0.0
    compat = 1.0 if option.get("versions") else (0.5 if domain in ("pypi.org", "npmjs.com") else 0.2)
    tests = 1.0 if len(option.get("test_plan", [])) >= 2 else 0.0
    if not option.get("versions"):
        tests *= 0.6
    coste = 1.0 if not option.get("files_affected") else (0.8 if len(option["files_affected"]) <= 1 else 0.5)
    score = round(
        30 * min(repro, 1.0) + 25 * min(evidencia, 1.0) + 20 * min(compat, 1.0)
        + 15 * min(tests, 1.0) + 10 * min(coste, 1.0),
        2,
    )
    return {
        "score": max(0, min(100, score)),
        "detalle": {
            "reproducibilidad": round(30 * min(repro, 1.0), 2),
            "evidencia_oficial": round(25 * min(evidencia, 1.0), 2),
            "compatibilidad": round(20 * min(compat, 1.0), 2),
            "tests_propuestos": round(15 * min(tests, 1.0), 2),
            "coste_impacto": round(10 * min(coste, 1.0), 2),
        },
    }


def _build_option(
    *,
    row: dict,
    domain: str,
    source_id: str,
    action: dict,
    gap_ids: list[str],
    files_affected: list[str],
    calls: int,
    approval: bool,
    engine=None,
) -> dict:
    url = canon_url(row.get("url", ""), engine)
    snippet = re.sub(r"\s+", " ", row.get("snippet", "") or "").strip()[:700]
    title = (row.get("title") or "").strip()[:220]
    dates = DATE_RE.findall(snippet + " " + title)
    versions = [v for v in VERSION_RE.findall(snippet + " " + title)]
    license_m = LICENSE_RE.search(snippet)
    license_value = license_m.group(1) if license_m else "NO_EVIDENCE"
    steps = _sanitize_steps([
        f"Consultar la fuente upstream y verificar la versión declarada: {url}",
        "Comparar con el ejemplo de la guía (match.py) antes de escribir código",
        f"Ejecutar el test de la acción «{action.get('objetivo', '')[:80]}» sobre el parche quirúrgico",
    ])
    option = {
        "solution_id": "",
        "gap_ids": list(gap_ids),
        "summary": f"[texto no confiable] {title or url}" + (f" — {snippet[:200]}" if snippet else ""),
        "steps_proposed": steps,
        "upstream_urls": [url] if url else [],
        "source_dates": sorted(set(dates))[:5],
        "versions": sorted(set(versions))[:5],
        "confidence_evidence": [{
            "url": url,
            "title": title,
            "snippet": snippet,
            "provider": row.get("provider", ""),
            "dominio": domain,
            "source_id": source_id,
            "confianza": "evidencia_no_confianza_inventada",
        }],
        "compatibility": (versions[0] if versions else "NO_EVIDENCE"),
        "license": license_value,
        "files_affected": list(files_affected),
        "risk": ("ALTO" if approval else ("MEDIO" if domain not in PESO_EVIDENCIA else "BAJO")),
        "test_plan": [
            "Verificar que el parche sólo cambia las líneas declaradas (match.verify_surgical)",
            f"Ejecutar la suite de la acción y comparar con el ejemplo de la guía",
        ],
        "estimated_calls": calls,
        "approval_needs_approval": approval,
        "fingerprint": "",
    }
    option["solution_id"] = "sol_" + hashlib.sha256((url or "").encode("utf-8")).hexdigest()[:12]
    prio = _prioridad(option, domain)
    option["fingerprint"] = hashlib.sha256(
        json.dumps({k: v for k, v in option.items() if k != "fingerprint"},
                   sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    option["prioridad"] = prio["score"]
    option["prioridad_detalle"] = prio["detalle"]
    option["estado"] = "EVIDENCIA" if url and snippet else "NEEDS_REVIEW"
    return option


# ── Cache por hash ───────────────────────────────────────────────────────────
def _cache_dir() -> pathlib.Path:
    env = os.getenv("GUIDE_DISCOVERY_CACHE_DIR", "").strip()
    path = pathlib.Path(env) if env else pathlib.Path(tempfile.gettempdir()) / "guide-discovery-cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_key(query: str, domains: list[str], providers: str, per_domain: int) -> str:
    raw = "|".join([query, ",".join(domains), providers, str(per_domain)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _cache_read(path: pathlib.Path, ttl: int) -> dict | None:
    if ttl <= 0 or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if (time.time() - path.stat().st_mtime) > ttl:
        return None
    return data


def _cache_write(path: pathlib.Path, payload: dict) -> dict:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    check = json.loads(path.read_text(encoding="utf-8"))
    if check.get("cache_key") != payload.get("cache_key"):
        raise RuntimeError("CACHE_READBACK_MISMATCH")
    return check


# ── Descubrimiento ───────────────────────────────────────────────────────────
def discover(
    action_text: str,
    *,
    query: str | None = None,
    provider: Callable[..., dict] | None = None,
    engine_path: str | None = None,
    sources_path: str | None = None,
    per_domain: int = DEFAULT_PER_DOMAIN,
    providers: str | None = None,
    max_domains: int = MAX_DOMAINS,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    cache_ttl: int = DEFAULT_CACHE_TTL_S,
    force: bool = False,
    gap_ids: list[str] | None = None,
    files_affected: list[str] | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Busca la acción en los dominios autorizados y devuelve OPCIONES con evidencia.

    `provider` inyectado ⇒ mismo contrato que el motor del repo
    (`provider(query, providers, limit, root) -> dict`).
    """
    per_domain = max(MIN_PER_DOMAIN, min(MAX_PER_DOMAIN, int(per_domain)))
    providers = providers or DEFAULT_PROVIDERS
    gap_ids = list(gap_ids or [])
    files_affected = list(files_affected or [])

    action = _grammar().decompose(action_text)
    base_query = (query or action_text or "").strip()
    if not base_query:
        return {
            "schema": SCHEMA,
            "estado": "NO_EVIDENCE",
            "veredicto": "NO_EVIDENCE",
            "motivo": "INPUT_GAP",
            "opciones": [],
            "dominios_consultados": [],
            "estado_dominios": {},
            "cache": {"state": "MISS", "key": None},
            "aprobacion": {"requiere": False, "motivo": None},
            "accion": action,
        }

    src = load_sources(sources_path)
    domains = [s["domain"] for s in src["sources"]][:max(1, min(int(max_domains), MAX_DOMAINS))]

    cache_dir = _cache_dir()
    key = _cache_key(base_query, domains, providers, per_domain)
    cache_path = cache_dir / f"{key}.json"
    cached = None if force else _cache_read(cache_path, cache_ttl)
    if cached:
        cached["cache"] = {"state": "HIT", "key": key, "path": str(cache_path)}
        return cached

    engine = None
    engine_path_used = None
    engine_status = "PROVIDER_INYECTADO"
    if provider is None:
        engine, engine_path_used = load_engine(engine_path)
        if engine is None:
            return {
                "schema": SCHEMA,
                "estado": "NO_EVIDENCE",
                "veredicto": "NO_EVIDENCE",
                "motivo": "ENGINE_PATH_GAP",
                "detalle": f"motor de búsqueda del repo no localizado: {ENGINE_RELATIVE}",
                "opciones": [],
                "dominios_consultados": [],
                "estado_dominios": {},
                "cache": {"state": "MISS", "key": key},
                "aprobacion": {"requiere": False, "motivo": None},
                "accion": action,
            }
        provider = default_provider(engine)
        engine_status = "MOTOR_REPO"

    estado_dominios: dict[str, dict] = {}
    opciones: list[dict] = []
    calls = 0
    used_tokens = 0
    truncado = False
    root = str(cache_dir / "engine-runs")

    for source in src["sources"][:max(1, min(int(max_domains), MAX_DOMAINS))]:
        domain = source["domain"]
        scoped = f"site:{domain} {base_query}"
        try:
            payload = provider(scoped, providers, max(per_domain * 2, per_domain), root)
            calls += 1
        except Exception as exc:
            estado_dominios[domain] = {
                "state": "GAP",
                "detail": f"{type(exc).__name__}:{str(exc)[:200]}",
                "results": 0,
            }
            continue
        rows = _records_from_payload(payload)
        kept = []
        for row in rows:
            url = canon_url(row.get("url", ""), engine)
            if not url or not hostname_matches(url, domain):
                continue          # sin relevancia para el dominio consultado
            snippet = re.sub(r"\s+", " ", row.get("snippet", "") or "").strip()[:700]
            title = (row.get("title") or "").strip()[:220]
            if not snippet and not title:
                continue          # sin señal utilizable
            cost = max(1, (len(title) + len(url) + len(snippet) + 3) // 4)
            if used_tokens + cost > budget_tokens:
                truncado = True
                break
            used_tokens += cost
            kept.append({"title": title, "url": url, "snippet": snippet,
                         "provider": row.get("provider", ""), "rank": row.get("rank", len(kept) + 1)})
            if len(kept) >= per_domain:
                break
        estado_dominios[domain] = {
            "state": "PASS" if kept else "NO_RESULTS",
            "results": len(kept),
            "source_id": source.get("source_id", domain),
        }
        for row in kept:
            text = f"{action_text} {row['title']} {row['snippet']}"
            approval = bool(APROBACION_RE.search(text))
            opciones.append(_build_option(
                row=row, domain=domain, source_id=source.get("source_id", domain),
                action=action, gap_ids=gap_ids, files_affected=files_affected,
                calls=calls, approval=approval, engine=engine,
            ))

    # Dedup por URL canónica (mismo enlace en varios dominios).
    unicas: dict[str, dict] = {}
    for opt in opciones:
        url = (opt["upstream_urls"] or [""])[0]
        prev = unicas.get(url)
        if prev is None or opt["prioridad"] > prev["prioridad"]:
            unicas[url] = opt
    opciones = sorted(unicas.values(), key=lambda o: (-o["prioridad"], o["solution_id"]))

    requiere_aprobacion = any(o["approval_needs_approval"] for o in opciones) or bool(
        APROBACION_RE.search(action_text or "")
    )
    motivo_aprobacion = None
    if requiere_aprobacion:
        m = APROBACION_RE.search(action_text or "")
        motivo_aprobacion = m.group(0) if m else "la evidencia encontrada habla de autorización/advertencia"

    if not opciones:
        estado = "NO_EVIDENCE"
        veredicto = "NO_EVIDENCE"
        motivo = "SIN_RESULTADOS_EN_DOMINIOS_AUTORIZADOS"
    elif all(o["estado"] == "EVIDENCIA" for o in opciones):
        estado = "EVIDENCIA_ENCONTRADA"
        veredicto = "EVIDENCE_FOUND"
        motivo = "opciones_con_evidencia_normalizada"
    else:
        estado = "NEEDS_REVIEW"
        veredicto = "NEEDS_REVIEW"
        motivo = "opciones_incompletas_sin_evidencia_suficiente"

    payload = {
        "schema": SCHEMA,
        "estado": estado,
        "veredicto": veredicto,
        "motivo": motivo,
        "query": base_query,
        "accion": action,
        "opciones": opciones,
        "dominios_consultados": domains,
        "estado_dominios": estado_dominios,
        "sources_origin": src["origin"],
        "sources_sha256": src["sha256"],
        "engine": {"estado": engine_status, "path": engine_path_used,
                   "timeout_s": timeout_s, "providers": providers},
        "presupuesto": {"tokens_estimados": used_tokens, "budget_tokens": budget_tokens,
                        "truncado": truncado, "llamadas": calls},
        "aprobacion": {"requiere": requiere_aprobacion, "motivo": motivo_aprobacion,
                       "destino": "usuario/IA" if requiere_aprobacion else None},
        "cache": {"state": "MISS", "key": key, "path": str(cache_path)},
    }
    try:
        _cache_write(cache_path, payload)
    except Exception:
        payload["cache"]["state"] = "MISS_SIN_ESCRITURA"
    return payload


__all__ = [
    "SCHEMA",
    "MAX_DOMAINS",
    "MIN_PER_DOMAIN",
    "MAX_PER_DOMAIN",
    "discover",
    "load_sources",
    "load_engine",
    "default_provider",
    "canon_url",
    "hostname_matches",
]
