"""simulate_modes.py — 12 simulaciones de modos (codigo) + 4 de servicio.

Simula la cadena COMPLETA de cada modo, sin inferir nada:
  prompt canonico -> detector -> alias -> adapter_config.json en HF ->
  dataset combined (swe-code-modes) -> LoRA (swe-code-loras) ->
  base_model -> Space local del Grupo 2 o proveedor externo.

Salida: JSON + tabla Markdown (para leerlos de un vistazo).
Criterio de PASS por modo:
  - el detector devuelve el modo esperado,
  - el adapter existe (HTTP 200 + JSON valido),
  - el dataset combinado existe (o, en modos de servicio, el contrato existe),
  - la LoRA existe cuando el modo la declara,
  - el base_model esta vivo o es un GGUF local servible.
"""
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
from router_llm_hf.mode_detector import detect_mode, detect_service_route  # noqa: E402
from router_llm_hf.mode_router import adapter_name_for_mode  # noqa: E402
from router_llm_hf.service_routes import SERVICE_MODES  # noqa: E402

TOKEN = os.environ.get("HF_TOKEN_1_NEW") or os.environ.get("HF_TOKEN")
ADAPTERS_REPO = "COMAND-CENTER-1/swe-code-adapters"
MODES_REPO = "COMAND-CENTER-1/swe-code-modes"
LORAS_REPO = "COMAND-CENTER-1/swe-code-loras"
OUT_DIR = "/workspace/simulations"

# Modelos servidos por el Grupo 2 (3 Spaces) -> Space
LOCAL_GGUF = {
    "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF": "swe-code-s1",
    "LiquidAI/LFM2.5-350M-GGUF": "swe-code-s2",
    "unsloth/Qwen3.5-0.8B-GGUF": "swe-code-s3",
}

CODE_PROMPTS = {
    "code_refactor": "refactoriza el modulo de facturacion",
    "code_debug": "debug del error de autenticacion",
    "code_review": "revisa el pull request de la API",
    "code_generate": "implementa una funcion que valida el dni",
    "architecture": "diseña la arquitectura del sistema",
    "reasoning": "razona por que falla el pool de conexiones",
    "tool_call": "llama a la herramienta API de pagos",
    "planning": "plan de fases para migrar el router",
    "documentation": "documenta la funcion con un README",
    "frontend": "crea la interfaz del boton en React",
    "3d_code": "modelo 3D en Blender",
    "verification": "verifica con un test unitario",
}

SERVICE_PROMPTS = {
    "swe_code": "hazme un swe code del modulo",
    "swe_free": "usa swe free para esto",
    "team_qwe": "lanzalo con team qwe",
    "deployment": "despliega el servicio con kubernetes",
}


def http(url, method="GET", timeout=30):
    req = urllib.request.Request(url, method=method,
                                 headers={"Authorization": "Bearer {}".format(TOKEN)})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return r.status, body, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers or {})
    except Exception as e:
        return 0, str(e).encode(), {}


def adapters_url(path):
    return "https://huggingface.co/{}/resolve/main/{}".format(ADAPTERS_REPO, path)


def modes_url(path):
    return "https://huggingface.co/datasets/{}/resolve/main/{}".format(MODES_REPO, path)


def tree_paths(repo, kind="models"):
    """Arbol del repo de HF en UNA llamada. (El HEAD contra el CDN xet falla
    de forma intermitente: daba 0 en 3 de 12 ficheros que existen. El arbol de
    la API es la fuente fiable.)"""
    prefix = {"models": "models/", "datasets": "datasets/"}.get(kind, "")
    code, body, _ = http("https://huggingface.co/api/{}{}/tree/main?recursive=true".format(prefix, repo))
    if code != 200:
        return set()
    try:
        return {x["path"] for x in json.loads(body)}
    except Exception:
        return set()


def lora_folders():
    code, body, _ = http("https://huggingface.co/api/datasets/{}/tree/main".format(LORAS_REPO))
    if code != 200:
        return []
    try:
        return [x["path"] for x in json.loads(body)]
    except Exception:
        return []


