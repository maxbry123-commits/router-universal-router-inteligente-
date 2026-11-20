"""apply_improvements_v5.py - 8 mejoras deterministas. Idempotente."""
import json, os, re


def _rw(path, fn):
    if not os.path.exists(path):
        return False
    src = open(path, "r", encoding="utf-8").read()
    new = fn(src)
    if new != src:
        open(path, "w", encoding="utf-8").write(new)
        return True
    return False


def m1_proxy_failclosed(s):
    """1. lifespan falla si falta ROUTER_API_KEY."""
    if "async def lifespan" in s and "get_env()" not in s:
        anchor = "async def lifespan(app):"
        guard = (anchor + "\n    from external.core.env_config import get_env\n"
                 "    _c = get_env()\n"
                 "    if not _c.ROUTER_API_KEY:\n"
                 "        raise RuntimeError('ROUTER_API_KEY ausente')")
        s = s.replace(anchor, guard, 1)
    return s


def m2_route_safe(s):
    """2. route() envuelto en try/except."""
    if "def route(" not in s or "_route_impl" in s:
        return s
    m = re.search(r"def route\(payload: dict\) -> dict:\n", s)
    if not m:
        return s
    return (s[:m.start()] +
            "def route(payload: dict) -> dict:\n"
            "    try:\n        return _route_impl(payload)\n"
            "    except Exception as e:\n"
            "        return {'error': str(e), 'mode': payload.get('mode')}\n\n"
            "def _route_impl(payload: dict) -> dict:\n" +
            s[m.end():])


def m3_no_harness_fallback(s):
    """3. HARNESS_KEY no hereda de ROUTER_API_KEY."""
    return s.replace('os.getenv("HARNESS_KEY") or os.getenv("ROUTER_API_KEY", "")',
                     'os.getenv("HARNESS_KEY", "")')


def m4_prune_checkpoints(s):
    """4. CheckpointManager.prune()."""
    if "def prune" in s or "class CheckpointManager" not in s:
        return s
    return s.rstrip() + '''

    def prune(self, max_age_days: int = 7) -> int:
        import time
        cutoff = time.time() - max_age_days * 86400
        n = 0
        for p in self.state_dir.glob("*.json"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink(); n += 1
            except Exception: pass
        return n
'''


def m5_capa_healthy(s):
    """5. /capa/status devuelve healthy real via probe_all."""
    if "/capa/status" not in s or "probe_all" in s:
        return s
    return s.replace('"uptime": "ok",',
                     '"uptime": "ok",\n        "healthy": '
                     '__import__("external.core.health_check", '
                     'fromlist=["probe_all"]).probe_all().get("ok", False),', 1)


def m6_hf_restart_http(s):
    """6. Tras RUNNING, probe HTTP a /health."""
    if "def main()" not in s or "requests.get" in s:
        return s
    return s.replace(
        'print("OK: Space RUNNING.")',
        'import requests\n            try:\n'
        '                url = f"https://{SPACE.replace(chr(47), chr(45)).lower()}.hf.space/health"\n'
        '                r = requests.get(url, timeout=10)\n'
        '                if r.status_code >= 500:\n'
        '                    print(f"FLAG:space_unhealthy:{r.status_code}")\n'
        '            except Exception as e:\n'
        '                print(f"FLAG:health_probe:{e}")\n'
        '            print("OK: Space RUNNING.")', 1)


def m7_tool_registry_cfg(s):
    """7. Añade tool_registry al config central."""
    if '"tool_registry"' in s:
        return s
    try:
        d = json.loads(s)
    except Exception:
        return s
    d["tool_registry"] = {
        "fs": ["read_file", "write_file", "list_dir", "grep"],
        "shell": ["run_shell"],
        "verify": ["run_tests", "run_lint", "run_types",
                   "py_compile", "ast_parse", "json_load", "yaml_load"],
    }
    return json.dumps(d, indent=2, ensure_ascii=False)


def m8_prune_dbs(_):
    """8. Ejecuta prune de DBs una vez."""
    try:
        from external.history.conversation_store import prune as conv_prune
        from external.memory.long_term import prune as ltm_prune
        from external.core.semantic_cache import purge_expired
        print(f"PRUNE: conv={conv_prune(30)} ltm={ltm_prune(90)} cache={purge_expired()}")
    except Exception as e:
        print(f"PRUNE_SKIP:{type(e).__name__}:{e}")
    return _


def main():
    targets = [
        ("ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py", m1_proxy_failclosed),
        ("router_llm_hf/mode_router.py", m2_route_safe),
        ("router_llm_hf/harness_wiring.py", m3_no_harness_fallback),
        ("router_llm_hf/checkpoint_manager.py", m4_prune_checkpoints),
        ("external/api/capa_api.py", m5_capa_healthy),
        ("scripts/hf_restart_space.py", m6_hf_restart_http),
        ("external/core/SATELITE_CENTRAL_CONECCION.json", m7_tool_registry_cfg),
    ]
    results = []
    for path, fn in targets:
        try:
            changed = _rw(path, fn)
            results.append(f"{'CHANGED' if changed else 'SKIP'}:{path}")
        except Exception as e:
            results.append(f"ERROR:{path}:{type(e).__name__}:{e}")
    m8_prune_dbs(None)
    print("IMPROVE_RESULTS:")
    for r in results:
        print(f"  {r}")


if __name__ == "__main__":
    main()
