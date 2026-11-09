#!/usr/bin/env python3
"""Wake next Space when local CPU stays >= threshold. No Jobs. No router.

CPU medido sobre el cgroup del contenedor (uso real del contenedor), no sobre
/pro/stat del host: /proc/stat refleja la CPU de la maquina compartida y
provocaba falsos positivos que despertaban el Space siguiente sin carga real.
Si no hay cgroup legible, no se despierta a nadie (modo fail-safe).
"""
from __future__ import annotations
import os, time, threading, urllib.request

THRESHOLD = float(os.environ.get("CPU_SCALE_THRESHOLD", "90"))
INTERVAL = float(os.environ.get("CPU_SCALE_INTERVAL_S", "10"))
STREAK = int(os.environ.get("CPU_SCALE_STREAK", "2"))
NEXT = (os.environ.get("NEXT_SPACE_URL") or "").rstrip("/")
COOLDOWN = float(os.environ.get("CPU_SCALE_COOLDOWN_S", "60"))

def _cpu_quota():
    """(cores asignadas al contenedor, uso_usec actual). (0, 0) si no es legible."""
    # cgroup v2
    try:
        with open("/sys/fs/cgroup/cpu.max") as f:
            quota, period = f.read().split()
        with open("/sys/fs/cgroup/cpu.stat") as f:
            for line in f:
                if line.startswith("usage_usec"):
                    usage = int(line.split()[1])
        cores = 1.0 if quota == "max" else int(quota) / int(period)
        return max(0.1, cores), usage
    except Exception:
        pass
    # cgroup v1
    try:
        with open("/sys/fs/cgroup/cpuacct.usage") as f:
            usage = int(f.read().strip())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as f:
            quota = int(f.read().strip())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as f:
            period = int(f.read().strip())
        cores = 1.0 if quota <= 0 else quota / period
        return max(0.1, cores), usage
    except Exception:
        return 0.0, 0

def container_cpu_pct(window_s: float = 1.0) -> float:
    """% de CPU del CONTENEDOR realmente usada (0-100). -1 si no se puede medir."""
    cores1, usage1 = _cpu_quota()
    if cores1 <= 0:
        return -1.0
    time.sleep(window_s)
    cores2, usage2 = _cpu_quota()
    if cores2 <= 0 or usage2 < usage1:
        return -1.0
    delta_usage_s = (usage2 - usage1) / 1_000_000.0
    return max(0.0, min(100.0, (delta_usage_s / window_s) * 100.0 / cores2))

def wake_next():
    if not NEXT:
        return False
    url = NEXT + "/v1/models"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "swe-code-scaler"})
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"[scaler] woke next HTTP {r.status} {url}", flush=True)
            return True
    except Exception as e:
        print(f"[scaler] wake attempt {url}: {type(e).__name__}: {e}", flush=True)
        return False

def loop():
    print(f"[scaler] start threshold={THRESHOLD}% next={NEXT or '(none)'} interval={INTERVAL}s", flush=True)
    hot = 0
    last_wake = 0.0
    while True:
        try:
            pct = container_cpu_pct()
            if pct < 0:
                print("[scaler] cpu no medible (sin cgroup): no se despierta al siguiente", flush=True)
                hot = 0
            else:
                if pct >= THRESHOLD:
                    hot += 1
                else:
                    hot = 0
                print(f"[scaler] cpu(contenedor)={pct:.1f}% streak={hot}/{STREAK}", flush=True)
            now = time.time()
            if hot >= STREAK and NEXT and (now - last_wake) >= COOLDOWN:
                wake_next()
                last_wake = now
                hot = 0
        except Exception as e:
            print(f"[scaler] err {type(e).__name__}: {e}", flush=True)
        time.sleep(INTERVAL)

def start_background():
    t = threading.Thread(target=loop, name="cpu-scaler", daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    loop()
