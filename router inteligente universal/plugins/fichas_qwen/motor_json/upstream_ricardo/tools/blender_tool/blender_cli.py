# -*- coding: utf-8 -*-
"""Reusable command bridge for Blender (background mode).

Usage:
    blender.exe --background --python blender_cli.py -- <commands.json>

JSON format: a bare list of ops, or {"meta": {...}, "ops": [...]}.
Each op is {"op": "<name>", ...params...}. Angles are in DEGREES.

Ops: new_scene, load_blend, set_world, add_mesh, set_transform, add_material,
     assign_material, add_light, add_camera, add_empty, track_to, connect,
     neural_net, set_render, render, save, delete, exec.

Prints a final machine-readable line:  BLENDER_CLI_REPORT <json>
"""
import bpy
import fnmatch
import json
import math
import os
import sys
import time
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
COMMANDS_FILE = next((a for a in ARGS if not a.startswith("-")), None)
ERRORS = []
PROJECT_ROOT = os.path.abspath(
    os.environ.get(
        "BLENDER_JSON_PROJECT_ROOT",
        os.path.join(os.path.dirname(__file__), "..", ".."),
    )
)


def log(m):
    print("[blender_cli] " + str(m))


def fail(op, exc):
    ERRORS.append({"op": op, "error": repr(exc)})
    log("ERROR op '%s': %r" % (op, exc))


def vec(v, d=(0.0, 0.0, 0.0)):
    if v is None:
        return list(d)
    if isinstance(v, (int, float)):
        return [float(v)] * 3
    o = [float(x) for x in v]
    while len(o) < 3:
        o.append(0.0)
    return o[:3]


def expand_project_paths(value):
    """Expand portable project-root placeholders throughout a JSON document."""
    if isinstance(value, str):
        return value.replace("${PROJECT_ROOT}", PROJECT_ROOT.replace("\\", "/"))
    if isinstance(value, list):
        return [expand_project_paths(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_project_paths(item) for key, item in value.items()}
    return value


def scn():
    return bpy.context.scene


def link(o):
    if o.name not in scn().collection.objects:
        scn().collection.objects.link(o)
    return o


def uname(base):
    n, i = base, 2
    while n in bpy.data.objects:
        n = "%s_%d" % (base, i)
        i += 1
    return n


def xform(o, c):
    if "location" in c:
        o.location = vec(c["location"])
    if "rotation" in c:
        o.rotation_mode = "XYZ"
        o.rotation_euler = [math.radians(a) for a in vec(c["rotation"])]
    if "scale" in c:
        o.scale = vec(c["scale"], (1.0, 1.0, 1.0))


def smooth(o):
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass


def track_to(o, loc, en):
    t = bpy.data.objects.get(en)
    if t is None or t.type != "EMPTY":
        t = bpy.data.objects.new(uname(en), None)
    t.empty_display_size = 0.25
    link(t)
    t.location = vec(loc)
    for c in list(o.constraints):
        if c.type == "TRACK_TO":
            o.constraints.remove(c)
    c = o.constraints.new("TRACK_TO")
    c.target = t
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


def make_link(a, b, r, mat=None, verts=8):
    va, vb = Vector(a), Vector(b)
    d = vb - va
    if d.length < 1e-6:
        return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=float(r), depth=d.length, location=(va + vb) / 2.0)
    o = bpy.context.active_object
    o.name = uname("link")
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    if mat:
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials[mat])
    return o


def op_load_blend(c):
    path = c.get("path")
    if not path:
        fail("load_blend", RuntimeError("no 'path'"))
    bpy.ops.wm.open_mainfile(filepath=path)
    log("loaded %s" % path)


def op_new_scene(c):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    w = bpy.data.worlds.new("World")
    scn().world = w
    log("new scene ready")


def op_set_world(c):
    if scn().world is None:
        scn().world = bpy.data.worlds.new("World")
    w = scn().world
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg is not None and "color" in c:
        bg.inputs[0].default_value = [float(x) for x in c["color"]] + [1.0]
    if "strength" in c:
        bg.inputs[1].default_value = float(c["strength"])


def op_add_mesh(c):
    kind = c.get("kind", "cube")
    name = c.get("name") or uname(kind)
    p = {k: v for k, v in c.items() if k not in ("op", "kind", "name", "material", "smooth")}
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**p)
    o = bpy.context.active_object
    o.name = name
    xform(o, c)
    if c.get("material"):
        m = bpy.data.materials.get(c["material"])
        if m is None:
            fail(c.get("op", "add_mesh"), RuntimeError("missing material %r" % c["material"]))
        o.data.materials.clear()
        o.data.materials.append(m)
    if c.get("smooth"):
        smooth(o)
    log("added mesh %s" % name)


