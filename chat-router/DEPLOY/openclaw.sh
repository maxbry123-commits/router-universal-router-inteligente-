#!/usr/bin/env bash
# OpenClaw Gateway (loopback). Proxy :7860 /openclaw/* -> 127.0.0.1:18789
set -uo pipefail
: "${OPENCLAW_GATEWAY_TOKEN:?Falta OPENCLAW_GATEWAY_TOKEN (Space Secret)}"

NODE24_VERSION="${NODE24_VERSION:-v24.22.2}"
OPENCLAW_VERSION="${OPENCLAW_VERSION:-2026.10.9}"
NODE_DIR=/opt/node24
UID_NOW="$(id -u)"

bootstrap_node24() {
  export PATH="$NODE_DIR/bin:$PATH"
  if command -v openclaw >/dev/null 2>&1 || [ -x "$NODE_DIR/bin/openclaw" ]; then
    return 0
  fi
  echo "bootstrap: installing Node $NODE24_VERSION + openclaw@$OPENCLAW_VERSION"
  tmp=/tmp/node24.tgz
  curl -fsSL "https://nodejs.org/dist/${NODE24_VERSION}/node-${NODE24_VERSION}-linux-x64.tar.gz" -o "$tmp"
  mkdir -p /opt
  rm -rf "$NODE_DIR"
  tar -xzf "$tmp" -C /opt
  mv "/opt/node-${NODE24_VERSION}-linux-x64" "$NODE_DIR"
  rm -f "$tmp"
  export PATH="$NODE_DIR/bin:$PATH"
  npm install -g --no-audit --no-fund "openclaw@${OPENCLAW_VERSION}"
  openclaw --version || true
}

bootstrap_node24
export PATH="$NODE_DIR/bin:$PATH"

# El bootstrap de pairing usa la caducidad oficial de OpenClaw.
# No modificar su código compilado ni prolongar tokens de identidad para evitar controles.

# State MUST be a real local dir owned by this uid with mode 0700.
# /data FUSE breaks OpenClaw state ownership locks — keep live state in /tmp only.
export OPENCLAW_HOME="/tmp/openclaw-home-${UID_NOW}"
export HOME="$OPENCLAW_HOME"
# Live state must be local 0700 (not /data FUSE). Wipe ONLY ephemeral locks;
# restore pairing DB + config from /data so the phone stays linked (QR no cambia).
rm -rf "$OPENCLAW_HOME"
mkdir -m 700 -p "$OPENCLAW_HOME/.openclaw/state" "$OPENCLAW_HOME/.openclaw/identity"
mkdir -p /data/openclaw/state /data/openclaw/identity /data/openclaw/snapshots
# --- Pairing durable: snapshots completos de ~/.openclaw (sqlite via backup API, sin wal/shm/locks)
# en /data/openclaw/snapshots/<ts>.tgz (se guardan 8). Restore = el más nuevo VÁLIDO.
# Nunca se arranca limpio si existe algún snapshot/legacy válido -> el QR no cambia.
cat > /tmp/oc_persist.py <<'PYS'
import os, sys, sqlite3, json, tarfile, tempfile, shutil, time, glob
SNAP = "/data/openclaw/snapshots"; KEEP = 8
SKIP_SUFFIX = ("-wal", "-shm", "-journal", ".lock", ".tmp", ".sock", ".pid")
def ok_sqlite(p):
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True); r = c.execute("pragma integrity_check").fetchone()[0]; c.close(); return r == "ok"
    except Exception: return False
def ok_json(p):
    try: json.load(open(p)); return True
    except Exception: return False
def snapshot(src):
    tmp = tempfile.mkdtemp(prefix="ocsnap"); dst = os.path.join(tmp, ".openclaw")
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not d.endswith(".lock") and d not in ("locks", "lock")]
        rel = os.path.relpath(root, src); os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            if f.endswith(SKIP_SUFFIX): continue
            s = os.path.join(root, f); d = os.path.join(dst, rel, f)
            try:
                if f.endswith((".sqlite", ".db", ".sqlite3")):
                    a = sqlite3.connect("file:%s?mode=ro" % s, uri=True); b = sqlite3.connect(d); a.backup(b); b.close(); a.close()
                    c = sqlite3.connect(d); c.execute("pragma journal_mode=delete"); c.close()
                    if not ok_sqlite(d): raise RuntimeError("integrity " + f)
                else: shutil.copy2(s, d)
            except Exception as e:
                print("persist: snapshot abortado (%s)" % e); shutil.rmtree(tmp); return 1
    os.makedirs(SNAP, exist_ok=True)
    out = os.path.join(SNAP, "%d.tgz" % time.time())
    with tarfile.open(out + ".tmp", "w:gz") as t: t.add(dst, ".openclaw")
    os.replace(out + ".tmp", out); shutil.rmtree(tmp)
    for old in sorted(glob.glob(SNAP + "/*.tgz"))[:-KEEP]: os.remove(old)
    return 0
