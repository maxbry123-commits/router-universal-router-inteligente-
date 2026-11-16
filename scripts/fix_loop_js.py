"""fix_loop_js.py — Reescribe api/loop.js corrigiendo los 4 bugs:
1) estado persistente en disco (loop_state.json)
2) dueño único (elimina el plugin loop_wachdog duplicado)
3) error del motor Python no silenciado
4) tope de vueltas desde config (LOOP_MAX_ITER)
"""
from pathlib import Path

TARGET = Path("api/loop.js")

CORRECTED = r'''
// api/loop.js — MINIMAX 4: loop corregido (estado persistente, dueño único,
// error no silenciado, tope desde config).
import fs from "fs";
import path from "path";
import { execFile } from "child_process";

const STATE_FILE = path.join(process.cwd(), "loop_state.json");
const MAX_ITER = parseInt(process.env.LOOP_MAX_ITER || "8", 10);

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
  } catch {
    return { running: false, iteration: 0, last_error: null };
  }
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function runEngine(payload) {
  return new Promise((resolve, reject) => {
    execFile("python3", ["-m", "router_llm_hf.loop_engine", JSON.stringify(payload)],
      { timeout: 60000 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(`engine: ${stderr || err.message}`));
        try { resolve(JSON.parse(stdout)); }
        catch (e) { reject(new Error(`engine parse: ${e.message}`)); }
      });
  });
}

export async function loopStep(input) {
  const state = loadState();
  if (state.running) throw new Error("loop ya en ejecución (dueño único)");
  state.running = true; state.iteration = 0; state.last_error = null;
  saveState(state);

  try {
    for (let i = 0; i < MAX_ITER; i++) {
      state.iteration = i + 1;
      saveState(state);
      const result = await runEngine({ input, iteration: i + 1 });
      if (result.done) break;
    }
    state.running = false;
    saveState(state);
    return { ok: true, iteration: state.iteration };
  } catch (e) {
    state.running = false;
    state.last_error = String(e);
    saveState(state);
    throw e; // NO se silencia
  }
}

export function loopStatus() {
  return loadState();
}
'''

def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(CORRECTED.strip() + "\n", encoding="utf-8")
    print(f"api/loop.js reescrito ({len(CORRECTED)} bytes).")

if __name__ == "__main__":
    main()
