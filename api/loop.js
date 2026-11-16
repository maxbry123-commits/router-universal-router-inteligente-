"use strict";

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
// api/loop.js — loop del router (MINIMAX 4).
// La persistencia (loop_state.json), el tope LOOP_MAX_ITER y el export
// loopStatus() los inyecta scripts/fix_loop_js.py sobre este archivo:
// parche quirúrgico, sin reescribir la estructura del loop.

const { execFile } = require("child_process");

const LOOP_ENGINE_MODULE = "router_llm_hf.loop_engine";
const ENGINE_TIMEOUT_MS = 60000;

function runEngine(payload) {
  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      ["-m", LOOP_ENGINE_MODULE, JSON.stringify(payload)],
      { timeout: ENGINE_TIMEOUT_MS },
      (err, stdout, stderr) => {
        if (err) return reject(new Error(`engine: ${stderr || err.message}`));
        try {
          resolve(JSON.parse(stdout));
        } catch (e) {
          reject(new Error(`engine parse: ${e.message}`));
        }
      }
    );
  });
}

async function loopStep(input) {
  const state = _loadLoopState();
  if (state.running) throw new Error("loop ya en ejecución (dueño único)");
  state.running = true;
  state.iteration = 0;
  state.last_error = null;
  _saveLoopState(state);

  try {
    for (let i = 0; i < LOOP_MAX_ITER; i++) {
      state.iteration = i + 1;
      _saveLoopState(state);
      const result = await runEngine({ input, iteration: i + 1 });
      if (result.done) break;
    }
    state.running = false;
    _saveLoopState(state);
    return { ok: true, iteration: state.iteration };
  } catch (e) {
    state.running = false;
    state.last_error = String(e);
    _saveLoopState(state);
    throw e; // NO se silencia
  }
}

module.exports.loopStep = loopStep;

// --- MINIMAX 4: status ---
module.exports.loopStatus = function() { return _loadLoopState(); };
// --- FIN MINIMAX 4 ---
