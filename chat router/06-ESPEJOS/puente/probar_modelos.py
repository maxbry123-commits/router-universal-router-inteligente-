"""Prueba modelos reales antes de trabajar (espejos, sentinelas y referencia para el Router).

Orden del Director 2026-09-27: prioridad Kimi K3 > GLM-5 > DeepSeek V4 Flash > cualquier modelo de NVIDIA que responda.
Primero pregunta el catálogo vivo de NVIDIA, luego prueba cada candidato con cada clave NVIDIA_API_KEY_1..4 y
solo usa los que contestan. Cerebras ELIMINADO (pide pago). Groq como respaldo si hay GROQ_API_KEY.
"""
import os

import requests
import yaml

PREFS = ["kimi-k3", "glm-5", "deepseek-v4", "kimi-k2", "qwen3-coder", "qwen3-235b", "gpt-oss-120b", "llama-4-maverick", "nemotron", "llama-3.3-70b"]


def catalog(url, key):
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=20)
        return [m["id"] for m in r.json().get("data", [])]
    except Exception:
        return []


def works(base, model, key):
    try:
        r = requests.post(base + "/chat/completions", headers={"Authorization": f"Bearer {key}"}, timeout=60,
                          json={"model": model, "messages": [{"role": "user", "content": "Responde solo: OK"}], "max_tokens": 8})
        return r.status_code == 200, r.status_code
    except Exception as e:
        return False, type(e).__name__


def ranked(ids):
    out = []
    for p in PREFS:
        out += sorted([i for i in ids if p in i.lower() and i not in out], reverse=True)
    return out


def main(alias="espejo", master="sk-espejo", out_path="/tmp/litellm.yaml"):
    keys = [(n, os.environ.get(n, "")) for n in ["NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4"] if os.environ.get(n)]
    nv = "https://integrate.api.nvidia.com/v1"
    cands = ranked(catalog(nv + "/models", keys[0][1] if keys else ""))[:10]
    ok, report = [], []
    for m in cands:
        for kn, kv in keys:
            good, code = works(nv, m, kv)
            report.append(f"{m}@{kn}={code}")
            if good:
                ok.append({"model_name": alias, "litellm_params": {"model": f"nvidia_nim/{m}", "api_key": f"os.environ/{kn}"}})
                break
        if len(ok) >= 3:
            break
    gq = os.environ.get("GROQ_API_KEY", "")
    if gq and len(ok) < 3:
        for m in ranked(catalog("https://api.groq.com/openai/v1/models", gq))[:2]:
            good, code = works("https://api.groq.com/openai/v1", m, gq)
            report.append(f"groq:{m}={code}")
            if good:
                ok.append({"model_name": alias, "litellm_params": {"model": f"groq/{m}", "api_key": "os.environ/GROQ_API_KEY"}})
    print("::notice::PRUEBAS " + " ".join(report)[:900])
    print("::notice::USABLES " + ", ".join(x["litellm_params"]["model"] for x in ok))
    if not ok:
        raise SystemExit("::error::ningún modelo responde con las claves disponibles")
    cfg = {"model_list": ok, "router_settings": {"num_retries": 3, "routing_strategy": "simple-shuffle"},
           "litellm_settings": {"drop_params": True}, "general_settings": {"master_key": master}}
    with open(out_path, "w") as f:
        f.write(yaml.safe_dump(cfg))


if __name__ == "__main__":
    import sys
    main(*(sys.argv[1:3] if len(sys.argv) >= 3 else []))
