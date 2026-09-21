"""Probe every provider key of the encrypted bank (NVIDIA, Groq, Cerebras): list models + one tiny chat each.
Prints only the key's position and the HTTP status, never the key. Run: RIU_BANK_PASSPHRASE=... python probe_keys.py"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import boot  # noqa: E402


def call(method: str, url: str, key: str, body: dict | None = None, timeout: float = 40.0) -> tuple[str, dict]:
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method=method,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "riu-probe"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            return str(r.status), json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        return str(exc.code), {}
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__, {}


def main() -> int:
    boot.open_bank("probe")
    from integration.chat_mvp import providers as prov
    from kernel import dispatcher

    jobs = [(p, i, k) for p in ("nvidia", "groq", "cerebras") for i, k in enumerate(prov.env_keys(p), 1)]

    def one(job: tuple[str, int, str]) -> tuple[str, int, str, str, str]:
        p, i, k = job
        base = prov.PROVIDERS[p]["base"]
        s, d = call("GET", base + "/models", k)
        ids = [m["id"] for m in d.get("data", [])] if s == "200" else []
        model = next((m for m in dispatcher.PREFS[p] if m in ids), ids[0] if ids else dispatcher.PREFS[p][0])
        t0 = time.time()
        cs, cd = call("POST", base + "/chat/completions", k, {"model": model, "messages": [{"role": "user", "content": "Reply with the single word OK"}], "max_tokens": 32})
        txt = ((cd.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        return p, i, s, ("OK" if cs == "200" and txt.strip() else cs), f"{model}:{time.time() - t0:.0f}s"

    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(one, jobs))
    for p in ("nvidia", "groq", "cerebras"):
        rows = [r for r in res if r[0] == p]
        print(f"::notice title=RIU_PROBE_{p.upper()}::" + " | ".join(f"k{i} models={s} chat={c} ({m})" for _, i, s, c, m in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
