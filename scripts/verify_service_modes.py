"""verify_service_modes.py — Verificacion local de Op2 (sin red salvo HF reads).

V1 AST de los 5 ficheros tocados.
V2 Import REAL del proxy (ROUTER_API_KEY dummy) -> rutas registradas y lifespan.
V3 Motor del loop: "python3 -m router_llm_hf.loop_engine" -> JSON valido.
V4 Detector: 12 modos de codigo + 4 de servicio.
V5 Routing SWE CODE free: /v1/swe-free debe pegarle al Space del Grupo 2 con
   el modelo del modo (Space simulado, cero llamadas a providers).

Salida: una linea por gate + "OP2_VERIFY_OK" si todo pasa (exit 1 si algo falla).
"""
import ast
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROXY_DIR = os.path.join(ROOT, "ROUTER MVP v1", "system_prompt_py")
FILES = [
    "router_llm_hf/service_routes.py",
    "router_llm_hf/loop_engine.py",
    "router_llm_hf/mode_detector.py",
    "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
    "scripts/fix_service_modes.py",
]

CODE_PROMPTS = {
    "code_refactor": "refactoriza el modulo de facturacion",
    "code_debug": "debug del error de autenticacion",
    "code_review": "revisa el pull request de la API",
    "code_generate": "implementa una funcion que valida el dni",
    "architecture": "diseña la arquitectura del sistema",
    "reasoning": "razona por que falla el pool de conexiones",
    "tool_call": "llama a la herramienta API de pagos",
    "planning": "plan de fases para migrar el router",
    "documentation": "documenta la funcion con un README",
    "frontend": "crea la interfaz del boton en React",
    "3d_code": "modelo 3D en Blender",
    "verification": "verifica con un test unitario",
}

SERVICE_PROMPTS = {
    "swe_code": "hazme un swe code del modulo",
    "swe_free": "usa swe free para esto",
    "team_qwe": "lanzalo con team qwe",
    "deployment": "despliega el servicio con kubernetes",
}

FAILS = []


