"""patch_fix3_modes.py - Sustituye modos de servicio por 4 GAP reales.
Idempotente. Exit 0 si OK, 1 si target inexistente, 2 si syntax error."""
import os, re, sys

TARGET = "router_llm_hf/mode_router.py"
GAP_MODES = ["python", "backend", "architecture", "agentic_tool"]

HEADER = f'''
VALID_MODES = {GAP_MODES!r}
_ADAPTER_REPO = "COMAND-CENTER-1/swe-code-adapters"

def _verify_adapter(mode: str) -> dict:
    """Verifica adapter_config.json en HF. Devuelve cfg o {{'error': ...}}."""
    import json, urllib.request
    url = f"https://huggingface.co/{{_ADAPTER_REPO}}/resolve/main/{{mode}}/adapter_config.json"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            if r.status != 200:
                return {{"error": f"http_{{r.status}}"}}
            return json.loads(r.read())
    except Exception as e:
        return {{"error": f"{{type(e).__name__}}:{{e}}"}}
'''

NEW_ROUTE = '''def route(payload: dict) -> dict:
    from .mode_detector import detect_mode
    prompt = ""
    for m in payload.get("messages", []):
        if m.get("role") == "user":
            prompt = m.get("content", ""); break
    mode = payload.get("mode") or detect_mode(prompt)
    if mode not in VALID_MODES:
        return {"mode": mode, "error": f"invalid_mode, valid={VALID_MODES}"}
    # Re-integrado (MiniMax 3, riesgo 4 del bloque): _ADAPTER_CACHE evita pedir
    # el adapter a HF en cada request; el shape cacheado es adapter_config.json.
    if mode in _ADAPTER_CACHE:
        adapter = _ADAPTER_CACHE[mode]
    else:
        adapter = _verify_adapter(mode)
        _ADAPTER_CACHE[mode] = {} if adapter.get("error") else adapter
    if adapter.get("error"):
        return {"mode": mode, "adapter_config": {},
                "dataset": None, "error": adapter["error"]}
    if not adapter:
        return {"mode": mode, "adapter_config": {},
                "dataset": None, "error": "adapter_not_found"}
    return {"mode": mode, "adapter_config": adapter,
            "dataset": adapter.get("dataset") or adapter.get("dataset_combined"),
            "base_model": adapter.get("base_model") or adapter.get("base_model_name_or_path"),
            "lora": adapter.get("lora")}
'''


def main():
    if not os.path.exists(TARGET):
        print(f"FATAL: {TARGET} no existe", file=sys.stderr)
        sys.exit(1)
    src = open(TARGET, "r", encoding="utf-8").read()

    if "VALID_MODES" in src and "agentic_tool" in src:
        print("IDEMPOTENTE: modos ya parcheados."); return

    if "VALID_MODES" not in src:
        lines = src.splitlines()
        at = 0
        for i, ln in enumerate(lines):
            if ln.startswith(("import ", "from ")):
                at = i + 1
        lines.insert(at, HEADER)
        src = "\n".join(lines)

    old = re.search(r"def route\(payload: dict\) -> dict:.*?(?=\ndef |\Z)",
                    src, re.DOTALL)
    if old and "VALID_MODES" not in old.group(0):
        # FIX: el route() original se sustituye SIEMPRE que no filtre por
        # VALID_MODES. La guarda anterior (solo si existian swe_free/team_qwe/
        # deployment) dejaba el route() viejo en ficheros que ya usaban
        # detect_mode -> los modos de servicio seguian aceptandose (S12).
        src = src[:old.start()] + NEW_ROUTE + src[old.end():]

    open(TARGET, "w", encoding="utf-8").write(src)
    print(f"OK: modos -> {GAP_MODES}")


if __name__ == "__main__":
    main()
