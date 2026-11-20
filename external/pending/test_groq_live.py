"""
test_groq_live.py — Prueba real contra Groq (cierra O1)
Ubicacion: external/pending/test_groq_live.py
Uso: GROQ_KEYS=gsk_xxx ROUTER_API_KEY=master python external/pending/test_groq_live.py
"""
import httpx
import os
import sys
import time

PROXY_URL = os.getenv("PROXY_URL", "http://localhost:7860")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "")
GROQ_KEYS = os.getenv("GROQ_KEYS", "")


def health():
    try:
        r = httpx.get(f"{PROXY_URL}/health", timeout=5)
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, {"error": str(e)}


def control_plane_status():
    try:
        r = httpx.get(f"{PROXY_URL}/control-plane/status", timeout=5)
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, {"error": str(e)}


def chat(prompt: str, model: str = "groq") -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }
    headers = {
        "X-API-Key": ROUTER_API_KEY,
        "Content-Type": "application/json",
    }
    t0 = time.time()
    try:
        r = httpx.post(
            f"{PROXY_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=120,
        )
        elapsed = time.time() - t0
        return {
            "status": r.status_code,
            "elapsed_s": round(elapsed, 2),
            "body": r.json() if r.status_code == 200 else r.text[:500],
        }
    except Exception as e:
        return {"status": "EXCEPTION", "error": str(e), "elapsed_s": round(time.time() - t0, 2)}


def main():
    print("=" * 70)
    print("PRUEBA REAL CONTRA GROQ (O1)")
    print("=" * 70)
    if not ROUTER_API_KEY:
        print("Falta ROUTER_API_KEY en entorno")
        return 1
    if not GROQ_KEYS:
        print("Falta GROQ_KEYS en entorno")
        return 1

    print("\n[1/4] /health")
    ok, data = health()
    print(f"  ok={ok} data={data}")

    print("\n[2/4] /control-plane/status")
    ok2, data2 = control_plane_status()
    print(f"  ok={ok2} data={data2}")

    print("\n[3/4] chat simple (ping)")
    r1 = chat("Responde solo la palabra PING")
    print(f"  status={r1['status']} elapsed={r1.get('elapsed_s')}s")
    if r1["status"] == 200:
        content = r1["body"]["choices"][0]["message"]["content"]
        print(f"  contenido={content[:100]!r}")

    print("\n[4/4] chat con mas tokens")
    r2 = chat("Escribe un haiku sobre la programacion", model="groq")
    print(f"  status={r2['status']} elapsed={r2.get('elapsed_s')}s")
    if r2["status"] == 200:
        content = r2["body"]["choices"][0]["message"]["content"]
        print(f"  contenido={content[:200]!r}")

    print("\n" + "=" * 70)
    all_ok = (
        ok and ok2 and
        r1.get("status") == 200 and
        r2.get("status") == 200
    )
    print("RESULTADO:", "OK" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
