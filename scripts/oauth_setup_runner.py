"""oauth_setup_runner.py — Escanea 5 MCP OAuth. No bloquea el pool.
--phase=scan:    detecta env vars y actualiza banco/secrets.json -> oauth_status
--phase=verify:  imprime OAUTH_READY:<n>

ADAPTACION 3 (bucket): huggingface_hub NO soporta repo_type="bucket" (el bucket no es
repo git). La lectura/escritura del banco se hace con el CLI oficial `hf cp`, que es
la via ya probada para este bucket.
ADAPTACION 2 (token): acepta HF_TOKEN o HF_TOKEN_1_NEW.
"""
import os, sys, json, subprocess, tempfile
from pathlib import Path

SERVERS = {
    "supabase": {"env": "SUPABASE_ACCESS_TOKEN",
                 "url": "https://supabase.com/dashboard/account/tokens"},
    "notion":   {"env": "NOTION_TOKEN",
                 "url": "https://www.notion.so/my-integrations"},
    "stripe":   {"env": "STRIPE_SECRET_KEY",
                 "url": "https://dashboard.stripe.com/apikeys"},
    "sentry":   {"env": "SENTRY_AUTH_TOKEN",
                 "url": "https://sentry.io/settings/account/api/auth-tokens/"},
    "linear":   {"env": "LINEAR_API_KEY",
                 "url": "https://linear.app/settings/api"},
}

BUCKET = "COMAND-CENTER-1/yaiwes-memoria-storage"
BANK_PATH = "banco/secrets.json"
TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN_1_NEW")
PHASE = next((a.split("=")[1] for a in sys.argv if a.startswith("--phase=")), "scan")
DST = "hf://buckets/" + BUCKET

def hf_cp(args):
    env = dict(os.environ)
    env["UV_DEFAULT_INDEX"] = "https://pypi.org/simple"
    env["UV_CACHE_DIR"] = "/workspace/.uvcache"
    env["HF_TOKEN"] = TOKEN
    r = subprocess.run(["uvx", "hf"] + args, env=env, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-300:])
    return r

def load_bank():
    tmp = Path(tempfile.mkdtemp()) / "secrets.json"
    hf_cp(["cp", "{}/{}".format(DST, BANK_PATH), str(tmp)])
    return json.load(open(tmp, encoding="utf-8"))

def save_bank(data):
    tmp = Path(tempfile.mkdtemp()) / "secrets.json"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    hf_cp(["cp", str(tmp), "{}/{}".format(DST, BANK_PATH)])

def main():
    if PHASE == "verify":
        bank = load_bank()
        ready = sum(1 for s in SERVERS if bank.get("oauth_status", {}).get(s) == "ready")
        print(f"OAUTH_READY:{ready}")
        sys.exit(0 if ready == 5 else 1)

    bank = load_bank()
    bank.setdefault("oauth_status", {})
    bank.setdefault("oauth_urls", {})
    for name, cfg in SERVERS.items():
        bank["oauth_urls"][name] = cfg["url"]
        if os.getenv(cfg["env"]):
            bank["oauth_status"][name] = "ready"
        else:
            bank["oauth_status"][name] = "oauth_pending"
    save_bank(bank)
    ready = sum(1 for s in SERVERS if bank["oauth_status"][s] == "ready")
    print(f"OAUTH_SCAN_DONE ready={ready}/5 pending={5-ready}/5")
    sys.exit(0 if ready == 5 else 2)

if __name__ == "__main__":
    main()
