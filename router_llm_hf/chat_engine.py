#!/usr/bin/env python3
"""chat_engine.py — MINIMAX 2H · motor determinista del chat + materializacion de archivos.

PROBLEMA REAL QUE RESUELVE (verificado, no supuesto):
  La cadena del chat era  Local (Space GGUF) -> NVIDIA -> Groq -> 503.
  Sin claves de proveedores externos y con los 6 Spaces PAUSED (402 sin saldo),
  la cadena cae en "provider: none" y el proxy responde 503. El chat queda MUERTO:
  no muestra ni una respuesta, y por tanto no puede mostrar un archivo ni un
  artefacto. Medido: POST /v1/chat/completions -> 503 Service Unavailable.

QUE HACE ESTE MODULO (100% backend, sin tocar el frontend):
  1. Es el ULTIMO eslabon de la cadena: si Local, NVIDIA y Groq fallan, responde
     el motor determinista en vez de un 503. Sigue siendo determinista y honesto:
     no simula ser un LLM, dice quien es y con que datos reales responde.
  2. Convierte la peticion en un ARCHIVO REAL cuando el usuario lo pide:
     escribe el documento en el store de artefactos (sha256 real en disco) y
     devuelve el bloque del artefacto dentro de message.content, que es
     exactamente lo que el chat pinta en la burbuja (sin tocar el frontend).

DATOS: todos los datos que devuelve son REALES y se leen de las fuentes del
sistema (registro de agentes, estado por agente, informe de raices, store de
artefactos, modos de servicio). No hay numeros inventados.
"""
from __future__ import annotations

def _safe_json(path, default):
    try:
        import json as _j
        return _j.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, OSError, UnicodeDecodeError):
        return default

def _safe_artifact_path(artifact_dir: str, name: str) -> Path:
    """Resuelve un nombre de artefacto garantizando que quede dentro de artifact_dir."""
    base = Path(artifact_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)
    raw = str(name)
    safe_name = Path(raw).name
    if not safe_name or safe_name in (".", ".."):
        raise ValueError(f"nombre inválido: {name!r}")
    # ADAPTACION DECLARADA (contrato del smoke del DAG): un nombre con separador
    # o ".." se RECHAZA con ValueError en vez de sanitizarse en silencio
    # (sanitizar convertiria un intento de traversal en una escritura legitima).
    if raw != safe_name or ".." in Path(raw).parts:
        raise ValueError(f"path traversal bloqueado: {name!r}")
    target = (base / safe_name).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"path traversal bloqueado: {name!r}")
    return target

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Deteccion de peticion de archivo ────────────────────────────────────────
# Reglas (no LLM). Un archivo se pide con verbos de creacion o con una
# extension tipica; el resto de mensajes NO generan archivo.
VERBOS_ARCHIVO = (
    "crea", "crear", "genera", "generar", "escribe", "escribir", "guarda",
    "guardar", "produce", "producir", "hazme", "prepara", "redacta", "exporta",
    "descarga", "documenta",
)
SUSTANTIVOS_ARCHIVO = (
    "informe", "report", "reporte", "documento", "fichero", "archivo", "nota",
    "acta", "acta de", "resumen", "pliego", "spec", "specs", "guia", "manual",
    "lista", "tabla", "script", "codigo", "código", "plantilla",
)
EXTENSIONES = ("md", "py", "html", "json", "txt", "csv", "yaml", "yml", "sh")

# Tipos de peticion que el motor determinista sabe responder con datos reales.
INTENCIONES = (
    ("archivo", ("archivo", "artefacto", "fichero", "documento", "informe",
                 "reporte", "report", "script", "plantilla")),
    ("agentes", ("agente", "agentes", "openclaw", "hermes", "ruflo", "rowboat",
                 "chat_a", "chat_b")),
    ("raices", ("raiz", "raíces", "raices", "root", "roots", "ruflo", "rowboat",
                "donors")),
    ("artefactos", ("artefacto", "artefactos", "archivo", "archivos")),
    ("modos", ("modo", "modos", "ruta", "rutas", "servicio", "servicios")),
    ("estado", ("estado", "salud", "health", "status", "router", "sistema",
                "resumen", "como estas", "cómo estás")),
)


def _norm(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "").strip().lower())