def op_set_transform(c):
    o = bpy.data.objects.get(c["name"])
    if o is None:
        fail(c.get("op", "set_transform"), RuntimeError("no object %r" % c["name"]))
    xform(o, c)
    log("transformed %s" % c["name"])


def op_add_material(c):
    name = c.get("name") or uname("Material")
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    n = m.node_tree.nodes
    lk = m.node_tree.links
    if bsdf is not None and "color" in c:
        bsdf.inputs["Base Color"].default_value = [float(x) for x in c["color"]] + [1.0]
    if "metallic" in c:
        bsdf.inputs["Metallic"].default_value = float(c["metallic"])
    if "roughness" in c:
        bsdf.inputs["Roughness"].default_value = float(c["roughness"])
    if "emission_color" in c or "emission_strength" in c:
        key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        if "emission_color" in c:
            bsdf.inputs[key].default_value = [float(x) for x in c["emission_color"]] + [1.0]
        if "emission_strength" in c:
            skey = "Emission Strength" if "Emission Strength" in bsdf.inputs else "Emission Strength"
            bsdf.inputs[skey].default_value = float(c["emission_strength"])
    if "alpha" in c:
        bsdf.inputs["Alpha"].default_value = float(c["alpha"])
        m.blend_method = "BLEND"
    log("material %s" % name)


def op_assign_material(c):
    m = bpy.data.materials.get(c["material"])
    if m is None:
        fail("assign_material", RuntimeError("no material %r" % c["material"]))
    for pat in c.get("objects", []):
        for o in bpy.data.objects:
            if fnmatch.fnmatch(o.name, pat) and o.type == "MESH":
                o.data.materials.clear()
                o.data.materials.append(m)
    log("assigned %s" % c["material"])


def op_add_light(c):
    kind = c.get("kind", "point")
    name = c.get("name") or uname(kind + "_light")
    light_type = {"point": "POINT", "sun": "SUN", "spot": "SPOT", "area": "AREA"}.get(kind)
    if light_type is None:
        fail("add_light", RuntimeError("unknown light kind %r" % kind))
    bpy.ops.object.light_add(type=light_type)
    o = bpy.context.active_object
    o.name = name
    xform(o, c)
    ld = o.data
    if "energy" in c:
        ld.energy = float(c["energy"])
    if "color" in c:
        ld.color = [float(x) for x in c["color"]]
    if kind == "point" and "radius" in c:
        ld.shadow_soft_size = float(c["radius"])
    if kind == "spot" and "spot_size" in c:
        ld.spot_size = math.radians(float(c["spot_size"]))
    log("light %s" % name)


def op_add_camera(c):
    name = c.get("name") or uname("Camera")
    bpy.ops.object.camera_add()
    o = bpy.context.active_object
    o.name = name
    xform(o, c)
    cd = o.data
    if "lens" in c:
        cd.lens = float(c["lens"])
    if "sensor_width" in c:
        cd.sensor_width = float(c["sensor_width"])
    if "dof" in c and c.get("dof", {}).get("focus_object"):
        cd.dof.use_dof = True
        fo = bpy.data.objects.get(c["dof"]["focus_object"])
        if fo is not None:
            cd.dof.aperture_fstop = float(c["dof"].get("fstop", 2.8))
    scn().camera = o
    log("camera %s" % name)


def op_add_empty(c):
    name = c.get("name") or uname("Empty")
    e = bpy.data.objects.new(name, None)
    link(e)
    xform(e, c)
    e.empty_display_size = float(c.get("size", 0.5))
    log("empty %s" % name)


def op_track_to(c):
    o = bpy.data.objects.get(c["object"])
    if o is None:
        fail("track_to", RuntimeError("no object %r" % c["object"]))
    track_to(o, c.get("location"), c.get("empty", "TrackTarget"))


def op_connect(c):
    a = vec(c["a"])
    b = vec(c["b"])
    r = float(c.get("radius", 0.02))
    mat = c.get("material")
    segs = max(1, int(c.get("segments", 1)))
    for i in range(segs):
        t0 = i / segs
        t1 = (i + 1) / segs
        pa = [a[k] + (b[k] - a[k]) * t0 for k in range(3)]
        pb = [a[k] + (b[k] - a[k]) * t1 for k in range(3)]
        make_link(pa, pb, r, mat)


