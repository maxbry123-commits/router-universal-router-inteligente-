import { MODELS, ROLES, DEST, PROC, LIB, DOCS, NODOS, role, model, dest, mkNode } from "./data.js";

const esc = s => String(s ?? "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export function createRun(root) {
  const $ = sel => root.querySelector(sel);
  const showErr = m => { const e = $("#run-err"); e.textContent = String(m); e.style.display = "block"; };

  const S = {
    view: "cascade", panel: null, sel: null, running: false, cursor: -1,
    name: "Equipo CODE",
    input: "Revisa este modulo y propone un parche minimo.",
    dest: "agent-api", endpoint: "/api/agent/complete", last: "",
    sb: { backend: "docker", timeout: 30, mem: 512, net: false },
    nodes: [mkNode("analyzer"), mkNode("coder"), mkNode("critic"), mkNode("synthesizer")],
    tren: { e: [], i: 8, props: ["PROP-001 Sentinel techo", "PROP-002 Canary 10%", "PROP-003 Lote fichas"], led: ["GENESIS"], det: "Toca un vagon." },
    aud: { q: "", pins: [], sel: null, out: "" },
    vent: { i: 0, st: "lista", p: {}, bp: {}, est: ["pending", "pending", "pending", "pending"], fotos: [null, null, null, null], in: '{"x":5}', dsl: "" },
    orq: { in: '{"x":5,"msg":"hola tren"}', lib: "sumar1", pila: [], out: "Ejecuta para ver la salida.", py: "", dest: "ver aqui" }
  };
  for (let t = 0; t < 16; t++) S.tren.e.push(t < 8 ? "done" : t === 8 ? "running" : "pending");

  const opts = (list, val, i0, i1) =>
    list.map(item => `<option value="${esc(item[i0])}"${item[i0] === val ? " selected" : ""}>${esc(item[i1])}</option>`).join("");
  const nodeBy = id => S.nodes.find(n => n.id === id) || null;
  const slot = i => S.nodes.length >= 20
    ? '<div class="run-slot"></div>'
    : `<div class="run-slot"><button type="button" data-ins="${i}">+</button></div>`;

  function viewCascade() {
    if (S.panel === "code") {
      return `<div class="run-box"><div class="run-row"><span class="run-k">Documento DAG locked</span><button class="run-btn" type="button" id="copyY">Copiar YAML</button></div><pre class="run-pre" id="yaml">${esc(toYaml())}</pre></div>`;
    }
    let h = '<div class="run-col">';
    h += `<button class="run-term${S.sel === "in" ? " on" : ""}" type="button" data-sel="in"><div class="run-k">Input</div><div class="run-t">${esc(S.input.slice(0, 80))}</div><div class="run-s">control de flujo · payload inicial</div></button>`;
    h += slot(0);
    S.nodes.forEach((n, i) => {
      const m = model(n.modelId), rl = role(n.roleId);
      const badge = n.status === "running" ? "RUN" : n.status === "done" ? "DONE" : n.backend;
      h += `<article class="run-card${S.sel === n.id ? " on" : ""}" data-sel="${n.id}" style="${n.on ? "" : "opacity:.5"}">
        <div class="run-row"><div><span class="run-idx">${("0" + (i + 1)).slice(-2)}</span><strong>${esc(n.label)}</strong></div><span class="run-chip">${esc(badge)}</span></div>
        <select data-model="${n.id}">${opts(MODELS, n.modelId, 0, 1)}</select>
        <div style="height:8px"></div>
        <select data-role="${n.id}">${opts(ROLES, n.roleId, 0, 1)}</select>
        <div class="run-s">IN-01 → ${esc(m[1])} → OUT-01 · ${esc(rl[2])}</div>
      </article>`;
      h += slot(i + 1);
    });
    const d = dest(S.dest);
    h += `<button class="run-term${S.sel === "out" ? " on" : ""}" type="button" data-sel="out"><div class="run-k">API · Destino</div><div class="run-t">${esc(d[1])}</div><div class="run-s">${esc(S.endpoint)}</div></button></div>`;
    return h;
  }

  function formSb(sb, global) {
    return `<div class="run-field"><div class="run-k">Backend</div><select id="sbB"><option${sb.backend === "docker" ? " selected" : ""}>docker</option><option${sb.backend === "subprocess" ? " selected" : ""}>subprocess</option></select></div>
      <div class="run-field"><div class="run-k">Timeout ${sb.timeout}s</div><input type="range" id="sbT" min="5" max="120" step="5" value="${sb.timeout}"></div>
      <div class="run-field"><div class="run-k">Memoria ${sb.mem} MB</div><input type="range" id="sbM" min="128" max="4096" step="128" value="${sb.mem}"></div>`
      + (global ? '<button class="run-btn" type="button" id="sbAll">Aplicar a todas las IA</button>' : "");
  }

  function viewSide() {
    if (S.panel === "sand")
      return `<h3>Sandbox <button class="run-btn run-ghost" type="button" data-close="1">x</button></h3><div class="run-sidebody">${formSb(S.sb, true)}</div>`;
    if (S.sel === "in")
      return `<h3>Input <button class="run-btn run-ghost" type="button" data-close="1">x</button></h3><div class="run-sidebody"><div class="run-field"><div class="run-k">Tarea</div><textarea id="inT">${esc(S.input)}</textarea></div></div>`;
    if (S.sel === "out")
      return `<h3>Destino API <button class="run-btn run-ghost" type="button" data-close="1">x</button></h3><div class="run-sidebody">`
        + `<div class="run-field"><div class="run-k">Destino</div><select id="outD">${opts(DEST, S.dest, 0, 1)}</select></div>`
        + `<div class="run-field"><div class="run-k">Endpoint</div><input type="text" id="outE" value="${esc(S.endpoint)}"></div>`
        + (S.last ? `<div class="run-field"><div class="run-k">Ultimo payload</div><pre class="run-pre">${esc(S.last)}</pre></div>` : "")
        + "</div>";
    const n = nodeBy(S.sel);
    if (!n) return `<h3>Config <button class="run-btn run-ghost" type="button" data-close="1">x</button></h3><div class="run-sidebody">Selecciona un nodo.</div>`;
    return `<h3>${esc(n.label)} <button class="run-btn run-ghost" type="button" data-close="1">x</button></h3><div class="run-sidebody">`
      + `<div class="run-flex" style="margin-bottom:12px"><button class="run-btn" type="button" data-mv="-1">Subir</button><button class="run-btn" type="button" data-mv="1">Bajar</button><button class="run-btn run-ghost" type="button" data-rm="${n.id}">Quitar</button></div>`
      + `<div class="run-field"><div class="run-k">Nombre</div><input type="text" id="nL" value="${esc(n.label)}"></div>`
      + `<div class="run-field"><div class="run-k">System prompt</div><textarea id="nP">${esc(n.prompt)}</textarea></div>`
      + `<div class="run-field"><div class="run-k">Codigo de entrada</div><textarea id="nI">${esc(n.input)}</textarea></div>`
      + `<div class="run-field"><div class="run-k">Codigo de salida</div><textarea id="nO">${esc(n.output)}</textarea></div>`
      + formSb(n, false) + "</div>";
  }

  function toYaml() {
    const lines = ["# UI YAIWES — DAG locked", "", "template:", "  id: YAIWES", "  name: " + JSON.stringify(S.name), "  dag: LOCKED", "", "input:", "  prompt: " + JSON.stringify(S.input), "", "nodes:"];
    S.nodes.forEach((n, i) => lines.push("  - id: n" + ("0" + (i + 1)).slice(-2), "    role: " + n.roleId, "    model: " + n.modelId, "    enabled: " + n.on));
    lines.push("", "output:", "  destination: " + S.dest, "  endpoint: " + JSON.stringify(S.endpoint));
    return lines.join("\n");
  }

  function viewTren() {
    let h = '<div class="run-grid three"><div class="run-box"><div class="run-k">Tren en vivo</div><div class="run-flex" style="overflow:auto;padding:8px 0">';
    S.tren.e.forEach((e, i) => { h += `<button class="run-vagon ${e}" type="button" data-vg="${i}">T-${("00" + (i + 1)).slice(-3)}<br>${NODOS[i]}</button>`; });
    h += `</div><p class="run-s" id="tdet">${esc(S.tren.det)}</p><div class="run-flex"><button class="run-btn run-primary" type="button" id="tGo">Avanzar</button><button class="run-btn" type="button" id="tFail">Simular fallo</button></div></div>`;
    h += '<div class="run-box"><div class="run-k">Cola de firmas</div>';
    if (!S.tren.props.length) h += '<p class="run-s">Cola vacia</p>';
    S.tren.props.forEach((p, i) => {
      h += `<div class="run-row" style="margin-top:8px"><span>${esc(p)}</span><span class="run-flex"><button class="run-btn run-primary" type="button" data-sign="${i}">Firmar</button><button class="run-btn" type="button" data-rej="${i}">Rechazar</button></span></div>`;
    });
    h += `<div class="run-k" style="margin-top:12px">Ledger</div><pre class="run-pre">${esc(S.tren.led.join("\n"))}</pre></div></div>`;
    return h;
  }

  function viewAud() {
    let h = `<div class="run-box"><div class="run-k">Auditor</div><p class="run-s">Anclar documentos e inyectar al agente</p><input type="text" id="aq" placeholder="Buscar…" value="${esc(S.aud.q)}"><div class="run-docs" style="margin-top:10px">`;
    DOCS.forEach(d => {
      if (S.aud.q && d[0].toLowerCase().indexOf(S.aud.q.toLowerCase()) < 0) return;
      h += `<button class="run-docc${S.aud.sel === d[0] ? " on" : ""}" type="button" data-doc="${esc(d[0])}">${esc(d[0])}<br><span class="run-chip">${esc(d[1])}</span></button>`;
    });
    h += "</div>";
    if (S.aud.sel) h += '<div class="run-flex" style="margin-top:10px"><button class="run-btn run-primary" type="button" id="aPin">Anclar</button><button class="run-btn" type="button" id="aSend">Enviar a agente</button></div>';
    if (S.aud.out) h += `<pre class="run-pre" style="margin-top:10px">${esc(S.aud.out)}</pre>`;
    h += `<div class="run-k" style="margin-top:12px">Anclados</div><p class="run-s">${S.aud.pins.length ? S.aud.pins.join(" · ") : "— nada anclado —"}</p></div>`;
    return h;
  }

  function viewVent() {
    let h = `<div class="run-box"><div class="run-row"><div class="run-k">Ventanas del tren</div><span class="run-chip">${esc(S.vent.st)}</span></div><div class="run-flex" style="overflow:auto">`;
    PROC.forEach((p, i) => {
      const f = S.vent.fotos[i];
      h += `<div class="run-box" style="min-width:180px"><b>${p[0]}</b> ${p[1]}<div class="run-s">${S.vent.est[i]}${S.vent.bp[p[0]] ? " · bp" : ""}</div>`;
      h += `<pre class="run-pre">IN ${esc(f ? JSON.stringify(f.inn) : "—")}\nOUT ${esc(f ? (f.err || JSON.stringify(f.out)) : "—")}</pre>`;
      h += `<button class="run-btn" type="button" data-bp="${p[0]}">Breakpoint</button></div>`;
    });
    h += `</div><div class="run-flex" style="margin-top:10px"><input type="text" id="vIn" value="${esc(S.vent.in)}" style="max-width:200px"><button class="run-btn run-primary" type="button" id="vRun">Correr</button><button class="run-btn" type="button" id="vReset">Reiniciar</button><button class="run-btn" type="button" id="vDsl">Export DSL</button></div>`;
    if (S.vent.dsl) h += `<pre class="run-pre" style="margin-top:10px">${esc(S.vent.dsl)}</pre>`;
    h += "</div>";
    return h;
  }

  function viewOrq() {
    const keys = Object.keys(LIB);
    let h = `<div class="run-grid three"><div class="run-box"><div class="run-k">Input</div><textarea id="oIn">${esc(S.orq.in)}</textarea></div>`;
    h += `<div class="run-box"><div class="run-k">Proceso</div><div class="run-flex"><select id="oLib">`;
    keys.forEach(k => { h += `<option${k === S.orq.lib ? " selected" : ""}>${k}</option>`; });
    h += '</select><button class="run-btn" type="button" id="oAdd">+</button></div>';
    S.orq.pila.forEach((p, j) => {
      h += `<div class="run-row" style="margin-top:6px"><span>${j + 1}. ${esc(p)}</span><button class="run-btn run-ghost" type="button" data-del="${j}">x</button></div>`;
    });
    h += '<div class="run-flex" style="margin-top:8px"><button class="run-btn run-primary" type="button" id="oRun">Ejecutar sandbox</button></div></div>';
    h += `<div class="run-box"><div class="run-k">Salida</div><pre class="run-pre">${esc(S.orq.out)}</pre></div></div>`;
    return h;
  }

  function paint() {
    $("#run-fl").textContent = S.nodes.length + " IA · " + S.sb.backend + " · " + S.sb.timeout + "s";
    $("#run-fr").textContent = "→ " + dest(S.dest)[1];
    root.querySelectorAll("#run-tabs button").forEach(b => {
      b.classList.toggle("on", b.getAttribute("data-view") === S.view);
    });
    const canvas = $("#run-canvas"), side = $("#run-side");
    if (S.view === "cascade") canvas.innerHTML = viewCascade();
    else if (S.view === "tren") canvas.innerHTML = viewTren();
    else if (S.view === "auditor") canvas.innerHTML = viewAud();
    else if (S.view === "ventanas") canvas.innerHTML = viewVent();
    else canvas.innerHTML = viewOrq();
    if (S.view === "cascade" && S.panel) { side.hidden = false; side.innerHTML = viewSide(); }
    else { side.hidden = true; side.innerHTML = ""; }
    bind();
  }

  const targetSb = () => S.panel === "sand" ? S.sb : (nodeBy(S.sel) || S.sb);

  function runVent() {
    const v = S.vent;
    if (v.st === "lista") { try { v.p = JSON.parse(v.in); } catch { showErr("entrada no es JSON"); return; } }
    v.st = "corriendo";
    while (v.i < PROC.length) {
      const p = PROC[v.i];
      if (v.bp[p[0]] && v.est[v.i] === "pending") { v.est[v.i] = "pausada"; v.st = "pausada"; return; }
      try { const inn = JSON.parse(JSON.stringify(v.p)); const out = p[2](v.p); v.fotos[v.i] = { inn, out }; v.p = out; v.est[v.i] = "done"; v.i++; }
      catch (ex) { v.fotos[v.i] = { inn: v.p, err: ex.message }; v.est[v.i] = "failed"; v.st = "failed"; return; }
    }
    v.st = "done";
  }

  function onCanvas(e) {
    const t = e.target.closest("[data-sel],[data-ins],[data-vg],[data-sign],[data-rej],[data-doc],[data-bp],[data-del],button");
    if (!t) return;
    if (t.id === "copyY") { try { navigator.clipboard.writeText(toYaml()); t.textContent = "Copiado"; } catch { showErr("No se pudo copiar"); } return; }
    if (t.hasAttribute("data-ins")) {
      if (S.nodes.length >= 20) return;
      const n = mkNode("custom");
      S.nodes.splice(+t.getAttribute("data-ins"), 0, n);
      S.sel = n.id; S.panel = "node"; paint(); return;
    }
    if (t.hasAttribute("data-sel")) { S.sel = t.getAttribute("data-sel"); S.panel = "node"; paint(); return; }
    if (t.hasAttribute("data-vg")) { const i = +t.getAttribute("data-vg"); S.tren.det = "T-" + ("00" + (i + 1)).slice(-3) + " " + NODOS[i] + " · " + S.tren.e[i]; paint(); return; }
    if (t.id === "tGo") {
      const rr = S.tren.e.indexOf("running"); if (rr >= 0) S.tren.e[rr] = "done";
      const p = S.tren.e.indexOf("pending"); if (p >= 0) S.tren.e[p] = "running";
      paint(); return;
    }
    if (t.id === "tFail") {
      const r2 = S.tren.e.indexOf("running");
      if (r2 >= 0) { S.tren.e[r2] = "failed"; S.tren.det = NODOS[r2] + " fallo → retry"; paint(); setTimeout(() => { if (S.tren.e[r2] === "failed") { S.tren.e[r2] = "running"; paint(); } }, 1200); }
      return;
    }
    if (t.hasAttribute("data-sign")) { const i2 = +t.getAttribute("data-sign"); S.tren.led.push("FIRMA " + S.tren.props[i2]); S.tren.props.splice(i2, 1); paint(); return; }
    if (t.hasAttribute("data-rej")) { S.tren.props.splice(+t.getAttribute("data-rej"), 1); paint(); return; }
    if (t.hasAttribute("data-doc")) { S.aud.sel = t.getAttribute("data-doc"); paint(); return; }
    if (t.id === "aPin" && S.aud.sel) { if (S.aud.pins.indexOf(S.aud.sel) < 0) S.aud.pins.push(S.aud.sel); S.aud.out = "ANCLADO " + S.aud.sel; paint(); return; }
    if (t.id === "aSend" && S.aud.sel) { S.aud.out = "POST /puente/enviar\n" + JSON.stringify({ doc: S.aud.sel, anclas: S.aud.pins }, null, 2); paint(); return; }
    if (t.hasAttribute("data-bp")) { const id = t.getAttribute("data-bp"); S.vent.bp[id] = !S.vent.bp[id]; paint(); return; }
    if (t.id === "vRun") { runVent(); paint(); return; }
    if (t.id === "vReset") { S.vent = { i: 0, st: "lista", p: {}, bp: S.vent.bp, est: ["pending", "pending", "pending", "pending"], fotos: [null, null, null, null], in: S.vent.in, dsl: "" }; paint(); return; }
    if (t.id === "vDsl") { S.vent.dsl = JSON.stringify({ nodos: PROC.map((p, i) => ({ id: p[0], fase: p[1] })), dag: "LOCKED" }, null, 2); paint(); return; }
    if (t.id === "oAdd") { S.orq.pila.push(S.orq.lib); paint(); return; }
    if (t.hasAttribute("data-del")) { S.orq.pila.splice(+t.getAttribute("data-del"), 1); paint(); return; }
    if (t.id === "oRun") {
      let payload;
      try { payload = JSON.parse(S.orq.in); } catch { showErr("JSON invalido"); return; }
      const log = ["IN " + JSON.stringify(payload)];
      for (const k of S.orq.pila) {
        try { payload = LIB[k](payload); log.push(k + " → " + JSON.stringify(payload)); }
        catch (ex) { log.push("ERROR " + ex.message); break; }
      }
      S.orq.out = log.join("\n"); paint();
    }
  }

  function onChange(e) {
    const t = e.target;
    if (t.hasAttribute("data-model")) { const n = nodeBy(t.getAttribute("data-model")); if (n) n.modelId = t.value; paint(); }
    if (t.hasAttribute("data-role")) {
      const n2 = nodeBy(t.getAttribute("data-role"));
      if (n2) { const rl = role(t.value); n2.roleId = rl[0]; n2.label = rl[1]; n2.prompt = rl[3]; }
      paint();
    }
  }

  function onSide(e) {
    const t = e.target.closest("[data-close],[data-mv],[data-rm],button");
    if (!t) return;
    if (t.hasAttribute("data-close")) { S.panel = null; S.sel = null; paint(); return; }
    if (t.hasAttribute("data-rm") && S.nodes.length > 1) { S.nodes = S.nodes.filter(n => n.id !== t.getAttribute("data-rm")); S.sel = S.nodes[0].id; paint(); return; }
    if (t.hasAttribute("data-mv")) {
      const n = nodeBy(S.sel); if (!n) return;
      const i = S.nodes.indexOf(n), j = i + (+t.getAttribute("data-mv"));
      if (j < 0 || j >= S.nodes.length) return;
      [S.nodes[i], S.nodes[j]] = [S.nodes[j], S.nodes[i]]; paint(); return;
    }
    if (t.id === "sbAll") { S.nodes.forEach(n => { n.backend = S.sb.backend; n.timeout = S.sb.timeout; n.mem = S.sb.mem; }); paint(); }
  }

  function onSideChange(e) {
    const t = e.target;
    if (t.id === "outD") { S.dest = t.value; S.endpoint = dest(t.value)[2]; paint(); }
    if (t.id === "outE") S.endpoint = t.value;
    if (t.id === "sbB") targetSb().backend = t.value;
    if (t.id === "sbT") { targetSb().timeout = +t.value; paint(); }
    if (t.id === "sbM") { targetSb().mem = +t.value; paint(); }
  }

  function bind() {
    const canvas = $("#run-canvas"), side = $("#run-side");
    canvas.onclick = onCanvas;
    canvas.onchange = onChange;
    const inT = $("#inT"); if (inT) inT.oninput = function () { S.input = this.value; };
    const nL = $("#nL"); if (nL) nL.oninput = function () { const n = nodeBy(S.sel); if (n) n.label = this.value; };
    const nP = $("#nP"); if (nP) nP.oninput = function () { const n = nodeBy(S.sel); if (n) n.prompt = this.value; };
    const nI = $("#nI"); if (nI) nI.oninput = function () { const n = nodeBy(S.sel); if (n) n.input = this.value; };
    const nO = $("#nO"); if (nO) nO.oninput = function () { const n = nodeBy(S.sel); if (n) n.output = this.value; };
    const aq = $("#aq"); if (aq) aq.oninput = function () { S.aud.q = this.value; paint(); $("#aq").focus(); };
    const vIn = $("#vIn"); if (vIn) vIn.oninput = function () { S.vent.in = this.value; };
    const oIn = $("#oIn"); if (oIn) oIn.oninput = function () { S.orq.in = this.value; };
    const oLib = $("#oLib"); if (oLib) oLib.onchange = function () { S.orq.lib = this.value; };
    side.onclick = onSide;
    side.onchange = onSideChange;
  }

  let runT = null;
  $("#run-tabs").onclick = e => {
    const b = e.target.closest("[data-view]"); if (!b) return;
    S.view = b.getAttribute("data-view"); S.panel = null; paint();
  };
  $("#run-btnAdd").onclick = () => {
    S.view = "cascade";
    if (S.nodes.length >= 20) return;
    const n = mkNode("custom"); S.nodes.push(n); S.sel = n.id; S.panel = "node"; paint();
  };
  $("#run-btnSand").onclick = () => { S.view = "cascade"; S.panel = S.panel === "sand" ? null : "sand"; paint(); };
  $("#run-btnCode").onclick = () => { S.view = "cascade"; S.panel = S.panel === "code" ? null : "code"; paint(); };
  $("#run-btnRun").onclick = () => {
    S.view = "cascade";
    if (S.running) {
      S.running = false; clearInterval(runT);
      $("#run-btnRun").textContent = "Run";
      S.nodes.forEach(n => { if (n.status === "running") n.status = "idle"; });
      paint(); return;
    }
    S.panel = null; S.sel = null; S.running = true; S.cursor = 0; S.last = "";
    S.nodes.forEach(n => { n.status = "idle"; });
    $("#run-btnRun").textContent = "Parar";
    paint();
    runT = setInterval(() => {
      if (!S.running) { clearInterval(runT); return; }
      if (S.cursor === 0) { S.cursor = 1; if (S.nodes[0]) S.nodes[0].status = "running"; paint(); return; }
      const i = S.cursor - 1;
      if (i < S.nodes.length) {
        S.nodes[i].status = "done";
        if (S.nodes[i + 1]) S.nodes[i + 1].status = "running";
        S.cursor++; paint(); return;
      }
      S.running = false; clearInterval(runT);
      S.last = JSON.stringify({ answer: "Flujo " + S.nodes.length + " IA", destination: dest(S.dest)[1], endpoint: S.endpoint }, null, 2);
      $("#run-btnRun").textContent = "Run";
      S.sel = "out"; S.panel = "node"; paint();
    }, 500);
  };
  paint();
  return { state: S, paint };
}
