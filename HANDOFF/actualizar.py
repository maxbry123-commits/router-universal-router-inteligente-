#!/usr/bin/env python3
"""Regenera HANDOFF/TAREAS.md (sección automática) desde ramas abiertas, commits recientes
y BITACORA del state-hub, y sube copia a buckets/COMAND-CENTER-1/yaiwes-memoria-storage/handoff/.
Uso: python HANDOFF/actualizar.py [--sin-subir]
Env opcional: GITHUB_TOKEN (más cuota), HF_TOKEN (subida al bucket). Nunca imprime secretos.
También sirve como plugin/cron del Space: importar y llamar run()."""
import json, os, sys, urllib.request, datetime, pathlib

REPO = "maxbry123-commits/router-universal-router-inteligente-"
BUCKET = "buckets/COMAND-CENTER-1/yaiwes-memoria-storage/handoff"
SEGUIDAS = ["memoria-audit", "orquestador-agentes", "panel-anclaje-v2", "constitucion-contrato",
            "tools-staff", "historial-persistente", "anclas-constitucion", "handoff-migracion"]
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

def ramas():
    filas = []
    for b in SEGUIDAS:
        try:
            c = gh(f"commits/{b}")
            cmp = gh(f"compare/main...{b}")
            filas.append(f"| `{b}` | {c['sha'][:10]} | {c['commit']['committer']['date'][:10]} | "
                         f"+{cmp.get('ahead_by','?')}/-{cmp.get('behind_by','?')} | "
                         f"{c['commit']['message'].splitlines()[0][:90]} |")
        except Exception as e:
            filas.append(f"| `{b}` | — | — | — | no existe o sin acceso ({type(e).__name__}) |")
    return filas

def commits(n=10):
    try:
        return [f"- {c['sha'][:10]} {c['commit']['committer']['date'][:10]} {c['commit']['message'].splitlines()[0][:100]}"
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
            out.append(f"- seq {e.get('seq')} {e.get('at','')[:16]} {e.get('task','')} {e.get('status','')}: "
                       f"{str(e.get('summary',''))[:120]} → next: {e.get('next','')}")
        return out
    except Exception as e:
        return [f"- (BITACORA no disponible: {type(e).__name__})"]

def run(subir=True):
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M (UTC-5)")
    auto = "\n".join([INI, f"## Estado automático ({ahora})", "", "### Ramas",
                      "| Rama | Último commit | Fecha | vs main (+/-) | Mensaje |", "|---|---|---|---|---|",
                      *ramas(), "", "### Últimos commits en main", *commits(), "",
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
