#!/usr/bin/env python3
"""Publica main-clean por tramos, cortando por TAMAÑO REAL de pack (D-124).

Instrucciones aplicadas del auditor:
  1. medicion del pack por tramo (pack_size_between) — en UNA sola pasada con
     `git cat-file --batch-check` (Gap 4 aplicado de entrada: la version objeto a objeto
     es O(N) procesos y con 7,53 GiB agota el techo del job).
  2. corte por TAMANO, no por numero de commits: se miden los tramos candidatos y los que
     superan el umbral se subdividen hasta que caben (o hasta un commit suelto).
  3. `git fetch origin <rama>` antes de cada intento (refs remotas al dia).
  4. reintentos con backoff 15/30/60 s para errores TRANSITORIOS; los errores de tamano
     (500/sideband/disconnect) van directo a subdividir, sin esperar.
  5. `--no-thin` + HTTP/1.1 + postBuffer + sin lowSpeedLimit.
  6. verificacion final que distingue "remoto == HEAD" de "HEAD es ancestro del remoto".

El lease se renueva tras cada tramo publicado y el script es idempotente: al releerlo
continua desde donde se quedo el remoto.
"""
import os, sys, subprocess, time, json

# --- Helpers ---
def sh(args, cwd=".", check=False):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{r.stderr}")
    return r

def ls_remote_sha(repo, branch="main-clean"):
    r = sh(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=repo)
    return r.stdout.split()[0] if r.stdout.strip() else ""

def head_sha(repo):
    return sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

def pack_size_between(repo, base_sha, tip_sha):
    """Tamano (KiB) del pack de los objetos unicos entre base_sha y tip_sha.

    D-126 (Gap 4 del recetario): la version por enumeracion de objetos
    (`git rev-list --objects` + `cat-file` uno a uno) CUELGA este repo: el rango cubre
    1.625 commits sobre un arbol de 338.007 ficheros y la enumeracion produce decenas de
    millones de lineas, que desbordan la tuberia y dejan el proceso dormido sin avanzar.
    Aqui se mide el pack REAL en streaming (`git pack-objects --revs --stdout | wc -c`),
    que es lo que GitHub mide, sin almacenar nada en memoria.
    """
    rng = f"{base_sha}..{tip_sha}" if base_sha else tip_sha
    cmd = "git pack-objects --revs --stdout --delta-base-offset | wc -c"
    p = subprocess.run(cmd, shell=True, cwd=repo, input=rng + "\n", capture_output=True, text=True)
    try:
        return int(p.stdout.strip()) // 1024
    except ValueError:
        return 0

# --- Configuracion ---
REPO = os.environ.get("REPO_DIR", "/workspace/work/repo-live")
BRANCH = "main-clean"
NUM_PARTS = int(os.environ.get("NUM_PARTS", "8"))
REMOTE_START = os.environ.get("REMOTE_START", "")
UMBRAL_KIB = int(os.environ.get("UMBRAL_KIB", "1500000"))   # ~1,46 GiB, margen bajo los 2 GiB de GitHub
GITOPT = ["-c", "http.version=HTTP/1.1",
          "-c", "http.postBuffer=524288000",
          "-c", "http.lowSpeedLimit=0",
          "-c", "http.lowSpeedTime=999999"]

def es_error_de_tamano(msg):
    m = (msg or "").lower()
    return any(x in m for x in ("500", "sideband", "unexpected disconnect", "pack exceeds"))

# --- 1. Commits pendientes ---
# GAP-G7 (instruccion del auditor): el push se interpretaba como BORRADO porque el clon local
# no tenia la ref ni los objetos del remoto (`stale info` + `Invalid revision range`). La causa
# eran las refs remotas obsoletas, no una historia rota: basta con `fetch --prune` ANTES de
# calcular los pendientes. Ademas, si aun asi el remoto no fuera ancestro, la rama se trataria
# como nueva (todos los commits del HEAD) y el lease seria el sha remoto REAL (nunca vacio:
# el lease vacio significa "crear solo si no existe" y el remoto si existe).
# D-128/D-129: durante la publicacion NO se poda nada. Motivo medido: el propio `git push`
# dispara `git gc --auto`, y con la politica por defecto los objetos que solo cuelgan de una
# ref de seguimiento se podan; la ref `origin/main-clean` quedaba colgante ("Invalid revision
# range") y los commits publicados desaparecian del clon. Se desactivan el gc automatico y la
# poda, y la rama publicada se ancla ademas en una ref LOCAL.
#
# G7 (instruccion del auditor): el lease es SIEMPRE el sha remoto REAL (el lease vacio
# significa "crear solo si no existe" y la rama SI existe). Si el remoto no es ancestro del
# HEAD (divergencia), la rama se trata como NUEVA y se publican todos los commits del HEAD.
sh(["git", "config", "gc.auto", "0"], cwd=REPO, check=False)
sh(["git", "config", "gc.pruneExpire", "never"], cwd=REPO, check=False)
sh(["git", "fetch", "origin", "--prune"], cwd=REPO, check=False)
remote_sha = REMOTE_START or ls_remote_sha(REPO)
have = bool(remote_sha) and sh(["git", "cat-file", "-e", remote_sha], cwd=REPO).returncode == 0
ancestor = have and sh(["git", "merge-base", "--is-ancestor", remote_sha, "HEAD"], cwd=REPO).returncode == 0
if remote_sha and ancestor:
    commits = sh(["git", "rev-list", "--reverse", f"{remote_sha}..HEAD"], cwd=REPO).stdout.split()
