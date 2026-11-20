"""Motor de audio explicativo (PARTE 4) — sin LLM en la conversion.

Fichero: audio_engine.py
Flujo: Diagrama (JSON/SVG) -> Resumen (LLM o plantilla, <=150 palabras)
       -> Traduccion (opcional) -> TTS (edge-tts) -> .mp3

REGLAS (INPUT BLOCK N4-A):
  - "El LLM solo produce el resumen textual (max. 150 palabras). No toca el audio."
  - Traduccion: deep-translator (Google/DeepL) si el idioma destino != espanol.
  - TTS: edge-tts. Fallback: pyttsx3 (offline, calidad 1.5/5, DEJA EL WARNING).
  - Cache por hash sha256(texto+voz).
  - Sin secretos: edge-tts no requiere API key y aqui no hay ninguna.

GAPS implementados (degradacion explicita, nunca fallo silencioso):
  - edge-tts requiere red -> fallback pyttsx3.
  - deep-translator depende de Google -> no traducir, devolver texto original.
  - Resumen inventado por plantilla -> marcar warning.
  - Sin secretos -> edge-tts no requiere API key.

NOTA DE CORRECCION (bug real del codigo de referencia): pyttsx3 escribe WAV,
no MP3. El motor guarda el WAV con su extension real (`audio_<hash>.wav`) y
devuelve esa ruta; edge-tts si genera MP3 real (`audio_<hash>.mp3`).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path(os.environ.get("CANVAS_AUDIO_DIR") or "/tmp/canvas_audio")
MAX_WORDS = 150
DEFAULT_VOICE = "es-ES-AlvaroNeural"
DEFAULT_TARGET_LANG: Optional[str] = None

_AUDIO_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


def _ensure_cache_dir() -> Path:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return CACHE_DIR


def _word_count(text: str) -> int:
    return len([w for w in str(text).split() if w])


def _truncate_words(text: str, max_words: int) -> Dict[str, Any]:
    """Recorta a max_words palabras sin partir una palabra."""
    words = [w for w in str(text).split() if w]
    if len(words) <= max_words:
        return {"text": " ".join(words), "truncated": False}
    return {"text": " ".join(words[:max_words]), "truncated": True}


def build_summary(diagram_json: Any, max_words: int = MAX_WORDS) -> Dict[str, Any]:
    """Resumen determinista del diagrama (max. 150 palabras).

    1) Si `diagram_json["summary"]` es str -> se usa (fuente "llm").
    2) Si no -> plantilla determinista:
         "El diagrama contiene N elementos."   (lista `elements`)
         "El grafo tiene N nodos."              (lista `nodes`)
         "Con N conexiones."                    (lista `edges`/`connections`/`links`)
         "Diagrama sin descripcion."            (sin datos)
       Plantilla -> warning explicito (resumen inventado).
    """
    warning: Optional[str] = None
    source = "template"
    text = ""

    if isinstance(diagram_json, str):
        text = diagram_json
        source = "llm"
    elif isinstance(diagram_json, dict):
        raw_summary = diagram_json.get("summary")
        if isinstance(raw_summary, str) and raw_summary.strip():
            text = raw_summary
            source = "llm"
        else:
            elements = diagram_json.get("elements")
            nodes = diagram_json.get("nodes")
            edges = None
            for key in ("edges", "connections", "links"):
                if isinstance(diagram_json.get(key), list):
                    edges = diagram_json[key]
                    break
            if isinstance(elements, list):
                text = f"El diagrama contiene {len(elements)} elementos."
            elif isinstance(nodes, list):
                text = f"El grafo tiene {len(nodes)} nodos."
            elif isinstance(edges, list):
                text = f"Con {len(edges)} conexiones."
            else:
                text = "Diagrama sin descripcion."
            warning = "resumen generado por plantilla (sin 'summary' del LLM)"
    else:
        text = "Diagrama sin descripcion."
        warning = "resumen generado por plantilla (payload no recognized)"

    truncated = _truncate_words(text, max_words)
    if truncated["truncated"]:
        warning = ((warning + "; ") if warning else "") + (
            f"resumen truncado a {max_words} palabras"
        )
    return {
        "text": truncated["text"],
        "words": _word_count(truncated["text"]),
        "max_words": max_words,
        "source": source,
        "warning": warning,
    }


def translate(text: str, target_lang: Optional[str] = None) -> Dict[str, Any]:
    """Traduce con deep-translator (Google/DeepL) solo si el destino != espanol.

    Sin deep-translator o sin red -> NO se traduce y se devuelve el texto
    original (gap explicito del INPUT BLOCK).
    """
    original = "" if text is None else str(text)
    lang = (target_lang or "").strip()
    if not lang or lang.lower().split("-")[0] == "es":
        return {
            "ok": True,
            "text": original,
            "lang": lang or "es",
            "translated": False,
            "engine": None,
            "error": None,
        }
    try:
        from deep_translator import GoogleTranslator  # type: ignore
    except Exception as exc:
        return {
            "ok": False,
            "text": original,
            "lang": lang,
            "translated": False,
            "engine": None,
            "error": f"deep-translator no instalado ({type(exc).__name__})",
        }
    try:
        translated = GoogleTranslator(source="auto", target=lang).translate(original)
    except Exception as exc:
        return {
            "ok": False,
            "text": original,
            "lang": lang,
            "translated": False,
            "engine": "deep-translator",
            "error": f"traduccion fallida ({type(exc).__name__}): {exc}",
        }
    if not translated:
        return {
            "ok": False,
            "text": original,
            "lang": lang,
            "translated": False,
            "engine": "deep-translator",
            "error": "traduccion vacia: se devuelve el texto original",
        }
    return {
        "ok": True,
        "text": str(translated),
        "lang": lang,
        "translated": True,
        "engine": "deep-translator",
        "error": None,
    }


def _audio_hash(text: str, voice: str) -> str:
    return hashlib.sha256(f"{text}{voice}".encode("utf-8")).hexdigest()[:12]


def _pyttsx3_save(text: str, wav_path: Path) -> Dict[str, Any]:
    """Fallback offline con pyttsx3 (escribe WAV real)."""
    try:
        import pyttsx3  # type: ignore
    except Exception as exc:
        return {
            "ok": False,
            "error": f"pyttsx3 no instalado ({type(exc).__name__})",
            "path": None,
        }
    try:
        engine = pyttsx3.init()
        engine.save_to_file(text, str(wav_path))
        engine.runAndWait()
    except Exception as exc:
        return {
            "ok": False,
            "error": f"pyttsx3 fallo ({type(exc).__name__}): {exc}",
            "path": None,
        }
    if not wav_path.exists():
        return {
            "ok": False,
            "error": "pyttsx3 no genero el fichero de audio",
            "path": None,
        }
    return {"ok": True, "error": None, "path": str(wav_path)}


async def tts(text: str, voice: str = DEFAULT_VOICE) -> Dict[str, Any]:
    """TTS con edge-tts (async) y cache por hash sha256(texto+voz)[:12].

    Devuelve SIEMPRE dict: {"ok","path","cached","engine","voice","hash","warning","error"}
    """
    content = "" if text is None else str(text)
    if not content.strip():
        return {
            "ok": False,
            "path": None,
            "cached": False,
            "engine": None,
            "voice": voice,
            "hash": None,
            "warning": None,
            "error": "texto vacio: no hay nada que sintetizar",
        }
    cache_dir = _ensure_cache_dir()
    digest = _audio_hash(content, voice)
    mp3_path = cache_dir / f"audio_{digest}.mp3"

    if mp3_path.exists() and mp3_path.stat().st_size > 0:
        return {
            "ok": True,
            "path": str(mp3_path),
            "cached": True,
            "engine": "edge-tts",
            "voice": voice,
            "hash": digest,
            "warning": None,
            "error": None,
        }

    warning: Optional[str] = None
    try:
        import edge_tts  # type: ignore
    except Exception as exc:
        edge_tts = None  # type: ignore
        warning = f"edge-tts no instalado ({type(exc).__name__}): se usa fallback offline pyttsx3"

    if edge_tts is not None:
        try:
            communicator = edge_tts.Communicate(content, voice)
            await communicator.save(str(mp3_path))
            if mp3_path.exists() and mp3_path.stat().st_size > 0:
                return {
                    "ok": True,
                    "path": str(mp3_path),
                    "cached": False,
                    "engine": "edge-tts",
                    "voice": voice,
                    "hash": digest,
                    "warning": warning,
                    "error": None,
                }
            warning = (warning + "; ") if warning else ""
            warning += "edge-tts no genero el mp3"
        except Exception as exc:
            warning = (warning + "; ") if warning else ""
            warning += f"edge-tts fallo ({type(exc).__name__}: {exc})"

    # Fallback offline: pyttsx3 (WAV real, calidad 1.5/5, warning obligatorio)
    wav_path = cache_dir / f"audio_{digest}.wav"
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _pyttsx3_save, content, wav_path)
    if result.get("ok"):
        return {
            "ok": True,
            "path": result["path"],
            "cached": False,
            "engine": "pyttsx3",
            "voice": voice,
            "hash": digest,
            "warning": (warning + "; ") if warning else "",
            "error": None,
        }
    return {
        "ok": False,
        "path": None,
        "cached": False,
        "engine": None,
        "voice": voice,
        "hash": digest,
        "warning": warning,
        "error": result.get("error"),
    }


async def explain(
    diagram_json: Any,
    target_lang: Optional[str] = None,
    voice: str = DEFAULT_VOICE,
) -> Dict[str, Any]:
    """Pipeline completo: diagrama -> resumen -> traduccion -> TTS -> mp3.

    El LLM solo aporta el texto del resumen; la conversion a audio no usa
    ningun token del LLM.
    """
    summary = build_summary(diagram_json)
    text = summary["text"]

    warnings: list = []
    if summary.get("warning"):
        warnings.append(summary["warning"])

    translation = translate(text, target_lang)
    if not translation.get("ok"):
        warnings.append(f"traduccion no aplicada: {translation.get('error')}")
    speak_text = translation.get("text") or text

    tts_result = await tts(speak_text, voice)
    if tts_result.get("warning"):
        warnings.append(tts_result["warning"])

    error = None
    if not tts_result.get("ok"):
        error = tts_result.get("error") or "no se pudo generar el audio"
    elif not translation.get("ok"):
        error = None  # gap de traduccion: no bloquea el audio

    return {
        "ok": bool(tts_result.get("ok")),
        "summary": summary["text"],
        "summary_words": summary["words"],
        "summary_source": summary["source"],
        "lang": translation.get("lang"),
        "translated": bool(translation.get("translated")),
        "audio_path": tts_result.get("path"),
        "cached": bool(tts_result.get("cached", False)),
        "engine": tts_result.get("engine"),
        "voice": voice,
        "hash": tts_result.get("hash"),
        "warning": "; ".join(warnings) if warnings else None,
        "error": error,
    }


def resolve_audio(audio_id: str) -> Optional[Path]:
    """Resuelve `audio_id` a un fichero real dentro de la cache (sin traversal)."""
    if not isinstance(audio_id, str) or not _AUDIO_ID_RE.match(audio_id):
        return None
    cache_dir = _ensure_cache_dir().resolve()
    candidates = [audio_id]
    if not audio_id.startswith("audio_"):
        candidates.insert(0, f"audio_{audio_id}")
    for candidate in candidates:
        for suffix in ("", ".mp3", ".wav"):
            path = (cache_dir / f"{candidate}{suffix}").resolve()
            try:
                path.relative_to(cache_dir)
            except ValueError:
                continue
            if path.exists() and path.is_file():
                return path
    return None


def audio_id_from_path(path: str) -> Optional[str]:
    """Extrae el audio_id (hash) de una ruta de la cache."""
    if not path:
        return None
    name = Path(path).stem
    if name.startswith("audio_"):
        return name
    return name or None


def cache_info() -> Dict[str, Any]:
    """Estado real de la cache de audio (diagnostico)."""
    cache_dir = _ensure_cache_dir()
    files: list = []
    try:
        for entry in sorted(cache_dir.iterdir()):
            if entry.is_file():
                files.append(
                    {
                        "name": entry.name,
                        "bytes": entry.stat().st_size,
                        "modified": entry.stat().st_mtime,
                    }
                )
    except Exception as exc:
        return {"dir": str(cache_dir), "error": f"{type(exc).__name__}: {exc}", "files": []}
    return {
        "dir": str(cache_dir),
        "files": files,
        "count": len(files),
        "timestamp": time.time(),
    }
