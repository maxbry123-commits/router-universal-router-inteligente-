#!/usr/bin/env python3
"""Gestión conservadora de blockedProviders de OmniRoute por API oficial local.

DRY-RUN por defecto. PATCH solo con --aplicar. Usa CAS/If-Match para no pisar
configuraciones concurrentes. Nunca imprime el resto de /api/settings ni claves.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from diagnostico import local_base


VALID_PROVIDER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def proposed(current, providers, undo=False):
    base = list(dict.fromkeys(p for p in current if isinstance(p, str)))
    if undo:
        return [p for p in base if p not in providers]
    return base + [p for p in providers if p not in base]


def _request(url, data=None, revision=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if revision is not None:
        headers["If-Match"] = str(revision)
    req = urllib.request.Request(
        url, data=json.dumps(data).encode() if data is not None else None,
        method="PATCH" if data is not None else "GET", headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        exc.close()
        return exc.code, {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:20128")
    parser.add_argument("--proveedor", action="append", required=True)
    parser.add_argument("--aplicar", action="store_true",
                        help="Autoriza modificar /api/settings; por defecto SOLO DRY-RUN")
    parser.add_argument("--desbloquear", action="store_true",
                        help="Quitar los IDs de blockedProviders (también requiere --aplicar)")
    opts = parser.parse_args(argv)
    base = local_base(opts.url)
    if not all(VALID_PROVIDER.fullmatch(p) for p in opts.proveedor):
        parser.error("Un ID de proveedor debe contener solo minúsculas, dígitos y guion")
    status, settings = _request(base + "/api/settings")
    if status != 200 or not isinstance(settings, dict):
        print(json.dumps({"status": "FAIL_SETTINGS_READ", "http": status}))
        return 2
    rev = settings.get("settingsRevision")
    existing = settings.get("blockedProviders", [])
    if not isinstance(rev, int) or rev < 0 or not isinstance(existing, list):
        print(json.dumps({"status": "FAIL_REVISION_OR_BLOCKLIST"}))
        return 2
    changed = proposed(existing, opts.proveedor, opts.desbloquear)
    outcome = {
        "status": "UNCHANGED" if changed == existing else "DRY_RUN",
        "current": existing,
        "proposed": changed,
        "settingsRevision": rev,
    }
    if opts.aplicar and changed != existing:
        code, _ = _request(base + "/api/settings",
                           {"blockedProviders": changed, "expectedRevision": rev},
                           revision=rev)
        outcome["status"] = "APPLIED" if code == 200 else "REJECTED"
        outcome["http"] = code
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
        return 0 if code == 200 else 3
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
