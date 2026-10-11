// ventana-workflows.js — ventana "Workflow Loops code Yaiwes": varios workflows, system prompt por workflow, anclas propias (misma lógica del anclaje),
// instrucciones desde el chat (/wf nombre instrucción) y desde la IA ([[WF:nombre]]…[[/WF]]) hacia su ventana de ejecución.
// Los workflows que ya están en curso se conectan con adaptadores (plugins): window.RIU_WORKFLOW_ADAPTERS[id] = { nombre, enviar(wf, entrada, ctx) }.
import { leer, escribir, KEYS, uid, hash } from "./almacen.js";
import { parsearBloquesWF, buscarWF, parsearSlashWF } from "./contexto.js";
import { el, boton, crearVentana, abrirVentana, agregarPill, seccionAnclas } from "./ventanas-comun.js";

export const ADAPTADORES = {
  chat: { nombre: "Chat (mensaje con el contexto del workflow)", enviar: async (wf, e, ctx) => {
    const m = ctx.q("#message"), f = ctx.q("#composer"); if (!m || !f) throw new Error("No encuentro la caja del chat");
    m.value = "[Workflow «" + wf.nombre + "»] " + e.texto; m.dispatchEvent(new Event("input", { bubbles: true }));
    if (f.requestSubmit) f.requestSubmit(); else f.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
  } },
  webhook: { nombre: "Webhook HTTPS (workflow en curso)", enviar: async (wf, e) => {
    const url = (wf.webhook || "").trim(); if (!/^https:\/\//i.test(url)) throw new Error("Falta la URL https del webhook");
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workflow: wf.nombre, id: wf.id, instruccion: e.texto, de: e.de, anclas: wf.items, system_prompt: wf.systemPrompt }) });
    if (!r.ok) throw new Error("El webhook respondió HTTP " + r.status);
  } },
};
window.RIU_WORKFLOW_ADAPTERS = window.RIU_WORKFLOW_ADAPTERS || {};
const adaptadores = () => Object.assign({}, ADAPTADORES, window.RIU_WORKFLOW_ADAPTERS);
const cargar = () => { const v = leer(KEYS.workflows, { lista: [], sel: null }); if (!Array.isArray(v.lista)) v.lista = []; return v; };
const guardar = (v) => escribir(KEYS.workflows, v);
const nuevoWF = (nombre) => ({ id: uid(), nombre, systemPrompt: "", encendido: false, adaptador: "chat", webhook: "", items: [], cola: [], vistos: [], creado: Date.now() });
const hora = (t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export function montarWorkflows({ root, q, tell }) {
  if (root.dataset.wf) return; root.dataset.wf = "1";
  const { sheet, caja } = crearVentana(root, { id: "ventana-workflows", titulo: "Workflow Loops code Yaiwes", css: "ventana-workflows" });
  const pill = agregarPill(q, "pill-workflows", "workflow ⌄", () => { pintar(); abrirVentana(root, sheet); });
  pill.style.display = "none";  // la entrada visible es la fila «workflow Loops code Yaiwes» del panel Selectores (selector-workflows.js)
  const cuerpo = el("div", "wf-cuerpo"); caja.append(cuerpo);
  const ctx = { q, tell };
  const marcar = () => pill.classList.toggle("on", cargar().lista.some((w) => w.encendido));
  const poner = (id, fn) => { const d = cargar(), w = d.lista.find((x) => x.id === id); if (!w) return; fn(w, d); guardar(d); };
  const entrada = (w, de, texto) => { w.cola.push({ id: uid(), t: Date.now(), de, texto, estado: "pendiente" }); if (w.cola.length > 200) w.cola.shift(); };
  async function enviar(wfId, eId) {
    const d = cargar(), w = d.lista.find((x) => x.id === wfId), e = w && w.cola.find((x) => x.id === eId); if (!e) return;
    const ad = adaptadores()[w.adaptador] || adaptadores().chat;
    try { await ad.enviar(w, e, ctx); e.estado = "enviada"; e.nota = ""; } catch (err) { e.estado = "error"; e.nota = err.message; tell("No se pudo enviar: " + err.message); }
    guardar(d); pintar();
  }
  function pintar() {
    const d = cargar(); cuerpo.replaceChildren(); marcar();
    const fila = el("div", "vn-fila"), sel = el("select", "vn-in"); sel.setAttribute("aria-label", "Workflow");
    d.lista.forEach((w) => { const o = el("option", "", (w.encendido ? "● " : "") + w.nombre); o.value = w.id; sel.append(o); });
    const w = d.lista.find((x) => x.id === d.sel) || d.lista[0];
    if (w) sel.value = w.id; else sel.hidden = true;
    sel.addEventListener("change", () => { const x = cargar(); x.sel = sel.value; guardar(x); pintar(); });
    const nom = el("input", "vn-in"); nom.placeholder = "Nombre del nuevo workflow"; nom.setAttribute("aria-label", "Nombre del nuevo workflow"); nom.maxLength = 40;
    const add = boton("＋ Añadir workflow", "mini", () => {
      let n = nom.value.trim(); if (!n) { tell("Escribe un nombre para el workflow"); return; }
      const x = cargar(); let k = n, i = 2; while (x.lista.some((y) => y.nombre.toLowerCase() === k.toLowerCase())) k = n + " " + i++;
      const nw = nuevoWF(k); x.lista.push(nw); x.sel = nw.id; guardar(x); nom.value = ""; pintar(); tell("Workflow creado: " + k);
    });
    fila.append(sel); cuerpo.append(fila); const f2 = el("div", "vn-fila"); f2.append(nom, add); cuerpo.append(f2);
    if (!w) { cuerpo.append(el("div", "fila-desc", "Aún no hay workflows. Añade uno para darle system prompt, anclas e instrucciones.")); return; }
    const enc = boton(w.encendido ? "Encendido" : "Apagado · encender", "toggle" + (w.encendido ? " on" : ""), () => { poner(w.id, (x) => { x.encendido = !x.encendido; }); pintar(); tell((w.encendido ? "Workflow apagado: " : "Workflow encendido: ") + w.nombre); });
    enc.setAttribute("aria-pressed", String(w.encendido));
    const borrar = boton("Borrar workflow", "mini rojo", () => { if (!confirm("¿Borrar el workflow «" + w.nombre + "» con sus anclas e instrucciones?")) return; const x = cargar(); x.lista = x.lista.filter((y) => y.id !== w.id); x.sel = x.lista[0] ? x.lista[0].id : null; guardar(x); pintar(); });
    const f3 = el("div", "vn-fila"); f3.append(enc, borrar); cuerpo.append(f3);
    cuerpo.append(el("div", "vn-estado", "Encendido = su system prompt, sus anclas y los agentes remotos viajan con cada mensaje del chat."));
    const rn = el("input", "vn-in"); rn.value = w.nombre; rn.maxLength = 40; rn.setAttribute("aria-label", "Nombre");
    rn.addEventListener("change", () => { const n = rn.value.trim(); if (!n) { rn.value = w.nombre; return; } const x = cargar(); if (x.lista.some((y) => y.id !== w.id && y.nombre.toLowerCase() === n.toLowerCase())) { tell("Ya existe un workflow con ese nombre"); rn.value = w.nombre; return; } poner(w.id, (y) => { y.nombre = n; }); pintar(); });
    cuerpo.append(el("div", "vn-t", "Nombre"), rn);
    const sp = el("textarea", "vn-ta"); sp.value = w.systemPrompt; sp.placeholder = "System prompt del workflow…"; sp.setAttribute("aria-label", "System prompt");
    sp.addEventListener("change", () => poner(w.id, (y) => { y.systemPrompt = sp.value.slice(0, 8000); }));
    cuerpo.append(el("div", "vn-t", "System prompt"), sp);
    const ad = el("select", "vn-in"); ad.setAttribute("aria-label", "Adaptador");
    Object.entries(adaptadores()).forEach(([k, a]) => { const o = el("option", "", a.nombre || k); o.value = k; ad.append(o); }); ad.value = adaptadores()[w.adaptador] ? w.adaptador : "chat";
    ad.addEventListener("change", () => { poner(w.id, (y) => { y.adaptador = ad.value; }); pintar(); });
    cuerpo.append(el("div", "vn-t", "Conectar con la ejecución"), ad);
    if (w.adaptador === "webhook") { const wh = el("input", "vn-in"); wh.placeholder = "https://… (endpoint del workflow en curso)"; wh.value = w.webhook || ""; wh.setAttribute("aria-label", "URL del webhook"); wh.addEventListener("change", () => poner(w.id, (y) => { y.webhook = wh.value.trim(); })); cuerpo.append(wh); }
    seccionAnclas(cuerpo, { titulo: "Anclas de «" + w.nombre + "»", leerTokens: () => (cargar().lista.find((x) => x.id === w.id) || { items: [] }).items, escribirTokens: (ts) => poner(w.id, (y) => { y.items = ts; }), destino: { tipo: "wf", id: w.id }, tell });
    cuerpo.append(el("div", "vn-t", "Ventana de ejecución"));
    const ins = el("input", "vn-in"); ins.placeholder = "Escribe una instrucción para este workflow…"; ins.setAttribute("aria-label", "Instrucción");
    const esc = boton("Escribir en la ejecución", "mini", () => { const t = ins.value.trim(); if (!t) return; poner(w.id, (y) => entrada(y, "usuario", t)); ins.value = ""; pintar(); });
    ins.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); esc.click(); } });
    const f4 = el("div", "vn-fila"); f4.append(ins, esc); cuerpo.append(f4);
    const cola = el("div", "vn-cola"); const pend = w.cola.filter((e) => e.estado !== "enviada");
    if (pend.length > 1) cola.append(boton("Enviar todas las pendientes (" + pend.length + ")", "mini", async () => { for (const e of pend) await enviar(w.id, e.id); }));
    if (!w.cola.length) cola.append(el("div", "fila-desc", "Sin instrucciones. Desde el chat: /wf " + w.nombre + " tu instrucción. La IA también puede escribir aquí con [[WF:" + w.nombre + "]]…[[/WF]]."));
    [...w.cola].reverse().forEach((e) => {
      const b = el("div", "vn-entrada"); b.dataset.estado = e.estado;
      b.append(el("small", "", (e.de === "ia" ? "IA" : "Tú") + " · " + hora(e.t) + " · " + e.estado + (e.nota ? " · " + e.nota : "")), el("div", "", e.texto));
      const ac = el("div", "vn-fila"); ac.append(boton(e.estado === "enviada" ? "Reenviar" : "Enviar a ejecutar", "mini", () => enviar(w.id, e.id)), boton("Quitar", "mini", () => { poner(w.id, (y) => { y.cola = y.cola.filter((z) => z.id !== e.id); }); pintar(); }));
      b.append(ac); cola.append(b);
    });
    cuerpo.append(cola);
  }
  // instrucciones desde el chat: /wf nombre instrucción (no se envía a la IA, va a la ventana de ejecución)
  root.addEventListener("submit", (ev) => {
    if (!ev.target || ev.target.id !== "composer") return;
    const m = q("#message"); if (!m) return;
    const d = cargar(), r = parsearSlashWF(m.value, d.lista); if (!r) return;
    ev.preventDefault(); ev.stopPropagation();
    if (!r.wf) { tell(d.lista.length ? "Workflows: " + d.lista.map((w) => w.nombre).join(", ") + ". Uso: /wf nombre instrucción" : "Aún no hay workflows: créalo en la pastilla workflow"); return; }
    if (!r.texto) { tell("Escribe la instrucción después de " + r.wf.nombre); return; }
    poner(r.wf.id, (y) => entrada(y, "usuario", r.texto)); m.value = ""; m.dispatchEvent(new Event("input", { bubbles: true })); tell("Instrucción escrita en «" + r.wf.nombre + "»");
    if (!sheet.hidden) pintar();
  }, true);
  // instrucciones de la IA: [[WF:nombre]]…[[/WF]] en sus respuestas
  const hist = q("#histories");
  if (hist) {
    let p = 0;
    const revisar = () => {
      p = 0; const d = cargar(); let cambio = false;
      hist.querySelectorAll(".message:not(.user):not(.pending) .txt").forEach((sp) => parsearBloquesWF(sp.textContent).forEach((b) => {
        const w = buscarWF(b.ref, d.lista); if (!w) return;
        const h = hash(w.id + b.texto); if (w.vistos.includes(h)) return;
        w.vistos.push(h); if (w.vistos.length > 300) w.vistos.shift(); entrada(w, "ia", b.texto); cambio = true; tell("La IA escribió una instrucción en «" + w.nombre + "»");
      }));
      if (cambio) { guardar(d); if (!sheet.hidden) pintar(); }
    };
    new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true });
  }
  const onAlm = () => { if (!root.isConnected) { window.removeEventListener("riu:almacen", onAlm); return; } marcar(); };
  window.addEventListener("riu:almacen", onAlm); marcar();
}