def op_neural_net(c):
    layers = c.get("layers") or []
    if not layers:
        fail("neural_net", RuntimeError("empty layers list"))
    r = float(c.get("radius", 0.18))
    gap = float(c.get("gap", 1.0))
    mat_node = bpy.data.materials.get(c.get("node_material", "NN_Node"))
    mat_link = bpy.data.materials.get(c.get("link_material", "NN_Link"))
    base = c.get("base_name", "NN")
    pos = {}
    for li, count in enumerate(layers):
        n = int(count)
        h = (n - 1) * 0.6
        for ni in range(n):
            name = "%s_L%d_N%d" % (base, li, ni)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=r, location=(li * gap, -h + ni * 0.6, 0.0))
            o = bpy.context.active_object
            o.name = name
            smooth(o)
            if mat_node:
                o.data.materials.clear()
                o.data.materials.append(mat_node)
            pos[(li, ni)] = [li * gap, -h + ni * 0.6, 0.0]
    for li in range(len(layers) - 1):
        a, b = int(layers[li]), int(layers[li + 1])
        for i in range(a):
            targets = list(range(b)) if c.get("full", True) else [i % b]
            for j in targets:
                make_link(pos[(li, i)], pos[(li + 1, j)], float(c.get("link_radius", 0.015)), mat_link.name if mat_link else None, verts=6)
    log("neural net built: %d layers" % len(layers))


def _gpu():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for dt in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = dt
                prefs.get_devices()
                if any(d.type == dt for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = True
                    return dt
            except Exception:
                continue
    except Exception:
        pass
    return "CPU"


def op_set_render(c):
    s = scn()
    if c.get("engine"):
        s.render.engine = c["engine"]
    if "width" in c:
        s.render.resolution_x = int(c["width"])
    if "height" in c:
        s.render.resolution_y = int(c["height"])
    if "scale" in c:
        s.render.resolution_percentage = int(round(float(c["scale"]) * 100.0))
    if "samples" in c:
        s.cycles.samples = int(c["samples"])
    if "denoise" in c:
        s.cycles.use_denoising = bool(c["denoise"])
    if "device" in c:
        dev = c["device"]
        if dev != "CPU":
            got = _gpu()
            s.cycles.device = got if got != "CPU" else "CPU"
            log("cycles device -> %s" % s.cycles.device)
        else:
            s.cycles.device = "CPU"
    if "film_transparent" in c:
        s.render.film_transparent = bool(c["film_transparent"])
    if "view_transform" in c:
        s.view_settings.view_transform = c["view_transform"]
    log("render settings done")


def op_render(c):
    s = scn()
    path = c.get("path")
    if not path:
        fail("render", RuntimeError("no output 'path'"))
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    s.render.filepath = path
    fmt = (c.get("format") or "PNG").upper()
    if fmt == "JPEG":
        s.render.image_settings.file_format = "JPEG"
        s.render.image_settings.quality = float(c.get("quality", 90))
    else:
        s.render.image_settings.file_format = "PNG"
        s.render.image_settings.color_mode = c.get("color_mode", "RGBA")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    out = path if os.path.isfile(path) else s.render.filepath
    log("rendered %s in %.1fs" % (out, dt))


def op_save(c):
    path = c.get("path")
    if not path:
        fail("save", RuntimeError("no 'path'"))
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    log("saved %s" % path)


def op_delete(c):
    for pat in c.get("patterns", []):
        for o in list(bpy.data.objects):
            if fnmatch.fnmatch(o.name, pat):
                bpy.data.objects.remove(o, do_unlink=True)
    log("deleted per %r" % c.get("patterns"))


def op_exec(c):
    code = c.get("code") or ""
    g = {"bpy": bpy, "math": math, "Vector": Vector}
    exec(code, g)
    log("exec ok")


OPS = {
    "new_scene": op_new_scene,
    "load_blend": op_load_blend,
    "set_world": op_set_world,
    "add_mesh": op_add_mesh,
    "set_transform": op_set_transform,
    "add_material": op_add_material,
    "assign_material": op_assign_material,
    "add_light": op_add_light,
    "add_camera": op_add_camera,
    "add_empty": op_add_empty,
    "track_to": op_track_to,
    "connect": op_connect,
    "neural_net": op_neural_net,
    "set_render": op_set_render,
    "render": op_render,
    "save": op_save,
    "delete": op_delete,
    "exec": op_exec,
}


def main():
    if not COMMANDS_FILE:
        print("usage: blender --background --python blender_cli.py -- <commands.json>")
        print("BLENDER_CLI_REPORT " + json.dumps({"ok": False, "error": "no commands file"}))
        return 1
    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            doc = expand_project_paths(json.load(f))
    except Exception as e:
        print("BLENDER_CLI_REPORT " + json.dumps({"ok": False, "error": repr(e)}))
        return 1
    ops = doc.get("ops", []) if isinstance(doc, dict) else doc
    for c in ops:
        name = c.get("op")
        fn = OPS.get(name)
        if fn is None:
            fail(str(name), RuntimeError("unknown op"))
            continue
        try:
            fn(c)
        except Exception as e:
            fail(str(name), e)
    report = {
        "ok": not ERRORS,
        "ops_total": len(ops),
        "errors": ERRORS,
        "blender": bpy.app.version_string,
        "scene": bpy.context.scene.name,
    }
    print("BLENDER_CLI_REPORT " + json.dumps(report))
    return 0 if not ERRORS else 1


if __name__ == "__main__":
    sys.exit(main())