def pide_archivo(prompt: str) -> Optional[Dict[str, Any]]:
    """¿El mensaje pide un archivo? Devuelve {nombre, kind} o None."""
    t = _norm(prompt)
    if not t:
        return None
    ext = None
    m = re.search(r"\.(" + "|".join(EXTENSIONES) + r")\b", t)
    if m:
        ext = m.group(1)
    # C3: verbos y sustantivos tolerantes (acentos, mayusculas, variantes).
    verbo = any(v in t for v in VERBOS_ARCHIVO) or any(
        v in t for v in ("dame", "damel", "damelos", "genera", "generame", "generá",
                         "hazme", "haceme", "crea", "creame", "escribe", "escribime",
                         "muestra", "mostrame", "muéstrame", "enséñame", "enseniame",
                         "necesito", "quiero", "pásame", "pasame", "enviame", "envíame",
                         "exporta", "exportame"))
    sustantivo = any(s in t for s in SUSTANTIVOS_ARCHIVO) or any(
        n in t for n in ("archivo", "fichero", "documento", "doc", "ficha", "reporte",
                         "csv", "json", "markdown", "txt", "py", "sh", "yaml", "html"))
    if not (ext or (verbo and sustantivo) or (verbo and ext)):
        return None
    # Nombre propuesto (determinista, sin inventar rutas del usuario).
    base = re.sub(r"[^a-z0-9\-_ ]+", " ", t)
    base = " ".join(base.split())
    vacias = {"con", "del", "la", "el", "de", "y", "en", "un", "una", "los", "las",
              "para", "por", "sobre", "que", "del", "al", "a", "the", "of"}
    verbos_c3 = ("dame", "damel", "damelos", "genera", "generame", "generá", "hazme",
                 "haceme", "crea", "creame", "escribe", "escribime", "muestra",
                 "mostrame", "muéstrame", "enséñame", "enseniame", "necesito",
                 "quiero", "pásame", "pasame", "enviame", "envíame", "exporta",
                 "exportame")
    palabras = [p for p in base.split(" ")
                if p not in VERBOS_ARCHIVO and p not in SUSTANTIVOS_ARCHIVO
                and p not in verbos_c3 and p not in vacias and p != ext and len(p) > 2][:4]
    slug = "-".join(palabras) or "salida"
    kind = ext or "md"
    if kind == "yml":
        kind = "yaml"
    return {"nombre": f"{slug}.{kind}", "kind": kind}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


# ── Estado REAL del sistema ────────────────────────────────────────────────
def estado_real() -> Dict[str, Any]:
    """Snapshot real: agentes, raices, artefactos y modos. Sin numeros inventados."""
    raiz = _repo_root()
    est: Dict[str, Any] = {"agentes": [], "raices": [], "artefactos": 0, "modos": []}

    # 1. Agentes: registro central + interruptor real en disco.
    try:
        from router_llm_hf.agent_state import list_state, is_enabled
        reg = _safe_json(raiz / "router_llm_hf" / "AGENTS_REGISTRY.json", {})
        for nombre, cfg in (reg.get("agents") or {}).items():
            est["agentes"].append({
                "nombre": nombre,
                "rol": cfg.get("rol") or cfg.get("role") or "",
                "on": bool(is_enabled(nombre, reg)),
                "raiz": (cfg.get("raiz") or cfg.get("root") or ""),
            })
    except Exception as e:  # pragma: no cover - el estado NUNCA se inventa
        est["agentes_error"] = f"{type(e).__name__}: {e}"

    # 2. Raices: informe real de auto-pull (solo lo que el informe afirma).
    try:
        rep = _safe_json(raiz / "reports" / "roots_pull.json", {})
        for nombre, info in (rep.get("roots") or {}).items():
            est["raices"].append({
                "nombre": nombre,
                "existe": bool(info.get("exists")),
                "ficheros": info.get("files") or info.get("local_files") or 0,
            })
    except Exception as e:  # pragma: no cover
        est["raices_error"] = f"{type(e).__name__}: {e}"

    # 3. Modos de servicio: los que el propio router declara.
    try:
        from router_llm_hf.service_routes import SERVICE_MODES  # type: ignore
        est["modos"] = list(SERVICE_MODES)
    except Exception:
        try:
            from router_llm_hf.mode_router import VALID_MODES  # type: ignore
            est["modos"] = list(VALID_MODES)
        except Exception:
            est["modos"] = []
    return est


