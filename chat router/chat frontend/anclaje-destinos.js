// anclaje-destinos.js — en la ventana de Anclaje: "Anclar a" Chat / Constitución / Workflows / Agentes remotos. Lo nuevo que anclas (pegar, subir, archivos)
// se reparte a los destinos encendidos; si el Chat está apagado, sale del anclaje del chat. No toca chat-ancla.js: observa lo anclado.
import { leer, escribir, KEYS } from "./almacen.js";
import { dameDestinos, dameWF, dameCon } from "./contexto.js";
import { el, boton, cargarCss } from "./ventanas-comun.js";
const DEST = [["chat", "Chat"], ["constitucion", "Constitución"], ["workflows", "Workflows"], ["agentes", "Agentes remotos"]];
const unico = (a) => [...new Set(a)];
function aniadirCon(tokens) { const c = dameCon(); c.items = unico([...(c.items || []), ...tokens]); escribir(KEYS.constitucion, c); }
function aniadirWF(id, tokens) { const d = leer(KEYS.workflows, { lista: [] }), w = (d.lista || []).find((x) => x.id === id); if (!w) return; w.items = unico([...(w.items || []), ...tokens]); escribir(KEYS.workflows, d); }
export function repartir(tokens, temporal) {  // devuelve true si el Chat también conserva los tokens
  const d = dameDestinos();
  if (temporal) { if (temporal.tipo === "wf") aniadirWF(temporal.id, tokens); else if (temporal.tipo === "constitucion") aniadirCon(tokens); return false; }
  if (d.activos.includes("constitucion")) aniadirCon(tokens);
  if (d.activos.includes("workflows")) d.wfSel.forEach((id) => aniadirWF(id, tokens));
  if (d.activos.includes("agentes")) {
    const urls = tokens.filter((t) => /^(enlace|raiz):https?:\/\//i.test(t)).map((t) => t.replace(/^[a-z]+:/, ""));
    if (urls.length) { const x = dameDestinos(); urls.forEach((u) => { if (!x.agentes.some((a) => a.url === u)) x.agentes.push({ url: u, sdk: true }); }); escribir(KEYS.destinos, x); }
  }
  return d.activos.includes("chat");
}
export function montarDestinos({ root, q, tell }) {
  const caja = q("#ventana-ancla .va-caja"); if (!caja || caja.dataset.destinos) return; caja.dataset.destinos = "1";
  cargarCss("ventanas-comun");
  const fila = el("div", "vn-sec vn-destinos"); const head = caja.querySelector(".va-head"); if (head) head.after(fila); else caja.prepend(fila);
  const guardar = (x) => escribir(KEYS.destinos, x);
  function pintar() {
    const d = dameDestinos(); fila.replaceChildren(el("div", "vn-t", "Anclar a · lo nuevo que ancles va a los destinos encendidos"));
    const bs = el("div", "vn-fila");
    DEST.forEach(([id, nom]) => {
      const on = d.activos.includes(id);
      const b = boton(nom, "toggle" + (on ? " on" : ""), () => { const x = dameDestinos(), s = new Set(x.activos); if (s.has(id)) s.delete(id); else s.add(id); if (!s.size) s.add("chat"); x.activos = [...s]; guardar(x); pintar(); });
      b.setAttribute("aria-pressed", String(on)); bs.append(b);
    });
    fila.append(bs);
    if (d.activos.includes("workflows")) {
      const wfs = dameWF(), l = el("div", "vn-traer");
      if (!wfs.length) l.append(el("div", "fila-desc", "Aún no hay workflows: créalos en la pastilla workflow."));
      wfs.forEach((w) => { const lab = el("label", "vn-check"), c = el("input"); c.type = "checkbox"; c.checked = d.wfSel.includes(w.id); c.addEventListener("change", () => { const x = dameDestinos(); x.wfSel = c.checked ? unico([...x.wfSel, w.id]) : x.wfSel.filter((i) => i !== w.id); guardar(x); }); lab.append(c, el("span", "", w.nombre)); l.append(lab); });
      fila.append(l);
    }
    if (d.activos.includes("agentes") || d.agentes.length) {
      const l = el("div", "vn-lista");
      if (!d.agentes.length) l.append(el("div", "fila-desc", "Pega el enlace del repo de un agente remoto: se ancla su código fuente junto con la SDK."));
      d.agentes.forEach((a) => {
        const f = el("div", "vn-item"), sdk = boton("SDK", "mini" + (a.sdk ? " on" : ""), () => { const x = dameDestinos(); const y = x.agentes.find((z) => z.url === a.url); if (y) y.sdk = !y.sdk; guardar(x); pintar(); });
        sdk.setAttribute("aria-pressed", String(!!a.sdk));
        f.append(el("span", "", "🤖 " + a.url), sdk, boton("✕", "mini", () => { const x = dameDestinos(); x.agentes = x.agentes.filter((z) => z.url !== a.url); guardar(x); pintar(); })); l.append(f);
      });
      fila.append(l);
    }
  }
  pintar();
  const cont = q("#anclados"), snap = {};
  const revisar = () => {
    const api = window.RIU_CHAT; if (!api) return; const c = api.chat(); if (!c) return;
    const ahora = [...c.anclados], prev = snap[c.sesion]; snap[c.sesion] = ahora; if (!prev) return;
    const nuevos = ahora.filter((t) => !prev.includes(t)); if (!nuevos.length) return;
    const temporal = (window.RIU_ANCLAS || {}).temporal || null;
    const chatTambien = repartir(nuevos, temporal); if (temporal) window.RIU_ANCLAS.temporal = null;
    if (!chatTambien) { nuevos.forEach((t) => c.anclados.delete(t)); snap[c.sesion] = [...c.anclados]; api.pintar(); }
    tell(chatTambien ? "Anclado en el chat y en los destinos encendidos" : "Anclado fuera del chat, en los destinos elegidos");
    if (!root.isConnected) return; pintar();
  };
  if (cont) new MutationObserver(revisar).observe(cont, { childList: true, subtree: true, characterData: true });
  revisar();
}
