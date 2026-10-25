// anclaje-mejoras.js — 20 mejoras de 0 fricción para el sistema de anclas. Actuan sobre la MISMA ventana de Anclaje, con cualquier objetivo.
//  1 deshacer · 2 quitar todo con deshacer · 3 contadores · 4 buscador · 5 fijar ⭐ · 6 silenciar (sigue anclado, no viaja) · 7 resumen de pegado
//  8 copiar todo · 9 pegar del portapapeles · 10 exportar/importar · 11 copiar a otro objetivo · 12 abrir enlace · 13 ver completo · 14 etiqueta
//  15 medidor de contexto · 16 recientes · 17 «también en» · 18 resalta lo nuevo · 19 Ctrl+Z · 20 orden por tipo
import { leer, escribir, KEYS } from "./almacen.js";
import { crearObjetivo, listaWF, listaProyectos } from "./objetivos-ancla.js";
import { K_MUTE, K_PIN, K_ALIAS } from "./contexto.js";
import { el, boton, cargarCss } from "./ventanas-comun.js";
const K_REC = "riu_recientes_anclas_v1", RESUMEN = /^(enlace|raiz|handoff|constitucion):/;
const mostrar = (a) => (a.startsWith("raiz:") ? "📁 " : a.startsWith("handoff:") ? "📌 " : a.startsWith("constitucion:") ? "📜 Constitución: " : "🔗 ") + a.replace(/^(enlace|raiz|handoff|constitucion):/, "");
const ORD = (a) => (a.startsWith("enlace:") ? 1 : a.startsWith("raiz:") ? 2 : a.startsWith("handoff:") ? 3 : 4);
const obj = () => (window.RIU_OBJETIVO_ANCLA ? window.RIU_OBJETIVO_ANCLA() : window.RIU_CHAT ? window.RIU_CHAT.chat() : null);
const clave = () => { const o = obj(); return o ? o.sesion : "general"; };
const porClave = (k) => { const l = leer(k, {})[clave()]; return Array.isArray(l) ? l : []; };
const ponerPorClave = (k, l) => { const t = leer(k, {}); t[clave()] = [...new Set(l)]; escribir(k, t); };
const destinos = () => [["chat", "Chat"], ["constitucion", "Constitución"], ...listaWF().map((w) => ["workflows:" + w.id, "Workflow · " + w.nombre]), ["agentes", "Agentes remotos"], ...listaProyectos().map((p) => ["proyecto:" + p.nombre, "Proyecto · " + p.nombre]), ["sandbox", "Sandbox"]];
function agregarA(d, tok) {
  if (d === "chat") { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (!c) return false; c.anclados.add(tok); window.RIU_CHAT.pintar(); return true; }
  const i = d.indexOf(":"), o = crearObjetivo(i < 0 ? d : d.slice(0, i), i < 0 ? undefined : d.slice(i + 1)); if (!o) return false; o.anclados.add(tok); return true;
}
function tambienEn(tok) {
  const en = [], c = window.RIU_CHAT && window.RIU_CHAT.chat(), k = clave();
  if (c && c.sesion !== k && c.anclados.has(tok)) en.push("Chat");
  if (k !== "constitucion" && (leer(KEYS.constitucion, {}).items || []).includes(tok)) en.push("Constitución");
  (leer(KEYS.workflows, { lista: [] }).lista || []).forEach((w) => { if (k !== "wf:" + w.id && (w.items || []).includes(tok)) en.push("Workflow " + w.nombre); });
  [["agentes", KEYS.agentes, "Agentes"], ["sandbox", KEYS.sandbox, "Sandbox"]].forEach(([n, K, t]) => { if (k !== n && (leer(K, {}).items || []).includes(tok)) en.push(t); });
  (leer("riu_proy_v1", {}).global || []).forEach((p) => { if (k !== "proyecto:" + p.nombre && (p.items || []).includes(tok)) en.push("Proyecto " + p.nombre); });
  return en;
}
const bajar = (nombre, texto) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([texto], { type: "application/json" })); a.download = nombre; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); };
export function montarMejorasAncla({ root, q, tell }) {
  const caja = q("#ventana-ancla .va-caja"), resumen = q("#anc-resumen"); if (!caja || !resumen || caja.dataset.mej) return; caja.dataset.mej = "1"; cargarCss("anclaje-mejoras");
  const barra = el("div", "vn-sec am-barra"), ref = caja.querySelector(".vn-destinos") || caja.querySelector(".va-head"); if (ref) ref.after(barra); else caja.prepend(barra);
  let pila = [], vistos = new Set(), claveVista = null, filtro = "";
  const tokens = () => { const o = obj(); return o ? [...o.anclados] : []; };
  const refrescar = () => { try { if (window.RIU_CHAT && !window.RIU_OBJETIVO_ANCLA) window.RIU_CHAT.pintar(); } catch (e) {} if (window.RIU_ANCLA_REFRESCAR) window.RIU_ANCLA_REFRESCAR(); };
  const aviso = el("div", "am-aviso"); aviso.hidden = true; let tAviso = 0;
  const avisar = (txt, conDeshacer) => { aviso.replaceChildren(el("span", "", txt)); if (conDeshacer) aviso.append(boton("Deshacer", "mini", deshacer)); aviso.hidden = false; clearTimeout(tAviso); tAviso = setTimeout(() => { aviso.hidden = true; }, 9000); };
  const snap = () => { const o = obj(); if (!o) return; pila.push({ k: clave(), t: [...o.anclados] }); if (pila.length > 8) pila.shift(); botDes.disabled = false; };
  function deshacer() {
    const s = pila.pop(); botDes.disabled = !pila.length; if (!s) { tell("Nada que deshacer"); return; }
    const o = obj(); if (!o || clave() !== s.k) { pila.push(s); tell("Vuelve al objetivo donde quitaste eso"); return; }
    s.t.forEach((t) => o.anclados.add(t)); aviso.hidden = true; refrescar(); tell("Deshecho");
  }
  // ---- barra de herramientas ----
  const buscar = el("input", "vn-in"); buscar.type = "search"; buscar.placeholder = "Buscar en lo anclado y en los archivos…"; buscar.autocomplete = "off"; buscar.setAttribute("aria-label", "Buscar en lo anclado");
  buscar.addEventListener("input", () => { filtro = buscar.value.trim().toLowerCase(); aplicarFiltro(); });
  const botDes = boton("↶ Deshacer", "mini", deshacer); botDes.disabled = true;
  const botCop = boton("Copiar todo", "mini", async () => { try { await navigator.clipboard.writeText(tokens().map((t) => t.replace(/^[a-z]+:/, "")).join("\n")); tell("Copiado: " + tokens().length + " ancla(s)"); } catch (e) { tell("No se pudo copiar"); } });
  const botPeg = boton("Pegar y anclar", "mini", async () => {
    try { const t = await navigator.clipboard.readText(); const ta = q("#anc-pegar"); if (!ta || !t.trim()) { tell("El portapapeles está vacío"); return; } ta.value = t; ta.dispatchEvent(new Event("input", { bubbles: true })); const b = [...caja.querySelectorAll("button")].find((x) => x.textContent.trim() === "Anclar"); if (b) b.click(); } catch (e) { tell("Permite el acceso al portapapeles o pega a mano"); }
  });
  const botExp = boton("Exportar", "mini", () => { const k = clave(); bajar("anclas-" + k.replace(/[^a-z0-9]+/gi, "_") + ".json", JSON.stringify({ objetivo: k, anclas: tokens(), fijas: porClave(K_PIN), silenciadas: porClave(K_MUTE), etiquetas: leer(K_ALIAS, {})[k] || {} }, null, 2)); tell("Anclas exportadas"); });
  const inp = el("input"); inp.type = "file"; inp.accept = "application/json,.json"; inp.hidden = true;
  inp.addEventListener("change", async () => {
    const f = inp.files && inp.files[0]; if (!f) return; snap();
    try {
      const d = JSON.parse(await f.text()), o = obj(); if (!o || !Array.isArray(d.anclas)) throw new Error("no es un archivo de anclas");
      const ok = d.anclas.filter((t) => typeof t === "string" && t.length < 2000).slice(0, 500); ok.forEach((t) => o.anclados.add(t));
      if (Array.isArray(d.fijas)) ponerPorClave(K_PIN, [...porClave(K_PIN), ...d.fijas.filter((t) => typeof t === "string")]);
      refrescar(); tell("Importadas " + ok.length + " ancla(s)"); avisar("Importadas " + ok.length, true);
    } catch (e) { tell("No se pudo importar: " + e.message); }
    inp.value = "";
  });
  const botImp = boton("Importar", "mini", () => inp.click());
  const fila = el("div", "vn-fila"); fila.append(botDes, botCop, botPeg, botExp, botImp, inp);
  const rec = el("div", "vn-fila am-rec"), medidor = el("div", "vn-estado am-med");
  barra.append(el("div", "vn-t", "Herramientas de anclaje"), buscar, fila, aviso, rec, medidor);
  const pintarRec = () => { rec.replaceChildren(); const l = (leer(K_REC, {}).l || []).slice(0, 6); if (l.length) rec.append(el("span", "vn-estado", "Recientes:")); l.forEach((u) => rec.append(boton(u.replace(/^https?:\/\//, "").slice(0, 28), "mini", () => { const ta = q("#anc-pegar"); if (!ta) return; ta.value = u; ta.dispatchEvent(new Event("input", { bubbles: true })); const b = [...caja.querySelectorAll("button")].find((x) => x.textContent.trim() === "Anclar"); if (b) b.click(); }))); };
  // ---- pegado: resumen y recientes ----
  const pegar = q("#anc-pegar");
  if (pegar) pegar.addEventListener("paste", (e) => {
    const antes = tokens().length, txt = (e.clipboardData && e.clipboardData.getData("text")) || "", urls = [...new Set(txt.match(/https?:\/\/[^\s]+/g) || [])];
    if (urls.length) { const r = (leer(K_REC, {}).l || []).filter((u) => !urls.includes(u)); escribir(K_REC, { l: [...urls, ...r].slice(0, 12) }); }
    setTimeout(() => { const n = tokens().length - antes, rep = Math.max(0, urls.length - n); if (urls.length) tell(n + " nuevo(s)" + (rep ? " · " + rep + " repetido(s)" : "")); pintarRec(); }, 450);
  });
  // ---- quitar con deshacer (incluye «Quitar todos») ----
  caja.addEventListener("click", (e) => {
    const b = e.target.closest && e.target.closest("button"); if (!b) return;
    if (!((b.closest("#anc-resumen") && /✕|Quitar/.test(b.textContent) && !b.closest(".am-bandeja")) || b.id === "anc-ninguno")) return;
    const antes = tokens().length; snap(); setTimeout(() => { const d = antes - tokens().length; if (d > 0) avisar("Quitaste " + d + " ancla(s)", true); }, 900);
  }, true);
  caja.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); deshacer(); } });
  // ---- filas: bandeja de acciones, «también en», fijas, silenciadas, orden y resaltado ----
  const bandeja = (f, tok) => {
    const b = el("div", "am-bandeja");
    const bFijo = boton("⭐ Fijar", "mini am-b-fijo", () => { const l = porClave(K_PIN); ponerPorClave(K_PIN, l.includes(tok) ? l.filter((x) => x !== tok) : [...l, tok]); decorar(); });
    const bMudo = boton("🔇 Silenciar", "mini am-b-mudo", () => { const l = porClave(K_MUTE), era = l.includes(tok); ponerPorClave(K_MUTE, era ? l.filter((x) => x !== tok) : [...l, tok]); decorar(); tell(era ? "Vuelve a viajar con los mensajes" : "Sigue anclado pero ya no viaja"); });
    b.append(bFijo, bMudo);
    if (/^(enlace|raiz):https?:\/\//.test(tok)) b.append(boton("↗ Abrir", "mini", () => window.open(tok.replace(/^[a-z]+:/, ""), "_blank", "noopener")));
    b.append(boton("✎ Etiqueta", "mini", () => { const k = clave(), t = leer(K_ALIAS, {}), a = t[k] || {}, v = prompt("Etiqueta para este ancla (vacío = quitarla)", a[tok] || ""); if (v === null) return; if (v.trim()) a[tok] = v.trim().slice(0, 60); else delete a[tok]; t[k] = a; escribir(K_ALIAS, t); decorar(); }));
    b.append(boton("Copiar", "mini", async () => { try { await navigator.clipboard.writeText(tok.replace(/^[a-z]+:/, "")); tell("Copiado"); } catch (e) { tell("No se pudo copiar"); } }));
    const sel = el("select", "vn-in"); sel.setAttribute("aria-label", "Copiar a otro objetivo"); const o0 = el("option", "", "Copiar a…"); o0.value = ""; sel.append(o0);
    destinos().forEach(([v, n]) => { const o = el("option", "", n); o.value = v; sel.append(o); });
    sel.addEventListener("change", () => { if (!sel.value) return; const n = sel.options[sel.selectedIndex].textContent; tell(agregarA(sel.value, tok) ? "Copiado a " + n : "No se pudo copiar a " + n); sel.value = ""; decorar(); });
    b.append(sel); return b;
  };
  function aplicarFiltro() {
    [...resumen.querySelectorAll(".va-item")].forEach((f) => { const t = (f.dataset.tok || f.textContent).toLowerCase(); f.style.display = filtro && !t.includes(filtro) ? "none" : ""; });
    const lf = q("#anc-lista"); if (lf) [...lf.querySelectorAll(".va-item")].forEach((f) => { if (f.classList.contains("borrado-oculto")) return; const n = (f.querySelector(".fila-nom") || f).textContent.toLowerCase(); f.dataset.filtrado = filtro && !n.includes(filtro) ? "1" : ""; });
  }
  function contadores(toks) {
    caja.querySelectorAll(".anc-sec").forEach((s) => {
      s.dataset.base = s.dataset.base || s.textContent; const b = s.dataset.base;
      if (b === "Anclado ahora") s.textContent = b + " (" + toks.length + ")";
      else if (b === "Archivos") { const lf = q("#anc-lista"); s.textContent = b + (lf ? " (" + lf.querySelectorAll(".va-item").length + ")" : ""); }
    });
  }
  function medir() { const mu = porClave(K_MUTE), n = tokens().filter((t) => !mu.includes(t)).reduce((s, t) => s + t.length, 0); medidor.textContent = "≈ " + n + " caracteres anclados en el contexto" + (n > 8000 ? " · ⚠ mucho: silencia o quita lo que no uses" : ""); medidor.classList.toggle("am-alerta", n > 8000); }
  function reponerFijos() { const o = obj(); if (!o) return; let c = false; porClave(K_PIN).forEach((t) => { if (!o.anclados.has(t)) { o.anclados.add(t); c = true; } }); if (c) refrescar(); }
  function decorar() {
    const o = obj(); if (!o) return; const k = clave(), toks = tokens().filter((a) => RESUMEN.test(a)), mapa = new Map(toks.map((a) => [mostrar(a), a]));
    const pins = porClave(K_PIN), mutes = porClave(K_MUTE), alias = leer(K_ALIAS, {})[k] || {}, primera = claveVista !== k;
    if (primera) { claveVista = k; vistos = new Set(toks); }
    let nueva = null;
    [...resumen.querySelectorAll(".va-item")].forEach((f) => {
      const nom = f.querySelector(".fila-nom"); if (!nom) return;
      nom.dataset.base = nom.dataset.base || nom.textContent; const tok = mapa.get(nom.dataset.base); if (!tok) return;
      f.dataset.tok = tok; f.classList.add("am-fila"); nom.textContent = alias[tok] ? "🏷 " + alias[tok] : nom.dataset.base;
      const fijo = pins.includes(tok), mudo = mutes.includes(tok);
      f.classList.toggle("am-fijo", fijo); f.classList.toggle("am-mudo", mudo); f.style.order = String(fijo ? -10 : ORD(tok));
      if (!vistos.has(tok)) { f.classList.add("am-nuevo"); nueva = f; vistos.add(tok); }
      if (!f.querySelector(".am-bandeja")) { f.append(bandeja(f, tok)); nom.addEventListener("click", () => f.classList.toggle("am-abierto")); }
      f.querySelector(".am-b-fijo").classList.toggle("on", fijo); f.querySelector(".am-b-mudo").classList.toggle("on", mudo);
      const tb = tambienEn(tok); let sm = f.querySelector(".am-tb"); if (tb.length) { if (!sm) { sm = el("small", "am-tb"); f.append(sm); } sm.textContent = "También en: " + tb.join(", "); } else if (sm) sm.remove();
    });
    if (nueva && !primera) nueva.scrollIntoView({ block: "nearest", behavior: "smooth" });
    contadores(toks); medir(); aplicarFiltro(); reponerFijos();
  }
  let p = 0; const diferido = () => { if (!p) p = requestAnimationFrame(() => { p = 0; decorar(); }); };
  new MutationObserver(diferido).observe(resumen, { childList: true });
  const lf = q("#anc-lista"); if (lf) new MutationObserver(diferido).observe(lf, { childList: true });
  window.addEventListener("riu:objetivo", () => { pila = []; botDes.disabled = true; aviso.hidden = true; claveVista = null; diferido(); });
  pintarRec(); decorar();
}
