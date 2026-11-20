"""Adapter aislado Qwen -> JSON seguro -> Blender; no modifica router ni Blender upstream.

Python >= 3.10, solo libreria estandar. Un adapter de ejemplo, NO un sistema
publico de ejecucion de codigo. El bridge del autor requiere archivos JSON
confiables: esta capa rechaza `exec`, rutas externas y operaciones arbitrarias.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib import request, error

SYSTEM_PROMPT = """Eres PLANIFICADOR DECLARATIVO DE ESCENAS, no ejecutor.
Tu unica salida es JSON puro, sin bloques Markdown, comentarios ni prosa.
Forma: {"meta":{"name":"nombre_simple"},"ops":[...]}
Usa exclusivamente estas operaciones declarativas, siguiendo el contrato:
new_scene, set_world, add_material, add_mesh, assign_material,
add_light, add_camera, track_to, set_render, render, save.
Debe haber suelo (plane), al menos otros dos meshes diferentes,
materiales, una luz, una camara activa y render EEVEE.
Comienza con new_scene. Termina en orden render y luego save.
Rutas exactas: ${PROJECT_ROOT}/output/ai_scene.png y
${PROJECT_ROOT}/output/ai_scene.blend.
No inventes operaciones: NO exec, load_blend, delete, shell, archivos Python.
Primitivas permitidas: cube, plane, uv_sphere, ico_sphere, torus.
set_render: engine=BLENDER_EEVEE, width<=1280, height<=720, scale=1.0.
En posiciones y rotaciones usa listas de 3 numeros; rotaciones en grados.
No incluyas texto de instalacion ni instrucciones para modificar el router.
Si no puedes cumplir, devuelve {"meta":{"name":"blocked"},"ops":[]}.
"""

ALLOWED = {
    "new_scene", "set_world", "add_material", "add_mesh", "assign_material",
    "add_light", "add_camera", "track_to", "set_render", "render", "save",
}
KINDS = {"cube", "plane", "uv_sphere", "ico_sphere", "torus"}
OUTPUTS = {
    "render": "${PROJECT_ROOT}/output/ai_scene.png",
    "save": "${PROJECT_ROOT}/output/ai_scene.blend",
}
# Limitar claves evita introducir parametros inesperados en bpy mediante la LLM.
KEYS = {
    "new_scene": {"op"},
    "set_world": {"op", "color", "strength"},
    "add_material": {"op", "name", "color", "metallic", "roughness", "emission_color", "emission_strength"},
    "add_mesh": {"op", "kind", "name", "location", "rotation", "scale", "size", "radius", "segments", "ring_count", "material", "smooth"},
    "assign_material": {"op", "material", "objects"},
    "add_light": {"op", "kind", "name", "location", "rotation", "energy", "color", "radius"},
    "add_camera": {"op", "name", "location", "rotation", "lens"},
    "track_to": {"op", "object", "location", "empty"},
    "set_render": {"op", "engine", "width", "height", "scale", "film_transparent"},
    "render": {"op", "path", "format", "color_mode"},
    "save": {"op", "path"},
}


def parse_model_json(answer: str) -> dict:
    """Recuperar respuesta JSON; texto extra es un fallo, no se ejecuta."""
    stripped = answer.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("La respuesta debe ser un objeto JSON")
    return parsed


def _vector(value, name):
    if not isinstance(value, list) or len(value) != 3 or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) or abs(x) > 1000
        for x in value
    ):
        raise ValueError(f"Vector de 3 numeros invalido: {name}")


def validate_scene(doc: dict) -> dict:
    """Validacion sin efectos secundarios: no confiar en texto generado."""
    if set(doc) - {"meta", "ops"}:
        raise ValueError("Campos desconocidos en documento")
    if "meta" in doc and not isinstance(doc["meta"], dict):
        raise ValueError("meta debe ser objeto")
    ops = doc.get("ops")
    if not isinstance(ops, list) or not (8 <= len(ops) <= 64):
        raise ValueError("La escena requiere entre 8 y 64 operaciones")
    names = []
    mats = set()
    kinds = []
    has_light = has_camera = has_render_settings = False
    for idx, item in enumerate(ops):
        if not isinstance(item, dict):
            raise ValueError(f"Operacion {idx} no es objeto")
        op = item.get("op")
        if op not in ALLOWED or set(item) - KEYS[op]:
            raise ValueError(f"Operacion o argumentos prohibidos en {idx}: {op}")
        if op == "new_scene" and idx != 0:
            raise ValueError("new_scene solo puede ir primero")
        for key in ("location", "rotation", "scale"):
            if key in item and not (op == "set_render" and key == "scale"):
                _vector(item[key], f"ops[{idx}].{key}")
        if op == "add_material":
            if not isinstance(item.get("name"), str) or not item["name"].isidentifier():
                raise ValueError("Nombre de material no seguro")
            mats.add(item["name"])
        if op == "add_mesh":
            if item.get("kind") not in KINDS:
                raise ValueError("Primitiva de mesh invalida")
            if not isinstance(item.get("name"), str) or not item["name"].isidentifier():
                raise ValueError("Nombre de mesh no seguro")
            if item["name"] in names:
                raise ValueError("Nombres de mesh duplicados")
            names.append(item["name"])
            kinds.append(item["kind"])
            if "material" in item and item["material"] not in mats:
                raise ValueError("Material de mesh no definido antes")
        if op == "assign_material" and item.get("material") not in mats:
            raise ValueError("Material asignado inexistente")
        if op == "add_light":
            if item.get("kind") not in {"point", "sun", "spot", "area"}:
                raise ValueError("Tipo de luz no admitido")
            has_light = True
        if op == "add_camera":
            has_camera = True
        if op == "set_render":
            has_render_settings = True
            if item.get("engine") != "BLENDER_EEVEE" or item.get("scale") != 1.0:
                raise ValueError("Motor o escala de render incorrectos")
            w, h = item.get("width"), item.get("height")
            if any(isinstance(x, bool) or not isinstance(x, int) for x in (w, h)):
                raise ValueError("Resolucion invalida")
            if not (320 <= w <= 1280 and 240 <= h <= 720):
                raise ValueError("Resolucion fuera del presupuesto")
        if op in OUTPUTS and item.get("path") != OUTPUTS[op]:
            raise ValueError("Ruta de salida no autorizada")
        if op == "render" and (item.get("format", "PNG") != "PNG"):
            raise ValueError("El formato de render debe ser PNG")
        if op == "save" and idx != len(ops) - 1:
            raise ValueError("save debe ser ultimo")
    order = [x["op"] for x in ops]
    if order[0] != "new_scene" or order[-2:] != ["render", "save"]:
        raise ValueError("El orden debe ser new_scene ... render, save")
    if order.count("render") != 1 or order.count("save") != 1:
        raise ValueError("Solo se admite un render y un save")
    if "plane" not in kinds or len(names) < 3 or len(set(kinds)) < 2:
        raise ValueError("Se requiere suelo y varios objetos diferenciados")
    if not (has_camera and has_light and has_render_settings and mats):
        raise ValueError("Faltan camara, luz, configuracion de render o materiales")
    return doc


def request_scene(prompt: str, base_url: str, model: str, api_key: str | None) -> dict:
    if not base_url.endswith("/v1"):
        raise ValueError("QWEN_BASE_URL debe acabar en /v1")
    if not model:
        raise ValueError("Falta QWEN_MODEL_ID; comprobar GET /v1/models")
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": prompt}],
        "temperature": 0.2, "top_p": 0.95,
        "max_tokens": 2600, "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = request.Request(base_url.rstrip("/") + "/chat/completions",
                          data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=180) as resp:
            reply = json.load(resp)
    except error.HTTPError as exc:
        raise RuntimeError(f"Servidor modelo HTTP {exc.code}") from exc
    text = reply["choices"][0]["message"]["content"]
    if not isinstance(text, str):
        raise ValueError("Respuesta de modelo no es texto JSON")
    return parse_model_json(text)


def execute_blender(doc: dict, project_root: Path, blender_bin: Path,
                    bridge_script: Path) -> dict:
    validate_scene(doc)
    if not blender_bin.is_file() or not bridge_script.is_file():
        raise FileNotFoundError("Falta ejecutable Blender o blender_cli.py de la fuente")
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "output").mkdir(exist_ok=True)
    scene_path = project_root / "scene_validada.json"
    scene_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    env = dict(os.environ, BLENDER_JSON_PROJECT_ROOT=str(project_root.resolve()))
    cmd = [str(blender_bin.resolve()), "--background", "--factory-startup",
           "--python", str(bridge_script.resolve()), "--", str(scene_path.resolve())]
    started = time.monotonic()
    completed = subprocess.run(cmd, cwd=project_root, env=env, capture_output=True,
                               text=True, timeout=300, check=False)
    logs = completed.stdout + "\n" + completed.stderr
    markers = [line.split("BLENDER_CLI_REPORT ", 1)[1]
               for line in logs.splitlines() if "BLENDER_CLI_REPORT " in line]
    report = json.loads(markers[-1]) if markers else {"ok": False, "errors": ["NO_REPORT"]}
    wanted = [project_root / "output" / "ai_scene.png", project_root / "output" / "ai_scene.blend"]
    output_ok = all(p.is_file() and p.stat().st_size > 0 for p in wanted)
    return {
        "ok": completed.returncode == 0 and report.get("ok") is True and output_ok,
        "returncode": completed.returncode, "elapsed_s": round(time.monotonic() - started, 2),
        "blender_report": report,
        "artifacts": [{"path": str(p), "bytes": p.stat().st_size if p.exists() else 0}
                      for p in wanted],
        "log_tail": logs[-3000:],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="Crea una escena 3D de un laboratorio IA con suelo, tres objetos, luces y camara")
    ap.add_argument("--input-json", help="Usar escena preparada, sin llamar a Qwen")
    ap.add_argument("--project-root", default="./qwen_blender_job")
    ap.add_argument("--execute", action="store_true", help="Ejecutar Blender una vez validado")
    ap.add_argument("--blender-bin", default=os.getenv("BLENDER_BINARY", ""))
    ap.add_argument("--bridge", default=os.getenv("BLENDER_CLI_PATH", ""))
    args = ap.parse_args()
    project_root = Path(args.project_root).resolve()
    try:
        if args.input_json:
            doc = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        else:
            doc = request_scene(args.task, os.getenv("QWEN_BASE_URL", "http://127.0.0.1:8080/v1"),
                                os.getenv("QWEN_MODEL_ID", ""), os.getenv("QWEN_API_KEY"))
        validate_scene(doc)
        project_root.mkdir(parents=True, exist_ok=True)
        plan_path = project_root / "scene_validada.json"
        plan_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        result = {"ok": True, "state": "VALIDATED_NOT_EXECUTED", "ops": len(doc["ops"]),
                  "scene": str(plan_path), "scene_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest()}
        if args.execute:
            result = execute_blender(doc, project_root, Path(args.blender_bin), Path(args.bridge))
            result["state"] = "EXECUTED" if result["ok"] else "FAILED"
            result["scene_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        receipt = project_root / "receipt.json"
        receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    except Exception as exc:
        fail = {"ok": False, "state": "REJECTED", "error": str(exc)}
        print(json.dumps(fail, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
