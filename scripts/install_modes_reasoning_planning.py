#!/usr/bin/env python3
"""install_modes_reasoning_planning.py — construye los 2 modos que faltaban (SIN Job y SIN creditos de HF).

Los 2 modos que el detector detecta pero no tenian adapter eran `reasoning` y
`planning`. Se instalan en local y se publican por la API de HF:

  reasoning  <- IFM/Code-Reasoning (config code-thinking-hard, split train)
                instruction = enunciado, output = razonamiento + codigo
  planning   <- multimodal-reasoning-lab/Robot-Planning (solo texto; se descartan las columnas de imagen)
                instruction = objetivo, output = traza de razonamiento + accion final

Las filas se leen del `datasets-server` de HF (HTTP). El tope de filas evita
descargar los 3 TB del dataset de razonamiento.

Uso:
    python3 scripts/install_modes_reasoning_planning.py --rows-reasoning 600 --rows-planning 1500
Requiere: huggingface_hub (pip install huggingface_hub) y HF_TOKEN con escritura
en COMAND-CENTER-1/swe-code-modes y COMAND-CENTER-1/swe-code-adapters.
"""
import argparse
import json
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request

ADAPTERS_REPO = "COMAND-CENTER-1/swe-code-adapters"
MODES_REPO = "COMAND-CENTER-1/swe-code-modes"
BASE_MODEL = "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF"
IMG_RE = re.compile(r"<image_start>.*?<image_end>", re.S)


def q(s):
    return urllib.parse.quote(s, safe="")


def get(url, tries=5, timeout=90):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mcode/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print(f"  retry {a + 1}: {type(e).__name__}: {str(e)[:80]}")
            time.sleep(2 + a * 3)
    return None


def rows_paginated(dataset, config, split, total, length=100):
    """Pagina /rows del datasets-server (HTTP, sin Job)."""
    out, offset = [], 0
    while len(out) < total:
        url = ("https://datasets-server.huggingface.co/rows?dataset=%s&config=%s&split=%s&offset=%d&length=%d"
               % (q(dataset), q(config), q(split), offset, min(length, total - len(out))))
        body = get(url)
        if body is None:
            break
        try:
            batch = json.loads(body.decode("utf-8")).get("rows") or []
        except Exception:
            break
        if not batch:
            break
        out.extend(r["row"] for r in batch)
        offset += len(batch)
        time.sleep(0.35)
    return out


def split_instruction(text):
    """Corta por el primer bloque de codigo: antes = instruccion, despues = respuesta."""
    i = text.find("```")
    if i == -1:
        return None, None
    head, tail = text[:i].strip(), text[i:].strip()
    if len(head) < 40 or len(tail) < 40:
        return None, None
    return head[:4000], tail[:12000]


def build_reasoning(n):
    recs = []
    for r in rows_paginated("IFM/Code-Reasoning", "code-thinking-hard", "train", n):
        t = (r.get("text") or "").strip()
        if not t:
            continue
        ins, out = split_instruction(t)
        if ins:
            recs.append({"instruction": ins, "output": out})
    return recs


def build_planning(n):
    recs = []
    for r in rows_paginated("multimodal-reasoning-lab/Robot-Planning", "default", "train", n):
        qtext = IMG_RE.sub("", (r.get("Question") or "")).strip()
        trace = IMG_RE.sub("", (r.get("Text Reasoning Trace") or "")).strip()
        final = IMG_RE.sub("", (r.get("Final Answer") or "")).strip()
        if qtext and (trace or final):
            body = (trace + ("\n\n" + final if final else "")).strip()
            recs.append({"instruction": qtext[:4000], "output": body[:12000]})
    return recs


def adapter(mode, source, config, split, rows_n, path_rel, notas):
    return {
        "mode": mode,
        "base_model": BASE_MODEL,
        "dataset_sources": [source],
        "dataset_combined": f"{MODES_REPO}/{path_rel}",
        "dataset_rows": rows_n,
        "lora": None,
        "lora_repo": None,
        "lora_state": "skip (modo base_only)",
        "fuentes": [{"repo": source, "estado": "ok", "filas": rows_n, "split": split, "config": config}],
        "dataset": source,
        "dataset_repo": MODES_REPO,
        "dataset_path": path_rel,
        "lora_path": None,
        "adapter_type": "base_only",
        "notas": notas,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-reasoning", type=int, default=600)
    ap.add_argument("--rows-planning", type=int, default=1500)
    ap.add_argument("--out", default=".", help="carpeta donde escribir los ficheros locales")
    args = ap.parse_args()

    from huggingface_hub import HfApi

    api = HfApi(token=os.environ["HF_TOKEN"])
    out = pathlib.Path(args.out)

    plan = [
        ("reasoning", "IFM/Code-Reasoning", "code-thinking-hard", "train",
         build_reasoning(args.rows_reasoning), "reasoning/dataset/combined.jsonl",
         ["instalado en local (sin Job y sin creditos HF)",
          "instruction = enunciado, output = razonamiento + codigo"]),
        ("planning", "multimodal-reasoning-lab/Robot-Planning", "default", "train",
         build_planning(args.rows_planning), "planning/dataset/combined.jsonl",
         ["instalado en local (sin Job y sin creditos HF)",
          "subset solo texto (columnas de imagen descartadas)"]),
    ]

    for mode, source, config, split, recs, path_rel, notas in plan:
        if not recs:
            raise SystemExit(f"FALLO: 0 filas para {mode}")
        d = out / mode / "dataset"
        d.mkdir(parents=True, exist_ok=True)
        with (d / "combined.jsonl").open("w", encoding="utf-8") as fh:
            for rec in recs:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        cfg = adapter(mode, source, config, split, len(recs), path_rel, notas)
        ad = out / mode
        ad.mkdir(parents=True, exist_ok=True)
        (ad / "adapter_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{mode}: {len(recs)} filas -> {d / 'combined.jsonl'}")

    api.upload_folder(repo_id=MODES_REPO, repo_type="dataset", folder_path=str(out),
                      allow_patterns=["reasoning/dataset/combined.jsonl",
                                      "planning/dataset/combined.jsonl"],
                      commit_message="feat(modes): datasets reales de reasoning y planning")
    api.upload_folder(repo_id=ADAPTERS_REPO, repo_type="model", folder_path=str(out),
                      allow_patterns=["reasoning/adapter_config.json",
                                      "planning/adapter_config.json"],
                      commit_message="feat(adapters): modos reasoning y planning con adapter_config.json")
    print("OK: publicados (adapters + datasets)")


if __name__ == "__main__":
    main()
