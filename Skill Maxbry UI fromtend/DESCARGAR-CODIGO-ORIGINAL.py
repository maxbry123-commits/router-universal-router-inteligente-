#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen
import zipfile, io, sys

COMMIT = "1d572f4b1862f5f6b1be61bb33380fede433e1df"
URL = f"https://codeload.github.com/swamimalode07/rare-ui/zip/{COMMIT}"
DEST = Path(sys.argv[1] if len(sys.argv) > 1 else "RARE-UI-ORIGINAL")

if DEST.exists():
    raise SystemExit(f"ERROR: ya existe {DEST}")

print("Descargando:", URL)
req = Request(URL, headers={"User-Agent":"RUI-YAIWES/1.0"})
with urlopen(req, timeout=120) as r:
    data = r.read()

with zipfile.ZipFile(io.BytesIO(data)) as z:
    top = z.namelist()[0].split("/")[0]
    z.extractall(".")

Path(top).rename(DEST)
print("DESCARGADO:", DEST)
print("COMPONENTES:", DEST / "components" / "ui")
