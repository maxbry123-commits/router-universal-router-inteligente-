"""
provider_health_dashboard.py — Monitor simple de 429/410/502 en logs del proxy
Ubicacion: external/improvements/provider_health_dashboard.py
Uso: python external/improvements/provider_health_dashboard.py [log_file]
Nota: si no hay log_file, solo reporta que el proxy responde /health.
"""
import httpx
import re
import sys
from collections import Counter


PROXY_URL = "http://localhost:7860"
PATTERNS = {
    "429": re.compile(r"\b429\b"),
    "410": re.compile(r"\b410\b"),
    "502": re.compile(r"\b502\b"),
    "groq": re.compile(r"\bgroq\b", re.IGNORECASE),
    "nvidia": re.compile(r"\bnvidia\b", re.IGNORECASE),
}


def scan_log(path: str) -> dict:
    counts = Counter()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            for key, pat in PATTERNS.items():
                if pat.search(line):
                    counts[key] += 1
    return dict(counts)


def ping_health():
    try:
        r = httpx.get(f"{PROXY_URL}/health", timeout=5)
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, {"error": str(e)}


def main():
    print("=" * 70)
    print("PROVIDER HEALTH DASHBOARD")
    print("=" * 70)
    ok, data = ping_health()
    print(f"\n[proxy /health] ok={ok} data={data}")

    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"\n[log scan] {path}")
        counts = scan_log(path)
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")
    else:
        print("\n[log scan] sin archivo (pasa la ruta como argumento)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
