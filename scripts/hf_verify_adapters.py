"""hf_verify_adapters.py - Verifica los 4 GAP en el repo HF.
Salida: reports/adapters_verify.json. Nunca aborta el pipeline."""
import json, os, urllib.request

REPO = "COMAND-CENTER-1/swe-code-adapters"
MODES = ["python", "backend", "architecture", "agentic_tool"]


def check(mode: str) -> dict:
    url = f"https://huggingface.co/{REPO}/resolve/main/{mode}/adapter_config.json"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            if r.status != 200:
                return {"mode": mode, "ok": False, "http": r.status}
            cfg = json.loads(r.read())
            return {"mode": mode, "ok": True,
                    "base_model": cfg.get("base_model_name_or_path"),
                    "dataset": cfg.get("dataset")}
    except Exception as e:
        return {"mode": mode, "ok": False,
                "error": f"{type(e).__name__}:{e}"}


def main():
    results = [check(m) for m in MODES]
    ok = sum(1 for r in results if r["ok"])
    os.makedirs("reports", exist_ok=True)
    with open("reports/adapters_verify.json", "w", encoding="utf-8") as f:
        json.dump({"repo": REPO, "modes": results, "ok_count": ok},
                  f, indent=2)
    print(f"ADAPTERS_VERIFY: {ok}/{len(MODES)} OK")
    for r in results:
        print(f"  {r['mode']:15s} {'OK' if r['ok'] else 'MISSING'}")


if __name__ == "__main__":
    main()
