"""
health_check_all.py — Ping a /health + status del puente Control Plane
Ubicacion: external/tools/health_check_all.py
Uso: python external/tools/health_check_all.py [http://localhost:7860]
"""
import httpx
import sys

DEFAULT_URL = "http://localhost:7860"


def check(url: str) -> dict:
    result = {"url": url, "endpoints": {}}
    for name, path in [("health", "/health"), ("control-plane", "/control-plane/status")]:
        try:
            r = httpx.get(f"{url}{path}", timeout=10)
            result["endpoints"][name] = {
                "status": r.status_code,
                "body": r.json() if r.status_code == 200 else r.text[:300],
            }
        except Exception as e:
            result["endpoints"][name] = {"status": "EXCEPTION", "error": str(e)}
    return result


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    print(f"Checkeando {url}")
    r = check(url)
    for name, data in r["endpoints"].items():
        print(f"\n  [{name}]")
        for k, v in data.items():
            print(f"    {k}: {v}")
    all_ok = all(e.get("status") == 200 for e in r["endpoints"].values())
    print(f"\nRESULTADO: {'OK' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
