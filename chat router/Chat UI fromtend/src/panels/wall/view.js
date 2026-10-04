import { SIX, YAI, WF, COL, ST, SL, CST, PCT0, RED, N } from "./data.js";
import { persistWall, exportWallVersion } from "./state.js";

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

export function createWall(root, context, state) {
  const $ = sel => root.querySelector(sel);
  const ov = n => {
    const o = state.ov[n.id] || {};
    return {
      st: o.st || n.st,
      col: o.col || CST[o.st || n.st] || n.st,
      pct: o.pct != null ? o.pct : (n.pct != null ? n.pct : PCT0[o.st || n.st] || 0)
    };
  };
  const find = (id, arr) => {
    for (const n of arr) { if (n.id === id) return n; const x = n.kids && find(id, n.kids); if (x) return x; }
    return null;
  };
  const allTrees = () => SIX.concat(YAI, WF).concat(state.extra.map(e => e.node));
  const findAny = id => find(id, allTrees());
  const worst = nodes => {
    const rank = { rojo: 0, naranja: 1, amarillo: 2, verde: 3 };
    let w = "verde", i = 9;
    (function walk(a) { a.forEach(n => { const c = ov(n).col; const r = rank[c]; if (r < i) { i = r; w = c; } if (n.kids) walk(n.kids); }); })(nodes);
    return w;
  };
  const toast = m => {
    const t = $("#wall-toast"); t.textContent = m; t.style.display = "block";
    setTimeout(() => { t.style.display = "none"; }, 1600);
  };
  const rowHTML = (n, depth) => {
    const o = ov(n);
    const red = RED.has(n.seg) ? "wall-redband" : "";
    return `<button type="button" class="wall-row ${red}" data-wall-tap="${n.id}">
      <span class="wall-dot ${o.col}"></span>
      <span class="wall-nm">${"│ ".repeat(Math.max(0, depth - 1))}${depth ? "├─ " : ""}<span class="wall-path">${esc(n.name)}</span></span>
      <span class="wall-meta">${o.pct}%</span>
    </button>` + (n.kids && n.kids.length ? `<div class="wall-kids">${n.kids.map(k => rowHTML(k, depth + 1)).join("")}</div>` : "");
  };
  const render = () => {
    $("#wall-six").innerHTML = SIX.map(n => rowHTML(n, 0)).join("");
    $("#wall-yai").innerHTML = YAI.map(n => rowHTML(n, 0)).join("");
    $("#wall-wf").innerHTML = WF.map(n => rowHTML(n, 0)).join("");
    $("#wall-extra").innerHTML = state.extra.map(e => rowHTML(e.node, 0)).join("") || '<div style="color:var(--dim);padding:6px;font-size:10px">ninguna</div>';
    $("#wall-ver").textContent = "v" + state.v;
    $("#wall-mfile").classList.toggle("on", state.mode === "file");
    $("#wall-mblock").classList.toggle("on", state.mode === "block");
  };
  const sheetBox = html => { $("#wall-sheetbox").innerHTML = html; $("#wall-sheet").classList.add("on"); };
  const closeSheet = () => $("#wall-sheet").classList.remove("on");
  const pal = n => {
    const o = ov(n);
    return `<div class="wall-k">COLOR</div>
      <div class="wall-sts">${COL.map(c => `<button type="button" class="${o.col === c ? "on" : ""}" data-wall-col="${n.id}|${c}">${c}</button>`).join("")}</div>
      <div class="wall-k">STATUS</div>
      <div class="wall-sts">${ST.map(s => `<button type="button" class="${o.st === s ? "on" : ""}" data-wall-st="${n.id}|${s}">${SL[s]}</button>`).join("")}</div>
      <div class="wall-k">% CODE</div>
      <div class="wall-sts">${[0, 10, 25, 40, 55, 70, 85, 100].map(p => `<button type="button" class="${o.pct === p ? "on" : ""}" data-wall-pct="${n.id}|${p}">${p}%</button>`).join("")}</div>`;
  };
  const noteField = (n, label) =>
    `<textarea class="wall-note" rows="4" placeholder="${label}" data-wall-note="${n.id}">${esc(state.notes[n.id] || "")}</textarea>`;
  const openFile = n => {
    const o = ov(n);
    sheetBox(`
      <div class="wall-k" style="color:var(--blue)">ARCHIVO · ${esc(n.seg || "—")}</div>
      <h3>${esc(n.name)}</h3>
      <div class="wall-micro">${esc(n.flow || "—")}</div>
      <div class="wall-xray"><b>Qué hace.</b> ${esc(n.desc)}</div>
      <div class="wall-xray"><b>X-ray.</b> ${esc(n.xray)}</div>
      <div class="wall-xray"><b>Destino ROOT MAP.</b> ${esc(n.dest)}</div>
      <div class="wall-xray"><b>Ahora.</b> ${SL[o.st]} · ${o.col} · ${o.pct}%</div>
      ${pal(n)}
      ${noteField(n, "nota de este archivo")}
      <button type="button" class="wall-p" data-wall-share="${n.id}">Compartir archivo</button>
      <button type="button" class="wall-p wall-ghost" data-wall-close="1">Cerrar</button>`);
  };
  const openBlock = n => {
    const o = ov(n);
    const files = (n.kids || []).map(k => { const x = ov(k); return `├─ [${x.col} ${x.pct}%] ${k.name}`; }).join("\n") || "(hoja)";
    sheetBox(`
      <div class="wall-k" style="color:${RED.has(n.seg) ? "var(--rojo)" : "var(--blue)"}">BLOQUE · seg ${esc(n.seg || "—")}${RED.has(n.seg) ? " · ROJO" : ""}</div>
      <h3>${esc(n.name)}</h3>
      <div class="wall-micro">${esc(n.flow || "—")}</div>
      <div class="wall-xray"><b>Qué hace el bloque.</b> ${esc(n.desc)}</div>
      <div class="wall-xray"><b>Problema X-ray.</b> ${esc(n.xray)}</div>
      <div class="wall-xray"><b>Destino.</b> ${esc(n.dest)}</div>
      <div class="wall-micro" style="white-space:pre">${esc(files)}</div>
      <div class="wall-xray"><b>Rollup.</b> ${SL[o.st]} · ${o.col} · ${o.pct}%</div>
      ${pal(n)}
      ${noteField(n, "nota del bloque")}
      <button type="button" class="wall-p" data-wall-share="${n.id}">Compartir bloque</button>
      <button type="button" class="wall-p wall-ghost" data-wall-close="1">Cerrar</button>`);
  };
  const tap = id => {
    const n = findAny(id); if (!n) return;
    state.sel = id;
    if (state.mode === "file" && !(n.kids && n.kids.length)) openFile(n);
    else openBlock(n);
  };
  const reopen = id => {
    const n = findAny(id); if (!n) return;
    (state.mode === "file" && !(n.kids && n.kids.length) ? openFile : openBlock)(n);
  };
  const setSt = (id, s) => {
    state.ov[id] = Object.assign({}, state.ov[id], { st: s, col: CST[s], pct: state.ov[id]?.pct != null ? state.ov[id].pct : PCT0[s] });
    persistWall(state); render(); reopen(id);
  };
  const setCol = (id, c) => { state.ov[id] = Object.assign({}, state.ov[id], { col: c }); persistWall(state); render(); reopen(id); };
  const setPct = (id, p) => { state.ov[id] = Object.assign({}, state.ov[id], { pct: p }); persistWall(state); render(); reopen(id); };
  const addRoot = () => {
    const title = $("#wall-ntitle").value || $("#wall-clone").selectedOptions[0].text;
    const md = $("#wall-nmd").value || "";
    const node = N("XR" + Date.now(), title, "pendiente", 0,
      "nueva raíz → bloque único → compartir",
      md || "Raíz añadida. Solo bloque, no árbol de archivos.",
      "Usuario pegó markdown. Sin hojas de archivo.", "extra/" + title, "00");
    state.extra.push({ node, md });
    $("#wall-ntitle").value = ""; $("#wall-nmd").value = "";
    persistWall(state); render(); toast("raíz-bloque añadida");
  };
  const blockText = n => {
    const o = ov(n);
    const six = SIX.map(rr => { const x = ov(rr); return `  ${rr.name} [${x.col} ${x.pct}%]`; }).join("\n");
    return `# YAIWES ${n.id}\n## RAÍZ\n\`\`\`\nagentes/\n${six}\n\`\`\`\n## NODO\n${n.name}\nFlujo: ${n.flow}\nDestino: ${n.dest}\nEstado: ${SL[o.st]} · ${o.col} · ${o.pct}%\n## DESC\n${n.desc}\n## XRAY\n${n.xray}\n## NOTA\n${state.notes[n.id] || ""}\n## LEY\nEnchufe IN+OUT cada file nuevo. Destino=ROOT MAP. Formato A22. No from-scratch.`;
  };
  const shareNode = async id => {
    const n = findAny(id); if (!n) return;
    const text = blockText(n);
    try {
      if (navigator.share) await navigator.share({ title: "YAIWES " + n.name, text });
      else await navigator.clipboard.writeText(text);
      toast("share/copiado");
    } catch {
      try { await navigator.clipboard.writeText(text); toast("copiado"); } catch { toast("cancel"); }
    }
  };
  root.addEventListener("click", e => {
    const el = e.target.closest("[data-wall-tap],[data-wall-col],[data-wall-st],[data-wall-pct],[data-wall-share],[data-wall-close],[data-wall-mode],[data-wall-add],[data-wall-save],[data-wall-sharesel]");
    if (!el) return;
    if (el.dataset.wallTap) return tap(el.dataset.wallTap);
    if (el.dataset.wallMode) { state.mode = el.dataset.wallMode; return render(); }
    if (el.dataset.wallCol) { const [id, c] = el.dataset.wallCol.split("|"); return setCol(id, c); }
    if (el.dataset.wallSt) { const [id, s] = el.dataset.wallSt.split("|"); return setSt(id, s); }
    if (el.dataset.wallPct) { const [id, p] = el.dataset.wallPct.split("|"); return setPct(id, +p); }
    if (el.dataset.wallShare) return shareNode(el.dataset.wallShare);
    if (el.dataset.wallClose) return closeSheet();
    if (el.dataset.wallAdd) return addRoot();
    if (el.dataset.wallSave) { const v = exportWallVersion(state); $("#wall-ver").textContent = "v" + v; return toast("v" + v + " → Descargas"); }
    if (el.dataset.wallSharesel) return shareNode(state.sel || "WF.runner");
    if (e.target === $("#wall-sheet")) closeSheet();
  });
  root.addEventListener("input", e => {
    const id = e.target?.dataset?.wallNote;
    if (id) { state.notes[id] = e.target.value; persistWall(state); }
  });
  $("#wall-sheet").addEventListener("click", e => { if (e.target === e.currentTarget) closeSheet(); });
  render();
  return { render, state };
}
