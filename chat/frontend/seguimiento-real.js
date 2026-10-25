// seguimiento-real.js — panel 3 «Planificación y seguimiento» con datos REALES. Antes llamaba a /chat/org/* (una ruta que este sitio no tiene: salia «Not Found» y quedaba vacío).
// Ahora: servidor (acciones status / estado / herramientas_estado), workflows y su cola, chats, actividad reciente y resumen de anclas. Nada inventado.
import { leer, escribir, KEYS } from "./almacen.js";
import { listaWF, listaProyectos } from "./objetivos-ancla.js";
import { el, boton, cargarCss } from "./ventanas-comun.js";
const LIVE = "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json";
const aplanar = (o, pre = "", out = []) => { if (o && typeof o === "object" && !Array.isArray(o)) Object.keys(o).slice(0, 30).forEach((k) => aplanar(o[k], pre + k + ".", out)); else out.push([pre.slice(0, -1) || "valor", Array.isArray(o) ? o.length + " elemento(s)" : String(o).slice(0, 120)]); return out; };
const irA = (vista) => { const b = document.querySelector('#navigation [data-view="' + vista + '"]'); if (b) b.click(); };
const chatsGuardados = () => { try { const a = JSON.parse(localStorage.getItem("riu_chats_v1") || "[]"); return Array.isArray(a) ? a : []; } catch (e) { return []; } };
const sesionActiva = () => { const c = chatsGuardados(); if (!c.length) return "general"; const i = Number(localStorage.getItem("riu_chat_activo")) || 0; return (c[Math.min(Math.max(i, 0), c.length - 1)] || {}).sesion || "general"; };
export function montarSeguimiento(root, { tell }) {
  if (root.querySelector(".sg-app")) return true;
  cargarCss("ventanas-comun"); cargarCss("paneles-reales");
  [...root.children].forEach((c) => { if (c.tagName !== "H1") c.style.display = "none"; });
  const app = el("div", "sg-app"); root.append(app);
  const sec = (titulo) => { const s = el("section", "sg-sec"); s.append(el("h2", "", titulo)); app.append(s); return s; };
  // ---- servidor ----
  const sS = sec("Servidor"), est = el("div", "vn-estado"), caja = el("div", "vn-lista");
  est.setAttribute("role", "status");
  async function servidor() {
    caja.replaceChildren(); est.textContent = "Consultando…"; let ok = 0;
    const acc = [["status", {}], ["estado", { sesion: sesionActiva() }], ["herramientas_estado", {}]];
    try {  // dirección del servidor: de cuándo es (los jobs de Hugging Face caducan; si es vieja, el servidor puede estar apagado)
      const r = await fetch(LIVE, { cache: "no-store" }), d = await r.json(), h = (Date.now() / 1000 - Number(d.updated)) / 3600;
      if (isFinite(h)) { const t = el("div", "vn-item sg-resp"); t.append(el("strong", "", "dirección del servidor (LIVE_URL)"), el("small", "", "actualizada hace " + (h < 1 ? Math.max(1, Math.round(h * 60)) + " min" : h.toFixed(1) + " h")), el("small", "", String(d.LIVE_URL || "").replace(/^https:\/\//, ""))); if (h > 6) t.append(el("small", "sg-alerta", "⚠ Puede estar apagado: los jobs de Hugging Face caducan. Hay que reiniciar el job.")); caja.append(t); }
    } catch (e) { /* sin red o sin acceso a GitHub: se omite */ }
    if (typeof window.RIU_ACCION !== "function") { est.textContent = "El chat todavía no tiene conexión con el servidor (abre el chat una vez)."; return; }
    for (const [a, p] of acc) {
      const t = el("div", "vn-item sg-resp"); t.append(el("strong", "", a));
      try { const r = await window.RIU_ACCION(a, p); ok++; aplanar(r).slice(0, 12).forEach(([k, v]) => t.append(el("small", "", k + ": " + v))); } catch (e) { t.append(el("small", "", "no respondió: " + e.message)); }
      caja.append(t);
    }
    est.textContent = ok ? "El servidor respondió " + ok + " de " + acc.length : "Sin respuesta del servidor. Revisa la conexión en el chat.";
  }
  sS.append(boton("Actualizar", "mini", servidor), est, caja);
  // ---- workflows y su cola ----
  const sW = sec("Workflows y su cola"), listaW = el("div", "vn-lista"); sW.append(listaW);
  function workflows() {
    listaW.replaceChildren(); const d = leer(KEYS.workflows, { lista: [] }), l = Array.isArray(d.lista) ? d.lista : [];
    if (!l.length) { listaW.append(el("div", "fila-desc", "Aún no hay workflows. Créalos en el chat: fila «workflow Loops code Yaiwes».")); return; }
    l.forEach((w) => {
      const card = el("div", "vn-entrada"), cola = Array.isArray(w.cola) ? w.cola : [], pend = cola.filter((e) => e.estado === "pendiente").length, env = cola.filter((e) => e.estado === "enviada").length, err = cola.filter((e) => e.estado === "error").length;
      const tg = boton(w.encendido ? "Encendido" : "Apagado · encender", "toggle" + (w.encendido ? " on" : ""), () => { const x = leer(KEYS.workflows, { lista: [] }), y = (x.lista || []).find((z) => z.id === w.id); if (y) { y.encendido = !y.encendido; escribir(KEYS.workflows, x); } workflows(); }); tg.setAttribute("aria-pressed", String(!!w.encendido));
      card.append(el("strong", "", w.nombre), el("small", "", pend + " pendiente(s) · " + env + " enviada(s) · " + err + " con error · " + (w.items || []).length + " ancla(s)"));
      cola.filter((e) => e.estado !== "enviada").slice(-6).forEach((e) => { const f = el("div", "vn-item"); f.append(el("span", "", (e.de === "ia" ? "IA" : "Tú") + ": " + String(e.texto).slice(0, 160) + (e.nota ? " · " + e.nota : "")), boton("Quitar", "mini", () => { const x = leer(KEYS.workflows, { lista: [] }), y = (x.lista || []).find((z) => z.id === w.id); if (y) { y.cola = (y.cola || []).filter((z) => z.id !== e.id); escribir(KEYS.workflows, x); } workflows(); })); card.append(f); });
      const acc = el("div", "vn-fila"); acc.append(tg, boton("Ir al chat para ejecutar", "mini", () => irA("chat"))); card.append(acc); listaW.append(card);
    });
  }
  // ---- chats ----
  const sC = sec("Chats"), listaC = el("div", "vn-lista"); sC.append(listaC);
  function chats() {
    listaC.replaceChildren(); const c = chatsGuardados(); let hist = {}; try { hist = JSON.parse(localStorage.getItem("riu_hist_v1") || "{}") || {}; } catch (e) {}
    if (!c.length) { listaC.append(el("div", "fila-desc", "Aún no hay chats guardados.")); return; }
    c.forEach((x, i) => { const h = hist[x.sesion], n = Array.isArray(h) ? h.length : h && typeof h === "object" ? Object.keys(h).length : 0; const f = el("div", "vn-item"); f.append(el("span", "", "Chat " + (i + 1) + " · " + String(x.sesion).slice(-6) + " · " + (x.anclados || []).length + " anclado(s) · " + n + " mensaje(s)"), boton("Abrir", "mini", () => { try { localStorage.setItem("riu_chat_activo", String(i)); } catch (e) {} irA("chat"); })); listaC.append(f); });
  }
  // ---- actividad reciente (la campana) ----
  const sA = sec("Actividad reciente"), listaA = el("div", "vn-lista"); sA.append(listaA);
  function actividad() {
    listaA.replaceChildren(); const a = leer("riu_avisos_v1", []), l = Array.isArray(a) ? a : [];
    if (!l.length) { listaA.append(el("div", "fila-desc", "Sin avisos todavía.")); return; }
    [...l].reverse().slice(0, 20).forEach((e) => { const txt = typeof e === "string" ? e : e.m || e.texto || e.text || e.msg || JSON.stringify(e), ts = typeof e === "object" ? e.t || e.ts : 0; listaA.append(el("div", "vn-item", (ts ? new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " · " : "") + String(txt).slice(0, 200))); });
    listaA.append(boton("Limpiar", "mini", () => { escribir("riu_avisos_v1", []); actividad(); }));
  }
  // ---- resumen de anclas ----
  const sR = sec("Resumen de anclas por objetivo"), listaR = el("div", "vn-lista"); sR.append(listaR);
  function resumen() {
    listaR.replaceChildren(); const n = (k) => ((leer(k, {}).items) || []).length;
    [["Constitución", n(KEYS.constitucion)], ["Agentes remotos", n(KEYS.agentes)], ["Sandbox", n(KEYS.sandbox)], ["Workflows", listaWF().reduce((s, w) => s + (w.items || []).length, 0)], ["Carpetas de proyecto", listaProyectos().reduce((s, p) => s + (p.items || []).length, 0)]].forEach(([t, v]) => listaR.append(el("div", "vn-item", t + ": " + v + " ancla(s)")));
  }
  workflows(); chats(); actividad(); resumen(); servidor();
  const rec = () => { if (!root.isConnected) { window.removeEventListener("riu:almacen", rec); return; } workflows(); resumen(); };
  window.addEventListener("riu:almacen", rec);
  return true;
}