def valid_tree(d):
    for root, _, files in os.walk(d):
        for f in files:
            p = os.path.join(root, f)
            if f.endswith((".sqlite", ".db", ".sqlite3")) and not ok_sqlite(p): return False
            if f.endswith(".json") and not ok_json(p): return False
    return True
def restore(dst, skip=0):
    snaps = sorted(glob.glob(SNAP + "/*.tgz"), reverse=True)[skip:]
    for s in snaps:
        tmp = tempfile.mkdtemp(prefix="ocrest")
        try:
            with tarfile.open(s) as t: t.extractall(tmp)
            if valid_tree(os.path.join(tmp, ".openclaw")):
                shutil.rmtree(dst, ignore_errors=True); shutil.move(os.path.join(tmp, ".openclaw"), dst)
                print("persist: restaurado", s); return 0
            print("persist: snapshot inválido, salto", s)
        except Exception as e: print("persist: error", s, e)
        finally: shutil.rmtree(tmp, ignore_errors=True)
    return 3
cmd = sys.argv[1]
if cmd == "snapshot": sys.exit(snapshot(sys.argv[2]))
if cmd == "restore": sys.exit(restore(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0))
PYS
OCDIR="$OPENCLAW_HOME/.openclaw"
restore_legacy() {
  [ -f /data/openclaw/openclaw.json ] && cp -f /data/openclaw/openclaw.json "$OCDIR/openclaw.json"
  [ -f /data/openclaw/state/openclaw.sqlite ] && cp -f /data/openclaw/state/openclaw.sqlite "$OCDIR/state/openclaw.sqlite"
  for f in devices.json paired.json; do [ -f "/data/openclaw/state/$f" ] && cp -f "/data/openclaw/state/$f" "$OCDIR/state/$f"; done
  [ -f /data/openclaw/identity/device.json ] && cp -f /data/openclaw/identity/device.json "$OCDIR/identity/device.json"
  true
}
fix_perms() {
  mkdir -m 700 -p "$OCDIR/state" "$OCDIR/identity"
  chown -R "$UID_NOW" "$OPENCLAW_HOME" 2>/dev/null || true
  chmod 700 "$OPENCLAW_HOME" "$OCDIR"; find "$OCDIR" -type f -exec chmod 600 {} + 2>/dev/null || true
}
if ! python3 /tmp/oc_persist.py restore "$OCDIR"; then
  echo "persist: sin snapshot válido -> restore legacy (state/openclaw.sqlite + identity/device.json)"
  restore_legacy
fi
fix_perms
SNAP_SKIP=0
GW_PID=""
persist_now() { python3 /tmp/oc_persist.py snapshot "$OCDIR" || true; }
on_term() { echo "persist: SIGTERM -> snapshot final"; [ -f /tmp/oc_healthy ] && persist_now; [ -n "$GW_PID" ] && kill "$GW_PID" 2>/dev/null; exit 0; }
trap on_term TERM INT
# snapshot cada 60s SOLO si el gateway lleva sano >=90s (no persistir estado roto)
( while sleep 60; do [ -f /tmp/oc_healthy ] && persist_now; done ) &

python3 - <<'PY'
import json, os, stat
from pathlib import Path
home = Path(os.environ["OPENCLAW_HOME"])
p = home / ".openclaw" / "openclaw.json"
cfg = {}
if p.exists():
    try:
        cfg = json.loads(p.read_text())
    except Exception:
        cfg = {}
gw = cfg.setdefault("gateway", {})
# OpenClaw requiere mode=local para abrir su API HTTP en loopback.
# No se sobreescribe un modo existente establecido por el propietario.
gw.setdefault("mode", "local")
gw.setdefault("controlUi", {})["basePath"] = "/openclaw"
# HTTP OpenAI-compatible sólo en el Gateway protegido con bearer token.
# Necesario para GET /v1/models y POST /v1/chat/completions del consejero Sonnet.
gw.setdefault("http", {}).setdefault("endpoints", {}).setdefault("chatCompletions", {})["enabled"] = True
auth = gw.setdefault("auth", {})
auth["mode"] = "token"
auth["token"] = os.environ["OPENCLAW_GATEWAY_TOKEN"]
gw["publicOrigin"] = os.environ.get(
    "OPENCLAW_PUBLIC_ORIGIN",
    "https://comand-center-1-riu-router.hf.space",
)
# strip bad path if somehow present
po = gw.get("publicOrigin", "")
if "/openclaw" in po:
    gw["publicOrigin"] = "https://comand-center-1-riu-router.hf.space"
