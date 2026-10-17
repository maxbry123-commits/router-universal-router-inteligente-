#!/usr/bin/env python3
"""Regenera HANDOFF/TAREAS.md (sección automática) desde ramas abiertas, commits recientes
y BITACORA del state-hub, y sube copia a buckets/COMAND-CENTER-1/yaiwes-memoria-storage/handoff/.
Uso: python HANDOFF/actualizar.py [--sin-subir]
Env opcional: GITHUB_TOKEN (más cuota), HF_TOKEN (subida al bucket). Nunca imprime secretos.
También sirve como plugin/cron del Space: importar y llamar run()."""
import json, os, sys, urllib.request, datetime, pathlib

REPO = "maxbry123-commits/router-universal-router-inteligente-"
BUCKET = "buckets/COMAND-CENTER-1/yaiwes-memoria-storage/handoff"
VENTANA_H = int(os.getenv("HANDOFF_VENTANA_H", "48"))  # ramas con push en las últimas N horas
BOGOTA = datetime.timezone(datetime.timedelta(hours=-5), "UTC-5")
AQUI = pathlib.Path(__file__).resolve().parent
BITACORA = AQUI.parent / "chat router" / "03-ESTADO" / "BITACORA.jsonl"
INI, FIN = "<!-- AUTO:INICIO -->", "<!-- AUTO:FIN -->"

def gh(path):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}",
                                 headers={"Accept": "application/vnd.github+json"})
    if os.getenv("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def bog(iso):
    """ISO UTC de GitHub -> 'AAAA-MM-DD HH:MM' en America/Bogota (UTC-5)."""
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BOGOTA).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(iso)[:16]

def ramas_activas():
    """Ramas reales con push reciente (API de actividad), sin main; luego solo las que van por delante de main."""
    corte = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=VENTANA_H)
    vistas = {}
    for e in gh("activity?per_page=100&time_period=week"):
        ref = e.get("ref", "")
        if not ref.startswith("refs/heads/") or ref == "refs/heads/main":
            continue
        t = datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        if t >= corte:
            vistas[ref[11:]] = max(t, vistas.get(ref[11:], t))
    return [b for b, _ in sorted(vistas.items(), key=lambda x: x[1], reverse=True)]

def ramas():
    filas = []
    try:
        lista = ramas_activas()
    except Exception as e:
        return [f"| — | — | — | — | sin acceso a la API de actividad ({type(e).__name__}) |"]
    tope = None if os.getenv("GITHUB_TOKEN") else int(os.getenv("HANDOFF_TOPE", "15"))  # cuota sin token: 60/h
    corte = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=VENTANA_H)
    omitidas = 0
    for b in lista[:tope]:
        try:
            c = gh(f"commits/{b}")
            fecha = datetime.datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
            if fecha < corte:
                continue  # push reciente pero sin commits nuevos (rama vieja re-subida)
            cmp = gh(f"compare/main...{b}")
            if not cmp.get("ahead_by"):
                continue  # ya fusionada en main
            filas.append(f"| `{b}` | {c['sha'][:10]} | {bog(c['commit']['committer']['date'])} | "
                         f"+{cmp.get('ahead_by','?')}/-{cmp.get('behind_by','?')} | "
                         f"{c['commit']['message'].splitlines()[0][:90]} |")
        except Exception:
            omitidas += 1
    if omitidas or (tope and len(lista) > tope):
        filas.append(f"| … | — | — | — | {omitidas} sin acceso y {max(0, len(lista) - (tope or len(lista)))} sin revisar (define GITHUB_TOKEN) |")
    return filas

def commits(n=10):
    try:
        return [f"- {c['sha'][:10]} {bog(c['commit']['committer']['date'])} {c['commit']['message'].splitlines()[0][:100]}"
                for c in gh(f"commits?sha=main&per_page={n}")]
    except Exception as e:
        return [f"- (sin acceso a GitHub: {type(e).__name__})"]

def bitacora(n=8):
    try:
        if BITACORA.exists():
            lineas = BITACORA.read_text(encoding="utf-8").strip().splitlines()
        else:
            url = f"https://raw.githubusercontent.com/{REPO}/main/chat%20router/03-ESTADO/BITACORA.jsonl"
            lineas = urllib.request.urlopen(url, timeout=20).read().decode().strip().splitlines()
        out = []
        for l in lineas[-n:]:
            e = json.loads(l)
            out.append(f"- seq {e.get('seq')} {bog(e.get('at',''))} {e.get('task','')} {e.get('status','')}: "
                       f"{str(e.get('summary',''))[:120]} → next: {e.get('next','')}")
        return out
    except Exception as e:
        return [f"- (BITACORA no disponible: {type(e).__name__})"]

def run(subir=True):
    ahora = datetime.datetime.now(BOGOTA).strftime("%Y-%m-%d %H:%M")
    auto = "\n".join([INI, f"## Estado automático ({ahora}, hora Bogotá UTC-5)", "", "### Ramas",
                      "| Rama | Último commit | Fecha (UTC-5) | vs main (+/-) | Mensaje |", "|---|---|---|---|---|",
                      *ramas(), "", "### Últimos commits en main (hora UTC-5)", *commits(), "",
                      "### BITACORA state-hub (últimos)", *bitacora(), FIN])
    f = AQUI / "TAREAS.md"
    txt = f.read_text(encoding="utf-8") if f.exists() else "# Tareas\n"
    txt = (txt.split(INI)[0] + auto + txt.split(FIN, 1)[1]) if INI in txt and FIN in txt else txt.rstrip() + "\n\n" + auto + "\n"
    f.write_text(txt, encoding="utf-8")
    print("TAREAS.md regenerado")
    if subir:
        if not os.getenv("HF_TOKEN"):
            print("HF_TOKEN ausente: no se sube al bucket"); return
        from huggingface_hub import HfFileSystem
        fs = HfFileSystem(token=os.environ["HF_TOKEN"])
        for nombre in ["README-HANDOFF.md", "ARQUITECTURA.md", "TAREAS.md", "PREFERENCIAS.md", "SECRETOS.md"]:
            p = AQUI / nombre
            if p.exists():
                fs.pipe_file(f"{BUCKET}/{nombre}", p.read_bytes())
        print(f"Subido a {BUCKET}/")

if __name__ == "__main__":
    run(subir="--sin-subir" not in sys.argv)
