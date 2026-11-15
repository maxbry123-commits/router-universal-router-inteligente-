"""probe_sondas.py — Sondas de health check de componentes del sistema."""
from __future__ import annotations
import os, time, logging
logger = logging.getLogger(__name__)


def _probe_url(url, timeout=5.0):
    try:
        import httpx
        t0 = time.time()
        r = httpx.get(url, timeout=timeout)
        return {"ok": r.status_code < 500, "status_code": r.status_code,
                "elapsed_ms": round((time.time() - t0) * 1000, 2)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def probe_router_mvp(url=None):
    u = url or os.getenv("ROUTER_MVP_URL", "http://localhost:7860")
    return {"name": "router_mvp", **_probe_url(f"{u.rstrip('/')}/health")}


def probe_capa_api(url=None):
    u = url or os.getenv("CAPA_API_URL", "http://localhost:7861")
    return {"name": "capa_api", **_probe_url(f"{u.rstrip('/')}/capa/status")}


def probe_hf_spaces():
    token = os.getenv("HF_TOKEN")
    ns = os.getenv("HF_NAMESPACE", "")
    if not token or not ns:
        return {"name": "hf_spaces", "ok": False, "error": "HF_TOKEN o HF_NAMESPACE ausente"}
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        results, running = {}, 0
        for sid in ["s1", "s2", "s3"]:
            try:
                info = api.get_space_info(f"{ns}/{sid}", repo_type="space")
                stage = str(getattr(info, "stage", "UNKNOWN"))
                results[sid] = stage
                if stage == "RUNNING":
                    running += 1
            except Exception as e:
                results[sid] = f"ERROR: {type(e).__name__}"
        return {"name": "hf_spaces", "ok": running == 3,
                "running": running, "total": 3, "details": results}
    except Exception as e:
        return {"name": "hf_spaces", "ok": False, "error": type(e).__name__}


def probe_handoff():
    try:
        from external.nct.handoff import HANDOFF
        snap = HANDOFF.snapshot(last_n=1)
        return {"name": "handoff", "ok": True, "total_entries": snap.get("total_entries", 0)}
    except Exception as e:
        return {"name": "handoff", "ok": False, "error": type(e).__name__}


def probe_crazy_wall():
    try:
        from external.nct.crazy_wall import WALL
        size = WALL.size()
        return {"name": "crazy_wall", "ok": size.get("exists", False),
                "lines": size.get("lines", 0), "bytes": size.get("bytes", 0)}
    except Exception as e:
        return {"name": "crazy_wall", "ok": False, "error": type(e).__name__}


def probe_all():
    probes = [probe_router_mvp(), probe_capa_api(), probe_hf_spaces(),
              probe_handoff(), probe_crazy_wall()]
    ok_count = sum(1 for p in probes if p.get("ok"))
    return {
        "timestamp": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(probes), "ok": ok_count,
        "failed": len(probes) - ok_count,
        "status": "ok" if ok_count == len(probes) else "degraded" if ok_count > 0 else "fail",
        "probes": probes,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(probe_all(), indent=2, ensure_ascii=False))
