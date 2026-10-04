import { createRun } from "./run/view.js";

export function renderRun(context) {
  const section = document.createElement("section");
  section.className = "panel run-app";
  section.dataset.panel = "run";
  section.innerHTML = `
    <div class="run-shell">
      <header class="run-top">
        <div class="run-brand"><b>UI YAIWES</b><small>Run · equipo IA</small></div>
        <nav class="run-tabs" id="run-tabs">
          <button type="button" class="on" data-view="cascade">CASCADE</button>
          <button type="button" data-view="tren">TREN</button>
          <button type="button" data-view="auditor">AUDITOR</button>
          <button type="button" data-view="ventanas">VENTANAS</button>
          <button type="button" data-view="orquesta">ORQUESTA</button>
        </nav>
        <div class="run-flex">
          <button class="run-btn run-ghost" type="button" id="run-btnAdd">+ IA</button>
          <button class="run-btn run-ghost" type="button" id="run-btnSand">Sandbox</button>
          <button class="run-btn run-ghost" type="button" id="run-btnCode">Codigo</button>
          <button class="run-btn run-primary" type="button" id="run-btnRun">Run</button>
        </div>
      </header>
      <div class="run-stage">
        <div class="run-canvas" id="run-canvas"><p class="run-boot">Cargando UI YAIWES…</p></div>
        <aside class="run-side" id="run-side" hidden></aside>
      </div>
      <footer class="run-foot"><span id="run-fl">—</span><span id="run-fr">—</span></footer>
    </div>
    <div class="run-err" id="run-err"></div>`;
  createRun(section);
  return section;
}
