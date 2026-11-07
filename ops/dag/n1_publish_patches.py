import os, sys, json, subprocess, pathlib, time
OUT = pathlib.Path("out/N1"); OUT.mkdir(parents=True, exist_ok=True)
if (OUT/"patches.json").exists(): sys.exit("N1: output exists, abort")
FILES = ["ops/j9_remirror.py","ops/wiring_check.py","connections/baseline_unresolved.json"]
res = {"checks": [], "files": FILES}
res["checks"].append({"name":"files_exist","ok":all(pathlib.Path(f).exists() for f in FILES)})
if not all(c["ok"] for c in res["checks"]):
    (OUT/"patches.json").write_text(json.dumps(res, indent=2)); sys.exit(1)
def sh(a): return subprocess.run(a, capture_output=True, text=True)
# D-154 (centinela G7/G3 + carrera real medida): otros agentes publican en main de forma
# continua, asi que el sha remoto cambia ENTRE la lectura del lease y el push. El motor
# original leia el lease una vez y empujaba (pudiendo REESCRIBIR main). Aqui se reintenta
# con lease RENOVADO sobre el sha remoto real leido en cada intento, y solo se publica si
# HEAD es ancestro del remoto (fast-forward) o si el remoto es ancestro de HEAD (se
# re-basa el indice sobre el remoto y se vuelve a intentar). Nunca se reescribe main.
res["checks"].append({"name":"files_exist","ok":all(pathlib.Path(f).exists() for f in FILES)})
if not all(c["ok"] for c in res["checks"]):
    (OUT/"patches.json").write_text(json.dumps(res, indent=2)); sys.exit(1)
sh(["git","add"]+FILES)
commit_ok=False; detail=""; attempts=[]
for intento in range(1,6):
    remote = sh(["git","ls-remote","origin","refs/heads/main"]).stdout.split()[0]
    res["lease"]=remote
    res["checks"].append({"name":"lease_read","ok":bool(remote),"detail":remote[:12]})
    if not remote:
        attempts.append({"intento":intento,"resultado":"lease vacio"}); time.sleep(3); continue
    anc=sh(["git","merge-base","--is-ancestor",remote,"HEAD"]).returncode==0
    if not anc:
        # el remoto AVANZO (otros agentes publican en main): se trae el remoto y se
        # realinea el puntero local + el indice sobre el. HEAD pasa a ser el remoto,
        # de modo que el commit que se cree encima es FAST-FORWARD. NO se reescribe main.
        sh(["git","fetch","origin","refs/heads/main:refs/remotes/origin/main"])
        sh(["git","update-ref","refs/heads/main","refs/remotes/origin/main"])
        sh(["git","read-tree","refs/remotes/origin/main"])
        sh(["git","add"]+FILES)
        anc=sh(["git","merge-base","--is-ancestor",remote,"HEAD"]).returncode==0
        if not anc:
            attempts.append({"intento":intento,"resultado":f"abortado: {remote[:12]} no es ancestro"}); time.sleep(5); continue
    # D-155: `git commit` recorre los 435.000 ficheros del working tree y en NFS se colgaba
    # (>9 min sin salida). Se usa la via INDEX-ONLY: commit-tree construye el commit a partir
    # del indice (que ya tiene los 3 parches staged) sin tocar el working tree. Mismo arbol,
    # mismo mensaje, mismo autor.
    tree = sh(["git","write-tree"]).stdout.strip()
    parent = sh(["git","rev-parse","HEAD"]).stdout.strip()
    if not tree or not parent:
        attempts.append({"intento":intento,"resultado":"write-tree/rev-parse fallo"}); time.sleep(3); continue
    newc = sh(["git","-c","user.name=kernel-bot","-c","user.email=kernel-bot@local",
               "commit-tree",tree,"-p",parent,
               "-m","D-148 D-149 D-149b: gate duro, cache grafo, baseline regenerado"]).stdout.strip()
    if not newc:
        attempts.append({"intento":intento,"resultado":"commit-tree fallo"}); time.sleep(3); continue
    sh(["git","update-ref","HEAD",newc])
    p = sh(["git","push","origin",f"{newc}:refs/heads/main",f"--force-with-lease=refs/heads/main:{remote}"])
    if p.returncode==0:
        commit_ok=True; attempts.append({"intento":intento,"resultado":"push OK"}); break
    attempts.append({"intento":intento,"resultado":f"push rc={p.returncode}"}); detail=(p.stdout+p.stderr)[-300:]; time.sleep(5)
res["attempts"]=attempts
res["checks"].append({"name":"fast_forward_only","ok":commit_ok,"detail":detail[:200] if not commit_ok else "publicado solo como fast-forward"})
res["checks"].append({"name":"commit_rc0","ok":commit_ok,"detail":detail[:200]})
# D-150: si el commit/push falla NO se da nada por bueno (fail-closed).
if not commit_ok:
    res["checks"].append({"name":"push_rc0","ok":False,"detail":detail[:300]})
    (OUT/"patches.json").write_text(json.dumps(res, indent=2)); sys.exit(1)
res["checks"].append({"name":"push_rc0","ok":True,"detail":detail[:300]})
after = sh(["git","ls-remote","origin","refs/heads/main"]).stdout.split()[0]
res["checks"].append({"name":"remote_sha_matches","ok":after==sh(["git","rev-parse","HEAD"]).stdout.strip()})
res["ok"] = all(c["ok"] for c in res["checks"])
(OUT/"patches.json").write_text(json.dumps(res, indent=2))
sys.exit(0 if res["ok"] else 1)
