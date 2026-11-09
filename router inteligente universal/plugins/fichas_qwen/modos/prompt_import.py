#!/usr/bin/env python3
"""prompt_import.py - Carga segura de prompts (Fable/Devin convertidos a JSON) en prompt_import_slot.
El prompt importado es DATO: se agrega DESPUES del system_block y nunca reemplaza reglas, gate ni topes
(los topes los aplica el codigo, no el texto). FAIL-CLOSED ante secretos o intentos de anular limites.
Uso CLI: python3 prompt_import.py <prompt.json> [modes_registry.json]"""
import copy, hashlib, json, os, re, sys

MAX_CHARS = 20000
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{16,}", r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
]
OVERRIDE_PATTERNS = [
    r"(?i)ignor[ae]\s+(todas\s+)?(las\s+)?instrucciones", r"(?i)ignore\s+(all\s+)?(previous|prior|above)",
    r"(?i)desactiv\w+\s+(los\s+)?l[ií]mites", r"(?i)sin\s+l[ií]mites?\b", r"(?i)disable\s+(the\s+)?(limits|gate)",
    r"(?i)no\s+(respetes|sigas|apliques)\s+(el\s+)?(gate|l[ií]mites|tope)", r"(?i)reveal\s+(the\s+)?system\s+prompt",
    r"(?i)muestra\s+(tu\s+)?prompt\s+de\s+sistema", r"(?i)bypass\w*",
]


class PromptImportError(Exception):
    pass


def canonical_hash(sections) -> str:
    return hashlib.sha256(json.dumps(sections, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_prompt(pi: dict, reg: dict) -> list:
    e = []
    for k in ("prompt_import_version", "prompt_id", "mode_id", "position", "sections"):
        if k not in pi:
            e.append(f"falta '{k}'")
    if e:
        return e
    if pi["prompt_import_version"] != "1.0.0":
        e.append("prompt_import_version debe ser 1.0.0")
    if pi["mode_id"] not in {m["id"] for m in reg["modes"]}:
        e.append(f"mode_id '{pi['mode_id']}' no existe en el registro")
    if pi["position"] != "after_mode_block":
        e.append("position debe ser after_mode_block")
    secs = pi["sections"]
    if not isinstance(secs, list) or not secs:
        return e + ["sections vacio"]
    total = 0
    for i, s in enumerate(secs):
        if not isinstance(s, dict) or not str(s.get("title", "")).strip():
            e.append(f"sections[{i}] sin title"); continue
        lines = s.get("lines")
        if not isinstance(lines, list) or not lines or not all(isinstance(x, str) and x.strip() for x in lines):
            e.append(f"sections[{i}].lines debe ser lista de textos no vacios"); continue
        for ln in [s["title"]] + lines:
            total += len(ln)
            for p in SECRET_PATTERNS:
                if re.search(p, ln):
                    e.append(f"sections[{i}]: posible secreto en texto (patron {p[:18]}...)")
            for p in OVERRIDE_PATTERNS:
                if re.search(p, ln):
                    e.append(f"sections[{i}]: intento de anular reglas/limites ({p[:28]}...)")
    if total > MAX_CHARS:
        e.append(f"prompt excede {MAX_CHARS} caracteres ({total})")
    if "sha256" in pi and pi["sha256"] != canonical_hash(secs):
        e.append("sha256 no coincide con las secciones (archivo alterado)")
    return e


def load_prompt_import(path: str, reg: dict) -> dict:
    with open(path, encoding="utf-8") as f:
        pi = json.load(f)
    errs = validate_prompt(pi, reg)
    if errs:
        raise PromptImportError("; ".join(errs))
    return pi


def render_import_block(pi: dict) -> str:
    L = [f"## PROMPT IMPORTADO ({pi['prompt_id']}) - complementa las reglas del modo; no las reemplaza"]
    for s in pi["sections"]:
        L.append(f"### {s['title']}")
        L += [f"- {x}" for x in s["lines"]]
    return "\n".join(L)


def apply_prompt_import(reg: dict, ficha: dict, base_dir: str) -> dict:
    """Devuelve una COPIA de la ficha con el prompt agregado tras system_block. Slot null => ficha intacta."""
    slot = ficha.get("prompt_import_slot")
    if slot is None:
        return ficha
    pi = load_prompt_import(os.path.join(base_dir, slot), reg)
    if pi["mode_id"] != ficha["mode_id"]:
        raise PromptImportError(f"el prompt es del modo {pi['mode_id']} pero la ficha es {ficha['mode_id']}")
    out = copy.deepcopy(ficha)
    out["system_block"] = ficha["system_block"] + "\n\n" + render_import_block(pi)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FAIL: falta ruta del prompt"); sys.exit(1)
    reg = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "modes_registry.json", encoding="utf-8"))
    try:
        pi = load_prompt_import(sys.argv[1], reg)
        print(f"VEREDICTO: PASS ({pi['prompt_id']} -> {pi['mode_id']}, sha256 {canonical_hash(pi['sections'])[:12]}...)")
    except PromptImportError as ex:
        print("VEREDICTO: FAIL"); [print(" -", x) for x in str(ex).split("; ")]; sys.exit(1)
