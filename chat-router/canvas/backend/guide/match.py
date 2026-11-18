"""match.py · N4-C · GUÍA VIVA — MOTOR DE MIRROR Y PARCHE QUIRÚRGICO.

Compara un bloque de código contra el EJEMPLO de la guía (catálogo
`guide_actions.json`) y decide si la acción YA ESTÁ DEFINIDA o es NECESARIA.

Salida (determinista, sin LLM):
    {
      "veredicto": "DEFINIDA | NECESARIA | PARCIAL | NO_APLICA",
      "lineas": {"inicio": int, "fin": int, "rangos": [[a, b], ...]},
      "lineas_originales": [...],
      "lineas_nuevas": [...],
      "parche": {"operaciones": [...], "diff_unificado": "..."}
    }

GARANTÍA CENTRAL: el parche NUNCA reescribe el bloque entero. Sólo se tocan las
líneas declaradas en `lineas`; `verify_surgical()` lo comprueba con un diff de
líneas y devuelve `ok=False` si se ha tocado algo de más.

Uso:
    from match import match_action, apply_match, verify_surgical
    r = match_action("añadir reintento con backoff", codigo_antes)
    nuevo = apply_match(codigo_antes, r)
    verify_surgical(codigo_antes, nuevo, r)
"""
from __future__ import annotations

import difflib
import json
import os
import re
from typing import Any

SCHEMA = "yaiwes.guide.match.v1"
CATALOG_FILENAME = "guide_actions.json"

VERDICTS = ("DEFINIDA", "NECESARIA", "PARCIAL", "NO_APLICA")

_STOPWORDS = {
    "the", "and", "for", "from", "with", "into", "that", "this", "add", "new",
    "una", "uno", "unos", "unas", "para", "con", "sin", "los", "las", "del",
    "que", "por", "como", "más", "más", "de", "la", "el", "en", "un", "a", "y",
    "o", "se", "su", "al", "por", "al",
}

_KEYWORDS = {
    "def", "return", "if", "else", "elif", "for", "while", "import", "from",
    "class", "try", "except", "finally", "with", "as", "lambda", "pass",
    "break", "continue", "raise", "yield", "assert", "global", "nonlocal",
    "async", "await", "in", "not", "and", "or", "is", "none", "true", "false",
    "function", "const", "let", "var", "new", "throw", "catch",
}


def _default_catalog_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), CATALOG_FILENAME)


def load_catalog(path: str | None = None) -> dict:
    """Carga el catálogo vivo de acciones. FAIL_CLOSED si no existe o no valida."""
    target = path or os.getenv("GUIDE_ACTIONS_CATALOG") or _default_catalog_path()
    with open(target, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema") != "yaiwes.guide.actions.v1":
        raise ValueError("CATALOG_SCHEMA_INVALID")
    if not isinstance(data.get("acciones"), list) or not data["acciones"]:
        raise ValueError("CATALOG_EMPTY")
    return data


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ_][A-Za-zÁÉÍÓÚÑáéíóúñ0-9_]{2,}", text or "")
    out = []
    for tok in raw:
        low = tok.lower()
        if low in _STOPWORDS:
            continue
        out.append(low)
    return out


def _identifiers(text: str) -> set[str]:
    ids = set()
    for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text or ""):
        if tok.lower() in _KEYWORDS:
            continue
        ids.add(tok)
    return ids


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return round(len(a & b) / len(a | b), 4)


def select_action(action_text: str, catalog: dict | None = None) -> tuple[dict | None, float]:
    """Localiza la entrada del catálogo que mejor corresponde a la acción escrita."""
    cat = catalog if catalog is not None else load_catalog()
    want = set(_tokens(action_text))
    best: tuple[dict | None, float] = (None, 0.0)
    for entry in cat["acciones"]:
        pool = [entry.get("titulo", "")] + list(entry.get("alias", [])) + list(entry.get("verbos", []))
        have = set(_tokens(" ".join(pool)))
        if not have or not want:
            continue
        overlap = len(want & have) / len(want | have)
        if overlap > best[1]:
            best = (entry, round(overlap, 4))
    return best


def _as_lines(code: str | list[str]) -> list[str]:
    if isinstance(code, list):
        return list(code)
    return (code or "").splitlines()


def _find_anchor(lines: list[str], patron: str) -> tuple[int, re.Match | None]:
    regex = re.compile(patron)
    for idx, line in enumerate(lines):
        m = regex.search(line)
        if m:
            return idx, m
    return -1, None