gw["trustedProxies"] = ["127.0.0.1", "::1"]
tp = auth.setdefault("trustedProxy", {})
tp["allowLoopback"] = True
tp["userHeader"] = "x-forwarded-user"
# --- provider swecode: merge conservador (no borrar Anthropic ni perfiles ya configurados) ---
try:
    sw = json.loads(Path("/swecode_provider.json").read_text())
    # No borrar providers Anthropic/OAuth ni modelos admitidos del Gateway al reiniciar.
    # Conservar las sesiones/autorizaciones que el operador configuró legalmente.
    modelcfg = cfg.setdefault("models", {})
    modelcfg.setdefault("providers", {}).update(sw["models"].get("providers", {}))
    ad = cfg.setdefault("agents", {}).setdefault("defaults", {})
    # No cambiar el modelo principal del Gateway si ya lo eligió su propietario.
    ad.setdefault("model", sw["agents"]["defaults"]["model"])
    ad.setdefault("models", {}).update(sw["agents"]["defaults"]["models"])
    # Permitir SOLO Sonnet para el consejero dedicado, no lo convierte en default.
    ad["models"].setdefault("anthropic/claude-sonnet-5-5", {})
    root_agents = cfg.setdefault("agents", {})
    agents = root_agents.setdefault("entries", {})
    agents.setdefault("main", {})  # proteger OpenClaw/default: no convertir el consejo en agente principal
    # Filtro de propiedad del multiagente: sin ownership explícito, un solo
    # default heredado (main) mantiene el chat original y valida el Gateway.
    if root_agents.get("ownership") != "explicit" and not any(
        isinstance(x,dict) and x.get("default") is True for x in agents.values()
    ):
        agents["main"]["default"] = True
    counsel = agents.setdefault("swen-council", {})
    counsel.update({"name":"SWEN Claude Sonnet 5.5","model":{"primary":"anthropic/claude-sonnet-5-5","fallbacks":[]},
      "thinkingDefault":"max","skills":[],
      "tools":{"profile":"minimal","allow":["session_status"],
        "deny":["group:fs","group:runtime","group:web","group:messaging","browser","exec","write","apply_patch","cron"]}})
    for prov, var in (("groq", "GROQ_API_KEY"), ("nvidia", "NVIDIA_API_KEY")):
        pv = cfg["models"]["providers"].get(prov)
        if pv is None: continue
        if os.environ.get(var):
            pv["apiKey"] = os.environ[var]
            print("provider %s: apiKey desde %s (%d models)" % (prov, var, len(pv["models"])))
        else:
            cfg["models"]["providers"].pop(prov)
            for k in [k for k in ad["models"] if k.startswith(prov + "/")]: ad["models"].pop(k)
            print("WARN provider %s omitido: falta %s" % (prov, var))
    print("swecode provider:", sum(len(v["models"]) for v in cfg["models"]["providers"].values()), "models; providers:", ",".join(cfg["models"]["providers"]))
except Exception as e:
    print("WARN swecode provider no aplicado:", e)
p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
p.write_text(json.dumps(cfg, indent=2))
os.chmod(p.parent, 0o700)
os.chmod(home, 0o700)
print("wrote", p, "uid", os.getuid(), "publicOrigin", gw["publicOrigin"])
print("home mode", oct(p.parent.stat().st_mode & 0o777))
PY

# Also fix proxy: accept WS before upstream so clients don't get opaque 403
# (done in proxy.py separately if needed)

PORT="${OPENCLAW_PORT:-18789}"
export OPENCLAW_GATEWAY_TOKEN
export OPENCLAW_STATE_DIR="$OPENCLAW_HOME/.openclaw"

FAILS=0
rm -f /tmp/oc_healthy
while true; do
  if [ "$FAILS" -ge 3 ]; then
    # Cuarentena NO destructiva: copia del estado para forense y restore del snapshot anterior.
    # Solo se arranca limpio (=> QR nuevo) si NINGÚN snapshot/legacy es válido.
    q="/data/openclaw/quarantine-$(date +%s)"; mkdir -p "$q"; cp -a "$OCDIR" "$q/" 2>/dev/null
    SNAP_SKIP=$((SNAP_SKIP+1))
    echo "gateway falla x$FAILS -> copia en $q; restaurando snapshot previo (skip=$SNAP_SKIP)"
    if ! python3 /tmp/oc_persist.py restore "$OCDIR" "$SNAP_SKIP"; then
      echo "persist: no quedan snapshots válidos -> se conserva estado actual (NO se borra pairing)"
      SNAP_SKIP=0
    fi
    fix_perms
    FAILS=0
  fi
  echo "starting gateway home=$OPENCLAW_HOME uid=$UID_NOW port=$PORT"
  OCBIN="$(command -v openclaw || echo "$NODE_DIR/bin/openclaw")"
  "$OCBIN" gateway --bind loopback --port "$PORT" --allow-unconfigured &
  GW_PID=$!; START=$(date +%s)
  ( sleep 90; kill -0 "$GW_PID" 2>/dev/null && touch /tmp/oc_healthy ) &
  wait "$GW_PID"; rc=$?; GW_PID=""
  if [ $(( $(date +%s) - START )) -ge 90 ]; then FAILS=0; SNAP_SKIP=0; fi
  rm -f /tmp/oc_healthy
  FAILS=$((FAILS+1)); echo "gateway exit $rc (fallo $FAILS) -> restart en 5s"; sleep 5
done
