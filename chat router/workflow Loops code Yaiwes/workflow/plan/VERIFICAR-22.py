#!/usr/bin/env python3
from pathlib import Path
import sys

EXPECTED = ['folder-component', 'bounce-sidebar', 'hook-sidebar', 'family-drawer', 'proximity-sidebar', 'duration-picker', 'fluid-orb', 'scroll-progress', 'code-block', 'otp-input', 'gravity-letters', 'github-activity', 'emoji-reaction', 'notification-bell', 'step-player', 'grid-reveal', 'gooey-nav', 'delete-button', 'animated-counter', 'matrix-orb', 'task-list', 'voice-note']
root = Path(sys.argv[1] if len(sys.argv) > 1 else "RARE-UI-ORIGINAL")
ui = root / "components" / "ui"

if not ui.exists():
    raise SystemExit(f"FAIL: no existe {ui}")

missing = [n for n in EXPECTED if not (ui / f"{n}.tsx").exists()]
print("Esperados:", len(EXPECTED))
print("Presentes:", len(EXPECTED)-len(missing))
if missing:
    print("Faltan:", ", ".join(missing))
    raise SystemExit(1)

print("PASS: 22/22 componentes presentes")