else:
    commits = sh(["git", "rev-list", "--reverse", "HEAD"], cwd=REPO).stdout.split()
    print(f"AVISO: remoto no ancestro del HEAD (divergencia G7). Se publica la rama como NUEVA: "
          f"{len(commits)} commits. Lease = sha remoto real.")
if not commits:
    print("No hay commits pendientes: main-clean ya esta actualizado.")
    sys.exit(0)

lease = remote_sha
part_num = 0
# D-132 (paso 3 del auditor: cortar por TAMANO REAL de pack): el bug anterior era que al
# subdividir se seguia empujando el FINAL del tramo, de modo que el rango desde el ultimo
# lease NUNCA se reducia (y el pack enviado seguia siendo de GiB). Aqui, en cada paso:
#   1) se mide el pack de un prefijo candidato (pack-objects en streaming, que es lo que
#      mide GitHub), 2) se empuja el MAYOR prefijo que cabe bajo el umbral, 3) el lease
#      avanza a ese commit y se repite con el resto.
rest = list(commits)
while rest:
    part_num += 1
    # D-133: con CHUNK_COMMITS fijo NO se mide (la medicion del RANGE acumulado engaña:
    # incluye los objetos que el remoto ya tiene y por eso crecia hasta GiB). El pack real
    # que viaja en cada empuje son los objetos NUEVOS de ese prefijo, y con el lease
    # renovandose por prefijo el avance es monotono y seguro. Sin CHUNK_COMMITS se usa el
    # corte por medicion (paso 3 del auditor).
    fijo = int(os.environ.get("CHUNK_COMMITS", "0"))
    if fijo > 0:
        n = min(fijo, len(rest)); kib = 0
    else:
        n = max(1, min(len(rest), int(len(rest) * 0.12)))
        kib = pack_size_between(REPO, lease if lease else "", rest[n - 1])
        guard = 0
        while kib > UMBRAL_KIB and n > 1 and guard < 12:
            n = max(1, n // 2)
            kib = pack_size_between(REPO, lease if lease else "", rest[n - 1])
            guard += 1
    print(f"\nParte {part_num} - prefijo de {n} commits - pack~{kib/1024:.1f} MiB - tip={rest[n-1][:12]}", flush=True)
    current_part = rest[:n]
    attempt = 0
    published = False
    while current_part:
        attempt += 1
        sh(["git", "fetch", "origin", BRANCH], cwd=REPO, check=False)
        try:
            lease_arg = f"refs/heads/{BRANCH}:{lease}" if lease else f"refs/heads/{BRANCH}:"
            # D-134: SIN --no-thin. Medido: con --no-thin git envia el pack COMPLETO (7,53 GiB
            # de historia) en vez de solo los objetos nuevos, y GitHub lo rechaza con HTTP 500
            # en TODOS los empujes (incluso de 1,6 MB). Con pack thin (por defecto) el envio
            # son solo los objetos nuevos y el empuje se acepta.
            r = sh(["git"] + GITOPT + ["push", "origin", f"{current_part[-1]}:refs/heads/{BRANCH}",
                                      f"--force-with-lease={lease_arg}"], cwd=REPO)
            if r.returncode == 0:
                lease = current_part[-1]
                print(f"   Publicado {current_part[-1][:12]} ({len(current_part)} commits)", flush=True)
                published = True
                break
            err = (r.stdout + r.stderr)
            print("   ERROR DE GIT:", " | ".join(x for x in err.splitlines() if x.strip())[-300:])
            if not es_error_de_tamano(err) and attempt <= 3:
                wait = 15 * (2 ** (attempt - 1))
                print(f"   Error transitorio. Reintento en {wait}s ({attempt}/3)")
                time.sleep(wait)
                continue
            # error de tamano: se reduce el prefijo a la mitad
            if len(current_part) == 1:
                sha = current_part[0]
                size_kib = pack_size_between(REPO, lease if lease else "", sha)
                print(f"   FALLO del commit {sha[:12]} - pack~{size_kib/1024:.1f} MiB")
                print(f"      git ls-tree -r --long {sha} | sort -k4 -n | tail -20")
                sys.exit(1)
            current_part = current_part[:max(1, len(current_part) // 2)]
            print(f"   Reduciendo el prefijo a {len(current_part)} commits")
        except Exception as e:
            print(f"   Error inesperado: {e}")
            sys.exit(1)
    if not published:
        sys.exit(1)
    rest = rest[len(current_part):]

# --- 4. Verificacion final ---
final_remote = ls_remote_sha(REPO)
final_head = head_sha(REPO)
if final_remote == final_head:
    print(f"\nmain-clean remoto == HEAD ({final_head[:12]})")
    print(json.dumps({"ok": True, "head": final_head, "parts": part_num}))
elif sh(["git", "merge-base", "--is-ancestor", final_head, final_remote], cwd=REPO).returncode == 0:
    print(f"\nmain-clean remoto ({final_remote[:12]}) tiene commits extra; HEAD es ancestro.")
    print(json.dumps({"ok": True, "head": final_head, "remote": final_remote, "extra": True}))
else:
    print(f"\nDISCREPANCIA: remoto={final_remote[:12]} head={final_head[:12]}")
    sys.exit(1)