def _artefactos_por_nombre(artifact_dir: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        for name in sorted(os.listdir(artifact_dir)):
            path = os.path.join(artifact_dir, name)
            if not os.path.isfile(path):
                continue
            data = open(path, "rb").read()
            out.append({"name": name, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "kind": name.rsplit(".", 1)[-1] if "." in name else ""})
    except OSError:
        pass
    return out


# ── Redaccion del cuerpo del archivo ───────────────────────────────────────
def _cuerpo_documento(prompt: str, est: Dict[str, Any], destino: str, respuesta_externa: str = "") -> str:
    """Cuerpo REAL del archivo: el estado real del sistema + lo pedido."""
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lineas = [
        f"# {prompt.strip()[:120]}",
        "",
        f"- Generado por: motor determinista del router (backend, MINIMAX 2H)",
        f"- Fecha: {ahora}",
        f"- Destino: {destino}",
        "",
        "## Agentes (registro central + interruptor real)",
        "",
    ]
    for a in est.get("agentes", []):
        lineas.append(f"- `{a['nombre']}` · {'ON' if a['on'] else 'OFF'} · {a['rol'] or '—'}")
    if not est.get("agentes"):
        lineas.append("- (sin datos)")
    lineas += ["", "## Raices (informe real de auto-pull)", ""]
    for r in est.get("raices", []):
        lineas.append(f"- `{r['nombre']}` · {'presente' if r['existe'] else 'ausente'} · {r['ficheros']} ficheros")
    if not est.get("raices"):
        lineas.append("- (sin datos)")
    lineas += ["", "## Modos de servicio", ""]
    lineas.append("- " + (", ".join(est.get("modos") or []) or "(sin datos)"))
    lineas += ["", "## Artefactos en el store", ""]
    lineas.append(f"- {est.get('artefactos', 0)} ficheros")
    if respuesta_externa:
        lineas += ["", "## Respuesta del motor", "", respuesta_externa.strip()]
    lineas.append("")
    return "\n".join(lineas)


def _texto_estado(est: Dict[str, Any]) -> str:
    on = [a["nombre"] for a in est.get("agentes", []) if a["on"]]
    off = [a["nombre"] for a in est.get("agentes", []) if not a["on"]]
    return (
        f"Estado real del router: {len(est.get('agentes', []))} agentes "
        f"({len(on)} ON: {', '.join(on) or '—'} · {len(off)} OFF: {', '.join(off) or '—'}), "
        f"{len(est.get('raices', []))} raices, {len(est.get('modos', []))} modos de servicio, "
        f"{est.get('artefactos', 0)} artefactos en el store."
    )


# ── El motor ───────────────────────────────────────────────────────────────
def responde(prompt: str, *, artifact_dir: str, artifact_kinds=("md", "py", "html", "json", "txt", "csv", "yaml", "yml", "sh"),
             respuesta_externa: str = "") -> Dict[str, Any]:
    """Respuesta determinista + materializacion del archivo si lo piden.

    Devuelve: {"content", "artefactos", "tipo", "modo"}.
    El bloque del artefacto va al principio del contenido: el chat pinta la
    respuesta con el render F3, que se queda con las 5 primeras lineas no vacias.
    """
    est = estado_real()
    est["artefactos"] = len(_artefactos_por_nombre(artifact_dir))
    t = _norm(prompt)

    tipo = "general"
    for nombre, claves in INTENCIONES:
        if any(c in t for c in claves):
            tipo = nombre
            break

    cuerpo = _texto_estado(est)
    if tipo == "agentes":
        cuerpo = "Agentes del registro central (interruptor real): " + ", ".join(
            f"{a['nombre']}={'ON' if a['on'] else 'OFF'}" for a in est.get("agentes", []))
    elif tipo == "raices":
        cuerpo = "Raices: " + ", ".join(
            f"{r['nombre']}({r['ficheros']} ficheros)" for r in est.get("raices", []))
    elif tipo == "modos":
        cuerpo = "Modos de servicio: " + ", ".join(est.get("modos") or [])
    elif tipo == "artefactos":
        arts = _artefactos_por_nombre(artifact_dir)
        cuerpo = "Artefactos en el store: " + (", ".join(f"{a['name']} ({a['bytes']} B)" for a in arts) or "(ninguno)")

    # ¿Pide archivo? -> se escribe de verdad.
    pedido = pide_archivo(prompt)
    artefactos: List[Dict[str, Any]] = []
    bloque = ""
    if pedido:
        os.makedirs(artifact_dir, exist_ok=True)
        nombre = pedido["nombre"]
        # C1: la escritura usa la ruta resuelta y verificada (sin traversal).
        destino = str(_safe_artifact_path(artifact_dir, nombre))
        doc = _cuerpo_documento(prompt, est, destino, respuesta_externa)
        with open(destino, "w", encoding="utf-8") as fh:
            fh.write(doc)
        data = doc.encode("utf-8")
        sha = hashlib.sha256(data).hexdigest()
        artefactos.append({"name": nombre, "kind": pedido["kind"], "bytes": len(data),
                            "sha256": sha, "path": destino})
        vista = [ln for ln in doc.splitlines() if ln.strip()][:2]
        bloque = (
            f"ARTEFACTO CREADO · {nombre} · sha256 {sha[:16]}… · {len(data)} bytes\n"
            f"ARCHIVO REAL en {destino}\n"
            f"--- contenido ({len([l for l in doc.splitlines() if l.strip()])} lineas) ---\n"
            + "\n".join(vista)
        )
    else:
        bloque = (
            "MOTOR DETERMINISTA LOCAL (sin proveedor externo: NVIDIA/Groq sin clave, "
            "Spaces PAUSED 402) — responde con el estado real del sistema.\n"
            f"{cuerpo}"
        )

    return {
        "content": bloque,
        "artifacts": artefactos,
        "artefactos": artefactos,
        "tipo": tipo,
        "modo": "determinista",
        "estado_real": est,
    }