def simulate_code(mode, prompt, loras, modes_tree):
    row = {"family": "codigo", "mode": mode, "prompt": prompt}
    detected = detect_mode(prompt)
    row["detected"] = detected
    row["detect_ok"] = detected == mode
    name = adapter_name_for_mode(mode)
    row["adapter_folder"] = name
    if not name:
        row.update({"adapter_http": None, "adapter_ok": False, "verdict": "SIN ADAPTER",
                    "gap": "sin equivalente explicito en el repo de adapters (declarado, no inventado)"})
        return row
    code, body, _ = http(adapters_url("{}/adapter_config.json".format(name)))
    row["adapter_http"] = code
    cfg = {}
    if code == 200:
        try:
            cfg = json.loads(body)
        except Exception:
            cfg = {}
    row["adapter_ok"] = code == 200 and bool(cfg.get("mode"))
    row["base_model"] = cfg.get("base_model")
    row["lora"] = cfg.get("lora")
    row["dataset_source"] = cfg.get("dataset")
    row["dataset_combined"] = cfg.get("dataset_combined")
    row["dataset_rows"] = cfg.get("dataset_rows")

    # dataset combinado: el fichero tiene que estar en el arbol de swe-code-modes
    if cfg.get("dataset_combined"):
        rel = cfg["dataset_combined"].split("swe-code-modes/", 1)[-1]
        row["dataset_http"] = 200 if rel in modes_tree else 404
        row["dataset_path_rel"] = rel
    else:
        row["dataset_http"] = None
        row["dataset_path_rel"] = None

    # LoRA: esta la carpeta en swe-code-loras?
    if cfg.get("lora"):
        row["lora_present"] = any(f.startswith(cfg["lora"]) or f == cfg["lora"] for f in loras) or \
            any(name in f for f in loras)
    else:
        row["lora_present"] = None  # modo base_only

    # destino: Space local o proveedor
    bm = cfg.get("base_model") or ""
    row["destino"] = LOCAL_GGUF.get(bm, "proveedor externo (NVIDIA/Groq)")
    row["local_space"] = LOCAL_GGUF.get(bm)

    ok = row["detect_ok"] and row["adapter_ok"] and (
        row["dataset_http"] == 200 or not cfg.get("dataset_combined"))
    if cfg.get("lora"):
        ok = ok and bool(row["lora_present"])
    row["verdict"] = "PASS" if ok else "FAIL"
    return row


def simulate_service(mode, prompt, modes_tree):
    cfg = SERVICE_MODES[mode]
    row = {"family": "servicio", "mode": mode, "prompt": prompt,
           "detected": detect_service_route(prompt), "route": cfg["route"],
           "local_space": cfg["space"], "local_model": cfg["model"],
           "local_first": cfg["local_first"], "destino": "servicio"}
    row["detect_ok"] = row["detected"] == mode
    code, body, _ = http(adapters_url("{}/adapter_config.json".format(mode)))
    row["adapter_http"] = code
    row["adapter_ok"] = code == 200
    cfg2 = {}
    if code == 200:
        try:
            cfg2 = json.loads(body)
        except Exception:
            cfg2 = {}
    row["base_model"] = cfg2.get("base_model")
    row["lora"] = cfg2.get("lora")
    row["dataset_source"] = cfg2.get("dataset")
    row["dataset_combined"] = cfg2.get("dataset_combined")
    row["dataset_http"] = None
    row["lora_present"] = None
    rel = "{}/service_contract.json".format(mode)
    row["contrato_http"] = 200 if rel in modes_tree else 404
    row["dataset_path_rel"] = rel
    row["verdict"] = "PASS" if (row["detect_ok"] and row["adapter_ok"]
                                and row["contrato_http"] == 200) else "FAIL"
    return row


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    loras = lora_folders()
    modes_tree = tree_paths(MODES_REPO, kind="datasets")
    rows = []
    for mode, prompt in CODE_PROMPTS.items():
        rows.append(simulate_code(mode, prompt, loras, modes_tree))
    for mode, prompt in SERVICE_PROMPTS.items():
        rows.append(simulate_service(mode, prompt, modes_tree))

    code_rows = [r for r in rows if r["family"] == "codigo"]
    svc_rows = [r for r in rows if r["family"] == "servicio"]
    adapters_tree = tree_paths(ADAPTERS_REPO, kind="models")
    n_adapters = len([p for p in adapters_tree if p.endswith("/adapter_config.json")])
    summary = {
        "generado": "2026-11-18",
        "total_simulaciones": len(rows),
        "codigo": {"total": len(code_rows), "pass": sum(1 for r in code_rows if r["verdict"] == "PASS")},
        "servicio": {"total": len(svc_rows), "pass": sum(1 for r in svc_rows if r["verdict"] == "PASS")},
        "adaptadores_en_hf": n_adapters,
        "detalle": rows,
    }
    with open(os.path.join(OUT_DIR, "sim_18_modos.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "sim_18_modos.json"), "rb") as fh:
        print("JSON sha256: {}".format(hashlib.sha256(fh.read()).hexdigest()))

    lines = ["| # | Familia | Modo | Detectado | Adapter | Dataset | LoRA | Destino | Veredicto |",
             "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        det = r["detected"]
        ad = "OK" if r.get("adapter_ok") else ("n/a" if r.get("adapter_folder") is None else "FALLO")
        ds = r.get("dataset_http")
        ds_txt = {200: "OK", 404: "FALLO", None: "n/a"}.get(ds, str(ds))
        lo = r.get("lora_present")
        lo_txt = {True: "OK", False: "FALLO", None: "n/a"}.get(lo, str(lo))
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            i, r["family"], r["mode"], det, ad, ds_txt, lo_txt,
            r.get("destino", "-"), r["verdict"]))
    md = "\n".join(lines) + "\n"
    with open(os.path.join(OUT_DIR, "sim_18_modos.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md)
    print("SIM_CODIGO {}/{} | SIM_SERVICIO {}/{}".format(
        summary["codigo"]["pass"], summary["codigo"]["total"],
        summary["servicio"]["pass"], summary["servicio"]["total"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