def check(gate, ok, detail=""):
    print("{}_{}: {}".format(gate, "OK" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(gate)


def v1_ast():
    for f in FILES:
        try:
            ast.parse(open(os.path.join(ROOT, f), encoding="utf-8").read())
        except SyntaxError as exc:
            check("V1", False, "{}: {}".format(f, exc))
            return
    check("V1", True, "AST 5/5")


def v2_import():
    os.environ["ROUTER_API_KEY"] = "dummy"
    os.environ.setdefault("NVIDIA_KEYS", "")
    os.environ.setdefault("GROQ_KEYS", "")
    sys.path.insert(0, ROOT)
    sys.path.insert(0, PROXY_DIR)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "proxy_under_test", os.path.join(PROXY_DIR, "openai_compatible_proxy.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:
        check("V2", False, "import fallo: {}: {}".format(type(exc).__name__, exc))
        return None
    paths = {getattr(r, "path", "") for r in mod.app.routes}
    need = [
        "/v1/nvidia", "/v1/groq", "/v1/swe", "/v1/swe-free", "/v1/team-qwe",
        "/v1/deployment", "/v1/chat/completions", "/v1/modes", "/v1/agents",
        "/v1/loop/config", "/v1/loop/start", "/v1/loop/step", "/v1/loop/error",
        "/health",
    ]
    missing = [p for p in need if p not in paths]
    check("V2", not missing, "14 rutas, faltan: {}".format(missing) if missing else "14/14 rutas + lifespan ok")
    check("V2b", mod.app.router.lifespan_context is not None, "lifespan registrado")
    return mod


def v3_loop_engine():
    cmd = [sys.executable, "-m", "router_llm_hf.loop_engine",
           json.dumps({"input": "refactoriza el codigo", "iteration": 1})]
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    ok = proc.returncode == 0
    payload = {}
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        ok = False
    check("V3", ok and "done" in payload and "mode" in payload,
          "rc={} out={}".format(proc.returncode, proc.stdout.strip()[:160]))
    bad = subprocess.run(
        [sys.executable, "-m", "router_llm_hf.loop_engine", "{no-json"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    try:
        err = json.loads(bad.stdout.strip().splitlines()[-1])
        ok2 = bad.returncode == 2 and "error" in err
    except Exception:
        ok2 = False
    check("V3b", ok2, "payload roto -> rc=2 + JSON de error")


def v4_detector():
    from router_llm_hf.mode_detector import detect_mode, detect_service_route
    bad = []
    for mode, prompt in CODE_PROMPTS.items():
        got = detect_mode(prompt)
        if got != mode:
            bad.append("{}->{}".format(mode, got))
    check("V4", not bad, "12/12 modos de codigo" if not bad else "fallos: {}".format(bad))
    bad2 = []
    for mode, prompt in SERVICE_PROMPTS.items():
        got = detect_service_route(prompt)
        if got != mode:
            bad2.append("{}->{}".format(mode, got))
    check("V4b", not bad2, "4/4 modos de servicio" if not bad2 else "fallos: {}".format(bad2))


def v5_routing(mod):
    from fastapi.testclient import TestClient

    calls = []

    class FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"role": "assistant", "content": "pong"}}]}

    class FakeClient:
        async def post(self, url, headers=None, json=None, timeout=None):
            calls.append((url, json))
            return FakeResp()

    mod.provider_fb.client = FakeClient()
    client = TestClient(mod.app)
    r = client.post("/v1/swe-free",
                    headers={"x-api-key": "dummy"},
                    json={"messages": [{"role": "user", "content": "refactoriza el modulo"}],
                          "model": "auto"})
    ok = r.status_code == 200
    body = r.json() if ok else {}
    hit = calls[0] if calls else ("", {})
    ok = ok and body.get("service_mode") == "swe_free" and body.get("provider") == "hf_local" \
        and "swe-code-s3" in hit[0] and hit[1].get("model") == "unsloth/Qwen3.5-0.8B-GGUF"
    check("V5", ok, "swe-free -> {} modelo={} provider={}".format(
        hit[0].split("/")[2] if hit[0] else "-", hit[1].get("model"), body.get("provider")))

    calls.clear()
    r2 = client.post("/v1/swe",
                     headers={"x-api-key": "dummy"},
                     json={"messages": [{"role": "user", "content": "swe code del repo"}],
                           "model": "auto"})
    hit2 = calls[0] if calls else ("", {})
    ok2 = r2.status_code == 200 and r2.json().get("service_mode") == "swe_code" \
        and "swe-code-s1" in hit2[0] and hit2[1].get("model") == "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF"
    check("V5b", ok2, "swe -> {} modelo={}".format(
        hit2[0].split("/")[2] if hit2[0] else "-", hit2[1].get("model")))

    calls.clear()
    r3 = client.post("/v1/team-qwe",
                     headers={"x-api-key": "dummy"},
                     json={"messages": [{"role": "user", "content": "team qwe del proyecto"}],
                           "model": "auto"})
    body3 = r3.json() if r3.status_code in (200, 503) else {}
    # Sin claves en el entorno no hay proveedor: 503 CON diag es la respuesta
    # correcta (fail-closed). Lo que NO debe pasar es una llamada a un Space local.
    ok3 = (r3.status_code in (200, 503)
           and body3.get("service_mode") == "team_qwe"
           and not calls
           and (r3.status_code == 200 or "diag" in body3))
    check("V5c", ok3, "team-qwe -> proveedores (0 llamadas locales) status={} provider={} body={}".format(
        r3.status_code, body3.get("provider"), str(body3)[:160]))

    r4 = client.post("/v1/swe-free", headers={"x-api-key": "mala"}, json={"messages": []})
    check("V5d", r4.status_code == 401, "clave mala -> 401")


def main():
    v1_ast()
    mod = v2_import()
    if mod is None:
        print("OP2_VERIFY_FAIL")
        sys.exit(1)
    v3_loop_engine()
    v4_detector()
    v5_routing(mod)
    if FAILS:
        print("OP2_VERIFY_FAIL {}".format(FAILS))
        sys.exit(1)
    print("OP2_VERIFY_OK")


if __name__ == "__main__":
    main()
