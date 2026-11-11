"""
verify_diffs_f1.py — Lee RAW de archivos con diff vacio en KB y compara (cierra F1a/b/c/d, F1)
Ubicacion: external/pending/verify_diffs_f1.py
Uso: python external/pending/verify_diffs_f1.py
"""
import hashlib
import httpx
import sys

REPO = "maxbry123-commits/router-universal-router-inteligente-"
BRANCH = "ccr-f01c3de9-bmry0s"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

TARGETS = [
    ("F1d", "router_llm_hf/__init__.py"),
    ("F1b", "router_llm_hf/escalation_guard.py"),
    ("F1c", "router_llm_hf/tests/test_queue_manager.py"),
    ("F1a", "ROUTER MVP v1/system_prompt_py/tests/test_control_bridge.py"),
    ("F1",  "router_llm_hf/README.md"),
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_raw(path: str) -> str:
    url = f"{RAW_BASE}/{path}"
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"ERROR: {e}"


def check_syntax_python(text: str) -> str:
    try:
        compile(text, "<raw>", "exec")
        return "OK"
    except SyntaxError as e:
        return f"SYNTAX_ERROR: {e}"


def main():
    print("=" * 70)
    print("VERIFICACION FORENSE DE DIFFS VACIOS (F1a/b/c/d, F1)")
    print("=" * 70)
    results = []
    for flag, path in TARGETS:
        text = fetch_raw(path)
        is_error = text.startswith("ERROR:")
        size = len(text.encode("utf-8"))
        sha = sha256_text(text) if not is_error else "N/A"
        syntax = check_syntax_python(text) if (not is_error and path.endswith(".py")) else "n/a"
        lines = text.count("\n") if not is_error else 0
        results.append({
            "flag": flag,
            "path": path,
            "size_bytes": size,
            "lines": lines,
            "sha256": sha,
            "syntax": syntax,
        })
        print(f"\n[{flag}] {path}")
        print(f"  size={size} bytes  lines={lines}  sha256={sha[:16]}...")
        print(f"  syntax={syntax}")

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    for r in results:
        status = "ERROR" if r["sha256"] == "N/A" else ("OK" if r["syntax"] in ("OK", "n/a") else "FAIL")
        print(f"  {r['flag']:5s} {r['path']:60s} {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
