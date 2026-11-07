#!/usr/bin/env python3
"""Publicacion PARALELA de la rama limpia (D-135).

Por que: el empuje secuencial cuesta un viaje de ida y vuelta por tramo (con el lease
renovado en cada uno). Con un pack thin (sin --no-thin) el envio de cada tramo son solo
los objetos NUEVOS de ese tramo, y el servidor ya conoce la base (main-clean). Por eso
se pueden publicar tramos INDEPENDIENTES en paralelo, cada uno en una rama temporal, y
despues hacer UN solo empuje final a main-clean (el servidor ya tiene todos los objetos:
el pack final es practicamente vacio y el ref queda en el tip).

Ventajas: 3-6x mas rapido, mismo resultado, y el pack final verifica que la rama remota
coincide con el HEAD local.

Reglas: nada de --no-thin (manda el pack completo y GitHub responde 500); lease SIEMPRE
al sha remoto real; los objetos pequenos de cada rama temporal se borran al terminar;
nunca se toca main ni la etiqueta de seguridad desde aqui.
"""
import os, sys, subprocess, time, json, concurrent.futures

BRANCH = "main-clean"
TMP_PREFIX = "wiring-pub-"
NUM_SEGMENTS = int(os.environ.get("SEGMENTS", "5"))
CHUNK = int(os.environ.get("SEGMENT_COMMITS", "400"))
UMBRAL_KIB = int(os.environ.get("UMBRAL_KIB", "1500000"))
GITOPT = ["-c", "http.version=HTTP/1.1", "-c", "http.postBuffer=524288000",
          "-c", "http.lowSpeedLimit=0", "-c", "http.lowSpeedTime=999999"]


def sh(args, cwd=".", check=False):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{r.stderr}")
    return r


def ls_remote_sha(repo, branch):
    r = sh(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=repo)
    return r.stdout.split()[0] if r.stdout.strip() else ""


def main():
    repo = os.environ.get("REPO_DIR", "/workspace/work/repo-live")
    sh(["git", "config", "gc.auto", "0"], cwd=repo, check=False)
    sh(["git", "config", "gc.pruneExpire", "never"], cwd=repo, check=False)
    sh(["git", "fetch", "origin", "--prune"], cwd=repo, check=False)
    remote = ls_remote_sha(repo, BRANCH)
    head = sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    have = bool(remote) and sh(["git", "cat-file", "-e", remote], cwd=repo).returncode == 0
    ancestor = have and sh(["git", "merge-base", "--is-ancestor", remote, "HEAD"], cwd=repo).returncode == 0
    if remote and ancestor:
        pending = sh(["git", "rev-list", "--reverse", f"{remote}..HEAD"], cwd=repo).stdout.split()
        print(f"Base remota: {remote[:12]} | pendientes: {len(pending)}", flush=True)
    else:
        pending = sh(["git", "rev-list", "--reverse", "HEAD"], cwd=repo).stdout.split()
        print(f"Rama nueva (divergencia): se publican {len(pending)} commits; "
              f"lease = sha remoto real {remote[:12]}", flush=True)
    if not pending:
        print("No hay commits pendientes.")
        return 0

    # Segmentos contiguos
    segs = []
    step = max(1, len(pending) // NUM_SEGMENTS)
    i = 0
    while i < len(pending):
        segs.append(pending[i:i + step])
        i += step
    print(f"{len(segs)} segmentos de hasta {CHUNK} commits", flush=True)

    def publicar(idx_seg):
        seg = segs[idx_seg]
        tmp = f"{TMP_PREFIX}{idx_seg}"
        # D-136: la rama temporal puede quedar de una vuelta anterior -> se borra antes
        # (son ramas mias y temporales) y el lease vacio vuelve a ser valido.
        sh(["git", "push", "origin", "--delete", tmp], cwd=repo, check=False)
        pos = 0
        while pos < len(seg):
            trozo = seg[pos:pos + CHUNK]
            tip = trozo[-1]
            r = sh(["git"] + GITOPT + ["push", "origin", f"{tip}:refs/heads/{tmp}",
                                       "--force-with-lease=refs/heads/{tmp}:"], cwd=repo)
            if r.returncode == 0:
                pos += len(trozo)
                continue
            # D-136: si el tramo es demasiado pesado, se reduce a la mitad y se reintenta.
            if len(trozo) > 1:
                CHUNK_LOCAL = max(1, len(trozo) // 2)
                seg = seg[:pos] + seg[pos:pos + CHUNK_LOCAL] + seg[pos + CHUNK_LOCAL:]
                print(f"  segmento {idx_seg}: tramo pesado -> reduzco a {CHUNK_LOCAL}", flush=True)
                continue
            return (idx_seg, False, (r.stdout + r.stderr)[-200:])
        return (idx_seg, True, f"{tmp} -> {seg[-1][:12]}")

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(NUM_SEGMENTS, 6)) as ex:
        for idx_seg, ok, det in ex.map(publicar, range(len(segs))):
            print(f"  segmento {idx_seg}: {'OK' if ok else 'FALLO'} {det}", flush=True)
    print(f"Segmentos en {int(time.time()-t0)} s", flush=True)

    # Empuje final: la rama real al HEAD. El servidor ya tiene los objetos (thin pack vacio).
    lease = ls_remote_sha(repo, BRANCH)
    lease_arg = f"refs/heads/{BRANCH}:{lease}" if lease else f"refs/heads/{BRANCH}:"
    r = sh(["git"] + GITOPT + ["push", "origin", f"HEAD:refs/heads/{BRANCH}",
                               f"--force-with-lease={lease_arg}"], cwd=repo)
    print(("Empuje final OK" if r.returncode == 0 else "Empuje final FALLO: " + (r.stdout + r.stderr)[-300:]), flush=True)
    if r.returncode != 0:
        return 1
    # Limpieza de las ramas temporales (mias)
    for idx_seg in range(len(segs)):
        sh(["git", "push", "origin", "--delete", f"{TMP_PREFIX}{idx_seg}"], cwd=repo, check=False)
    final = ls_remote_sha(repo, BRANCH)
    print(json.dumps({"ok": final == head, "head": head, "remote": final}))
    return 0 if final == head else 1


if __name__ == "__main__":
    sys.exit(main())