def _parse_signature(lines: list[str], def_idx: int) -> tuple[str, list[str]]:
    """Devuelve (nombre_funcion, lista_de_parametros) leyendo la línea de def."""
    line = lines[def_idx]
    m = re.search(r"(?:async\s+def|def|function)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)", line)
    if not m:
        m2 = re.search(r"(?:async\s+def|def|function)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        name = m2.group(1) if m2 else ""
        return name, []
    name = m.group(1)
    raw_params = m.group(2).strip()
    params: list[str] = []
    if raw_params:
        for part in raw_params.split(","):
            piece = part.split("=")[0].split(":")[0].strip()
            if piece and piece not in ("self", "cls"):
                params.append(piece)
    return name, params


def _body_extent(lines: list[str], def_idx: int) -> tuple[int, int]:
    """Devuelve (inicio_cuerpo, fin_cuerpo) EXCLUSIVO, en índices 0-based."""
    indent = len(lines[def_idx]) - len(lines[def_idx].lstrip())
    start = def_idx + 1
    end = len(lines)
    for i in range(start, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        cur = len(line) - len(line.lstrip())
        if cur <= indent:
            end = i
            break
    return start, end


def _substitute(template_lines: list[str], mapping: dict[str, str]) -> list[str]:
    out = []
    for line in template_lines:
        new = line
        for key, value in mapping.items():
            new = new.replace("{" + key + "}", value)
        out.append(new)
    return out


def _build_patch(entry: dict, lines: list[str]) -> dict:
    """Construye las operaciones de parche quirúrgico para la entrada del catálogo."""
    ancla = entry.get("ancla", {}) or {}
    patron = ancla.get("patron", "")
    modo = ancla.get("modo", "")
    patch = entry.get("patch_esperado", {}) or {}
    template = list(patch.get("lineas", []) or [])
    max_lines = int(patch.get("lineas_max", 40) or 40)

    anchor_idx, anchor_match = _find_anchor(lines, patron)
    mapping: dict[str, str] = {}
    func_name = ""
    params: list[str] = []

    if anchor_match is not None and "funcion" in (anchor_match.groupdict() or {}):
        func_name = anchor_match.group("funcion") or ""
    if anchor_idx >= 0:
        fn, ps = _parse_signature(lines, anchor_idx)
        func_name = func_name or fn
        params = ps
    if not func_name and lines:
        fn, ps = _parse_signature(lines, 0) if lines else ("", [])
        func_name, params = fn, ps

    mapping["funcion"] = func_name or "accion"
    mapping["parametro"] = params[0] if params else "entrada"
    mapping["parametros"] = ", ".join(params) if params else "entrada"
    mapping["modulo"] = re.sub(r"[^A-Za-z0-9_]", "_", (func_name or "accion")).lower()

    ops: list[dict] = []

    if modo == "al_final":
        body = _substitute(template, mapping)
        ops.append({"op": "insert_at_end", "lines": body})
    elif modo == "reemplazar_linea":
        if anchor_idx < 0:
            return {"ok": False, "motivo": "ANCLA_NO_ENCONTRADA", "ops": []}
        body = _substitute(template, mapping)
        ops.append({
            "op": "replace",
            "line_start": anchor_idx + 1,
            "line_end": anchor_idx + 1,
            "lines": body,
        })
    elif modo == "insertar_despues_linea":
        if anchor_idx < 0:
            return {"ok": False, "motivo": "ANCLA_NO_ENCONTRADA", "ops": []}
        body = _substitute(template, mapping)
        ops.append({"op": "insert_after", "line": anchor_idx + 1, "lines": body})
    elif modo == "insertar_en_cuerpo":
        if anchor_idx < 0:
            return {"ok": False, "motivo": "ANCLA_NO_ENCONTRADA", "ops": []}
        body_start, _body_end = _body_extent(lines, anchor_idx)
        insert_at = body_start
        # Si la función abre con docstring, la validación va DESPUÉS del docstring.
        if insert_at < len(lines) and lines[insert_at].lstrip().startswith(('"""', "'''")):
            quote = lines[insert_at].lstrip()[:3]
            if lines[insert_at].strip().count(quote) >= 2:
                insert_at += 1
            else:
                for j in range(insert_at + 1, len(lines)):
                    if quote in lines[j]:
                        insert_at = j + 1
                        break
        body = _substitute(template, mapping)
        ops.append({"op": "insert_after", "line": insert_at, "lines": body})
    elif modo == "extraccion":
        if anchor_idx < 0:
            return {"ok": False, "motivo": "ANCLA_NO_ENCONTRADA", "ops": []}
        body_start, body_end = _body_extent(lines, anchor_idx)
        body_lines = lines[body_start:body_end]
        if not body_lines:
            return {"ok": False, "motivo": "CUERPO_VACIO", "ops": []}
        last = body_lines[-1].strip()
        m_ret = re.match(r"^return\s+(.+)$", last)
        if not m_ret:
            # Sin `return` final NO se puede delegar sin cambiar la semántica.
            return {"ok": False, "motivo": "EXTRACCION_NO_EQUIVALENTE", "ops": []}
        new_name = f"{func_name}_impl"
        args = ", ".join(params) if params else ""
        delegation = f"    return {new_name}({args})"
        extracted = ["", "", f"def {new_name}({', '.join(params) if params else ''}):"] + list(body_lines)
        ops.append({
            "op": "replace",
            "line_start": body_start + 1,
            "line_end": body_end,
            "lines": [delegation],
        })
        ops.append({"op": "insert_at_end", "lines": extracted})
    else:
        return {"ok": False, "motivo": "MODO_DE_ANCLA_DESCONOCIDO", "ops": []}

    total = sum(len(op.get("lines", [])) for op in ops)
    if total > max_lines:
        return {"ok": False, "motivo": "PATCH_SUPERA_LINEAS_MAX", "ops": []}
    return {"ok": True, "motivo": "OK", "ops": ops, "mapping": mapping}


def _apply_ops(lines: list[str], ops: list[dict]) -> list[str]:
    """Aplica las operaciones de derecha a izquierda para no invalidar índices."""
    out = list(lines)
    for op in sorted(ops, key=lambda o: -(o.get("line_start") or o.get("line") or len(out))):
        kind = op["op"]
        if kind == "insert_at_end":
            out.extend(op["lines"])
        elif kind == "insert_after":
            pos = max(0, min(op["line"], len(out)))
            out[pos:pos] = list(op["lines"])
        elif kind == "insert_before":
            pos = max(0, min(op["line"] - 1, len(out)))
            out[pos:pos] = list(op["lines"])
        elif kind == "replace":
            a = max(0, op["line_start"] - 1)
            b = min(len(out), op["line_end"])
            out[a:b] = list(op["lines"])
    return out


def _touched_ranges(ops: list[dict], n_lines: int) -> list[list[int]]:
    ranges: list[list[int]] = []
    for op in ops:
        if op["op"] == "replace":
            ranges.append([op["line_start"], op["line_end"]])
        elif op["op"] == "insert_after":
            ranges.append([op["line"], op["line"]])
        elif op["op"] == "insert_before":
            ranges.append([op["line"], op["line"]])
        elif op["op"] == "insert_at_end":
            ranges.append([max(1, n_lines), max(1, n_lines)])
    return sorted(ranges)


def match_action(
    action_text: str,
    code: str | list[str],
    *,
    catalog: dict | None = None,
    entry: dict | None = None,
    fichero: str | None = None,
) -> dict:
    """MIRROR de la acción contra el ejemplo de la guía + parche quirúrgico."""
    cat = catalog if catalog is not None else load_catalog()
    if entry is None:
        entry, score = select_action(action_text, cat)
    else:
        score = 1.0
    lines = _as_lines(code)
    code_text = "\n".join(lines)

    base = {
        "schema": SCHEMA,
        "accion": action_text,
        "fichero": fichero,
        "veredicto": "NO_APLICA",
        "motivo": "",
        "estado": "OK",
        "lineas": None,
        "lineas_originales": [],
        "lineas_nuevas": [],
        "parche": None,
    }

    if entry is None:
        base["motivo"] = "NO_CATALOG_MATCH"
        base["estado"] = "NEEDS_REVIEW"
        base["coincidencia_guia"] = 0.0
        return base

    base["accion_guia"] = {
        "action_id": entry.get("action_id"),
        "titulo": entry.get("titulo"),
        "tipo": entry.get("tipo"),
    }
    base["coincidencia_guia"] = score
    ejemplo_lines = _as_lines(entry.get("ejemplo", []))
    base["coincidencia_ejemplo"] = _jaccard(_identifiers(code_text), _identifiers("\n".join(ejemplo_lines)))

    # 1 · Aplicabilidad
    aplicabilidad = entry.get("aplicabilidad", []) or []
    if aplicabilidad and not any(re.search(rx, code_text, re.M) for rx in aplicabilidad):
        base["veredicto"] = "NO_APLICA"
        base["motivo"] = "NO_APLICA_EN_BLOQUE"
        return base

    # 2 · Señales
    senales = entry.get("senales_requeridas", []) or []
    encontradas: list[str] = []
    faltantes: list[str] = []
    for rx in senales:
        if re.search(rx, code_text, re.M):
            encontradas.append(rx)
        else:
            faltantes.append(rx)
    base["senales"] = {"encontradas": encontradas, "faltantes": faltantes}

    if senales and not faltantes:
        base["veredicto"] = "DEFINIDA"
        base["motivo"] = "TODAS_LAS_SENALES_PRESENTES"
        return base

    veredicto = "PARCIAL" if encontradas else "NECESARIA"

    # 3 · Parche quirúrgico
    built = _build_patch(entry, lines)
    if not built.get("ok"):
        base["veredicto"] = veredicto
        base["motivo"] = built.get("motivo", "PATCH_NO_CONSTRUIDO")
        base["estado"] = "NEEDS_REVIEW"
        return base

    ops = built["ops"]
    new_lines = _apply_ops(lines, ops)
    ranges = _touched_ranges(ops, len(lines))
    inicio = min(r[0] for r in ranges)
    fin = max(r[1] for r in ranges)
    originales = lines[inicio - 1:fin]
    nuevas = new_lines[:]
    # Recorte de la ventana equivalente tras el parche.
    ventana = _extract_window(new_lines, ops, len(lines))

    diff = "\n".join(
        difflib.unified_diff(
            lines, new_lines,
            fromfile="antes", tofile="despues", lineterm="", n=0,
        )
    )

    base["veredicto"] = veredicto
    base["motivo"] = "ALGUNAS_SENALES_PRESENTES" if encontradas else "NINGUNA_SENAL_PRESENTE"
    base["lineas"] = {"inicio": inicio, "fin": fin, "rangos": ranges}
    base["lineas_originales"] = originales
    base["lineas_nuevas"] = ventana
    base["parche"] = {"operaciones": ops, "diff_unificado": diff}
    base["estado"] = "OK"
    return base


def _extract_window(new_lines: list[str], ops: list[dict], n_old: int) -> list[str]:
    """Devuelve las líneas nuevas que corresponden a la ventana tocada."""
    out: list[str] = []
    for op in ops:
        if op["op"] == "replace":
            out.extend(op["lines"])
        elif op["op"] in ("insert_after", "insert_before", "insert_at_end"):
            out.extend(op["lines"])
    return out


def apply_match(code: str | list[str], result: dict) -> str:
    """Aplica el parche de `match_action()` y devuelve el código nuevo."""
    lines = _as_lines(code)
    ops = ((result.get("parche") or {}).get("operaciones")) or []
    if not ops:
        return "\n".join(lines)
    return "\n".join(_apply_ops(lines, ops))


def verify_surgical(original: str | list[str], patched: str | list[str], result: dict) -> dict:
    """Comprueba (determinista) que el parche SÓLO cambia las líneas declaradas."""
    old = _as_lines(original)
    new = _as_lines(patched)
    declared = (result.get("lineas") or {})
    ranges = declared.get("rangos") or []
    lo = declared.get("inicio")
    hi = declared.get("fin")
    detalles: list[str] = []

    # 1 · Recomputar el parche desde el original debe dar el mismo resultado.
    ops = ((result.get("parche") or {}).get("operaciones")) or []
    esperado = _apply_ops(old, ops) if ops else old
    recomputa_ok = esperado == new

    # 2 · Diff de líneas: todo cambio debe caer en las líneas declaradas.
    fuera: list[int] = []
    cambiadas: list[int] = []
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            # j1 = nº de líneas ORIGINALES que anteceden a la inserción ⇒
            # la inserción se produce justo después de la línea original j1.
            punto = j1
            if not _dentro(punto, ranges, lo, hi, borde=True):
                fuera.append(punto)
            else:
                cambiadas.append(punto)
        else:
            for k in range(i1 + 1, i2 + 1):
                if not _dentro(k, ranges, lo, hi, borde=False):
                    fuera.append(k)
                else:
                    cambiadas.append(k)

    ok = recomputa_ok and not fuera
    if not recomputa_ok:
        detalles.append("PATCH_NO_REPRODUCIBLE")
    if fuera:
        detalles.append("LINEAS_FUERA_DE_RANGO")
    return {
        "ok": ok,
        "recomputa_ok": recomputa_ok,
        "lineas_modificadas": sorted(set(cambiadas)),
        "lineas_fuera_de_rango": sorted(set(fuera)),
        "detalle": ",".join(detalles) if detalles else "SOLO_LINEAS_DECLARADAS",
    }


def _dentro(linea: int, ranges: list, lo: Any, hi: Any, *, borde: bool) -> bool:
    for a, b in ranges:
        if a <= linea <= b:
            return True
        if borde and (linea == a - 1 or linea == b):
            return True
    if lo is not None and hi is not None:
        if borde:
            return (lo - 1) <= linea <= hi
        return lo <= linea <= hi
    return False


__all__ = [
    "SCHEMA",
    "VERDICTS",
    "load_catalog",
    "select_action",
    "match_action",
    "apply_match",
    "verify_surgical",
]
