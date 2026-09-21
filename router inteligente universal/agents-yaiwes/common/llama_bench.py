"""Real tokens/second of the small local models with llama.cpp on a CPU runner (proxy of the HF CPU nodes).
 1) llama-bench: prompt processing (pp256) and token generation (tg128) with the accelerators (flash attention, threads).
 2) llama-server with parallel slots (-np 4), continuous batching, prompt cache, KV q8_0: aggregate tokens/s with 1, 4 and 8 simultaneous requests.
Everything is reported as GitHub annotations (RIU_BENCH_*), including every failure with its reason."""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import tarfile
import threading
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path

import requests
from huggingface_hub import hf_hub_download

MODELS = {
    "qwen35-0.8b-q4_0": ("ggml-org/Qwen3.5-0.8B-GGUF", "Qwen3.5-0.8B-Q4_0.gguf"),
    "lfm25-1.2b-instruct-q4km": ("LiquidAI/LFM2.5-1.2B-Instruct-GGUF", "LFM2.5-1.2B-Instruct-Q4_K_M.gguf"),
    "lfm25-1.2b-thinking-q4km": ("LiquidAI/LFM2.5-1.2B-Thinking-GGUF", "LFM2.5-1.2B-Thinking-Q4_K_M.gguf"),
    "qwen3-0.6b-q8": ("Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf"),
    "gemma4-e2b-qat-q4_0": ("google/gemma-4-E2B-it-qat-q4_0-gguf", "gemma-4-E2B_q4_0-it.gguf"),
}
THREADS = os.cpu_count() or 4
BAD = r"vulkan|rocm|openvino|sycl|cuda|hip|arm|s390|riscv|musa|kompute|opencl"


def note(title: str, msg: str, level: str = "notice") -> None:
    print(f"::{level} title=RIU_BENCH_{title}::{msg}".replace("\n", " ")[:900], flush=True)


def get_llama() -> str:
    hdr = {"Authorization": "Bearer " + os.environ.get("GH_TOKEN", "")}
    rels = requests.get("https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=40", headers=hdr, timeout=60).json()
    chosen = None
    for rel in rels:
        cands = [a for a in rel.get("assets", []) if re.search(r"(ubuntu|linux).*x64", a["name"]) and not re.search(BAD, a["name"])]
        if cands:
            chosen = (rel, cands[0])
            break
    if not chosen:
        raise RuntimeError("ninguna release trae binario ubuntu-x64; etiquetas vistas: " + ",".join(str(r.get("tag_name")) for r in rels[:6]))
    rel, asset = chosen
    note("LLAMACPP", f"release={rel.get('tag_name')} asset={asset['name']} ({asset['size'] / 1e6:.0f} MB)")
    blob = requests.get(asset["browser_download_url"], timeout=600).content
    dest = Path("/tmp/llama")
    dest.mkdir(exist_ok=True)
    if asset["name"].endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(blob)).extractall(dest)
    else:
        tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz").extractall(dest)
    bench = next(dest.rglob("llama-bench"))
    subprocess.run(["chmod", "-R", "+x", str(bench.parent)], check=False)
    note("BINARIOS", f"{bench.parent} -> {sorted(p.name for p in bench.parent.iterdir() if p.name.startswith('llama-'))[:8]}")
    return str(bench.parent)


def bench(binp: str, path: str) -> str:
    env = {**os.environ, "LD_LIBRARY_PATH": binp}
    last = ""
    for fa in ("1", "0"):
        p = subprocess.run([f"{binp}/llama-bench", "-m", path, "-p", "256", "-n", "128", "-t", str(THREADS), "-fa", fa, "-r", "2", "-o", "json"],
                           capture_output=True, text=True, timeout=900, env=env)
        last = (p.stderr or p.stdout)[-160:]
        if p.returncode == 0:
            try:
                rows = json.loads(p.stdout)
                pp = next((r["avg_ts"] for r in rows if r.get("n_prompt") and not r.get("n_gen")), float("nan"))
                tg = next((r["avg_ts"] for r in rows if r.get("n_gen") and not r.get("n_prompt")), float("nan"))
                return f"pp256={pp:.1f} t/s | tg128={tg:.1f} t/s | flash_attn={fa} | threads={THREADS}"
            except Exception as exc:  # noqa: BLE001
                return f"salida no interpretable ({type(exc).__name__}): {p.stdout[:120]}"
    return "FALLO: " + last


def post(port: int) -> int:
    body = json.dumps({"prompt": "Escribe una lista de 5 ideas para un chat de agentes.", "n_predict": 64, "temperature": 0.7, "cache_prompt": True}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/completion", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:  # noqa: S310
        return int(json.loads(r.read().decode()).get("tokens_predicted", 0))


def serve(binp: str, path: str) -> str:
    port, env = 8080, {**os.environ, "LD_LIBRARY_PATH": binp}
    for fa in ("on", "off"):
        cmd = [f"{binp}/llama-server", "-m", path, "--host", "127.0.0.1", "--port", str(port), "-c", "8192", "-np", "4", "-cb", "--cache-prompt",
               "--cache-reuse", "256", "-t", str(THREADS), "-fa", fa] + (["-ctk", "q8_0", "-ctv", "q8_0"] if fa == "on" else [])
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        ok = False
        for _ in range(90):
            time.sleep(2)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)  # noqa: S310
                ok = True
                break
            except Exception:  # noqa: BLE001
                if proc.poll() is not None:
                    break
        if not ok:
            proc.terminate()
            continue
        res = []
        for conc in (1, 4, 8):
            t0, total, lock = time.time(), [0], threading.Lock()

            def worker() -> None:
                try:
                    n = post(port)
                except Exception:  # noqa: BLE001
                    n = 0
                with lock:
                    total[0] += n

            ts = [threading.Thread(target=worker) for _ in range(conc)]
            [t.start() for t in ts]
            [t.join() for t in ts]
            dt = time.time() - t0
            res.append(f"{conc} simult.: {total[0] / dt:.1f} t/s total ({total[0] / dt / conc:.1f} por agente)")
        proc.terminate()
        proc.wait(timeout=20)
        return f"flash_attn={fa} slots=4 | " + " | ".join(res)
    return "el servidor no arrancó"


def main() -> int:
    try:
        binp = get_llama()
    except Exception as exc:  # noqa: BLE001
        note("ERROR_LLAMACPP", f"{type(exc).__name__}: {exc}", "warning")
        return 1
    paths: dict[str, str] = {}
    for name, (repo, fname) in MODELS.items():
        try:
            paths[name] = hf_hub_download(repo, fname, local_dir="/tmp/models", token=os.environ.get("HF_TOKEN") or None)
            note("MODELO_OK", f"{name} {Path(paths[name]).stat().st_size / 1e6:.0f} MB")
        except Exception as exc:  # noqa: BLE001
            note("MODELO_FALLO", f"{name}: {type(exc).__name__} {str(exc)[:110]}", "warning")
    for name, path in paths.items():
        try:
            note(name, bench(binp, path))
        except Exception as exc:  # noqa: BLE001
            note("ERROR_" + name, f"{type(exc).__name__}: {str(exc)[:200]}", "warning")
    for name in ("qwen35-0.8b-q4_0", "lfm25-1.2b-instruct-q4km"):
        if name in paths:
            try:
                note("SLOTS_" + name, serve(binp, paths[name]))
            except Exception as exc:  # noqa: BLE001
                note("ERROR_SLOTS_" + name, f"{type(exc).__name__}: {str(exc)[:200]}", "warning")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        note("ERROR_GENERAL", traceback.format_exc()[-300:], "warning")
        raise SystemExit(1)
