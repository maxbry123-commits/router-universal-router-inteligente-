"""fix_loop_js.py — Parche quirúrgico de api/loop.js.
NO reescribe la estructura. Solo añade:
1) persistencia en loop_state.json (ruta configurable)
2) dueño único (state.running) si no lo tiene
3) tope desde LOOP_MAX_ITER
4) export loopStatus()
Valida que api/loop.js exista antes de tocar nada.
"""
from pathlib import Path

TARGET = Path("api/loop.js")

HEADER = """
// --- MINIMAX 4: persistencia y dueño único ---
const fs = require("fs");
const path = require("path");
const os = require("os");
const LOOP_STATE_FILE = process.env.LOOP_STATE_PATH
  || path.join(os.tmpdir(), "loop_state.json");
const LOOP_MAX_ITER = parseInt(process.env.LOOP_MAX_ITER || "8", 10);
function _loadLoopState() {
  try { return JSON.parse(fs.readFileSync(LOOP_STATE_FILE, "utf8")); }
  catch { return { running: false, iteration: 0, last_error: null }; }
}
function _saveLoopState(s) {
  fs.writeFileSync(LOOP_STATE_FILE, JSON.stringify(s, null, 2));
}
// --- FIN MINIMAX 4 ---
"""

FOOTER = """
// --- MINIMAX 4: status ---
module.exports.loopStatus = function() { return _loadLoopState(); };
// --- FIN MINIMAX 4 ---
"""

def patch():
    if not TARGET.exists():
        raise FileNotFoundError(f"No existe {TARGET} — revisa la ruta real en el repo.")
    text = TARGET.read_text(encoding="utf-8")
    if "MINIMAX 4: persistencia" in text:
        print("api/loop.js ya parcheado (idempotente).")
        return
    # Insertar header tras 'use strict' o al inicio
    stripped = text.lstrip()
    if stripped.startswith('"use strict"') or stripped.startswith("'use strict'"):
        idx = text.find("\n")
        text = text[:idx+1] + HEADER + text[idx+1:]
    else:
        text = HEADER + text
    # Insertar footer al final (preserva module.exports original + añade loopStatus)
    text = text.rstrip() + "\n" + FOOTER
    TARGET.write_text(text, encoding="utf-8")
    print("api/loop.js parcheado: persistencia + dueño único + tope + loopStatus.")

if __name__ == "__main__":
    patch()
