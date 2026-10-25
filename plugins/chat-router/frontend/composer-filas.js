// composer-filas.js — debajo del texto, 3 selectores que abren su ventana (sin carrusel, nada tapado):
//  [Modelo: <el que responde>]  → todos los selectores de modelo (la sección «Selectores» se muda aquí: más espacio para la salida)
//  [Permisos ●●○]               → IA / Agentes / System prompt (los mismos chips, mismo estado del servidor)
//  [Herramientas]               → cada herramienta con su dibujo 2D y su nombre
// Mueve los MISMOS nodos (listeners intactos). Enviar (.action) sigue en la barra. Botón ⤢ del historial: salida grande.
const CHIPS = ["btn-tools", "btn-agentes", "btn-prompt"];
const NOMBRE = { "btn-adjunto": "Adjuntar", "btn-archivos": "Archivos", "btn-ancla": "Anclar", "btn-sandbox": "Sandbox", "btn-microfono": "Dictar", "btn-copiar-input": "Copiar", "btn-conexiones": "Conexiones", "btn-room": "ROOM", "btn-power": "Servidor", "btn-pendientes": "Pendientes" };
const QUEDAN = (e) => e.classList.contains("action") || e.classList.contains("cb-sel") || e.id === "anclados" || e.id === "btn-detener" || e.tagName === "INPUT";
const SVG = (d) => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + "</svg>";
const ICO = { modelo: '<rect x="5" y="5" width="14" height="14" rx="3"/><path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4"/>', permisos: '<path d="M12 2 20 5v6c0 5-3 8-8 11-5-3-8-6-8-11V5Z"/>', herr: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.4 2.4-2.6-.6-.6-2.6z"/>' };
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
function hoja(id, titulo) {  // ventana inferior con su lista (mismo estilo que las demás hojas del chat)
  const vieja = document.getElementById(id); if (vieja) vieja.remove();  // el chat se volvió a montar: la hoja anterior tenía nodos de la vista vieja
  const s = el("div", "sheet cb-hoja"); s.id = id; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-label", titulo);
  const caja = el("div", "va-caja"), cab = el("div", "row va-head"), x = el("button", "secondary sh-cerrar", "✕"), cuerpo = el("div", "cb-cuerpo");
  x.type = "button"; x.setAttribute("aria-label", "Cerrar " + titulo); cab.append(el("strong", "", titulo), x); caja.append(cab, cuerpo); s.append(caja); document.body.append(s);
  const cerrar = () => { s.hidden = true; };
  x.onclick = cerrar; s.addEventListener("click", (e) => { if (e.target === s) cerrar(); else if (e.target.closest("[data-sheet], .sel-pill, #sel-workflows, .cb-herr > button:not(#btn-microfono):not(#btn-copiar-input)")) setTimeout(cerrar, 0); });  // lo que abre otra ventana cierra esta
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(); });
  return { s, cuerpo };
}
function selector(clase, ico, titulo, h) {
  const b = el("button", "cb-sel secondary " + clase); b.id = clase; b.type = "button"; b.setAttribute("aria-haspopup", "dialog"); b.setAttribute("aria-controls", h.s.id);
  b.innerHTML = '<span class="cb-ico">' + SVG(ICO[ico]) + '<span class="cb-dots"></span></span><span class="cb-et"></span><svg class="cb-flecha" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  b.querySelector(".cb-et").textContent = titulo; b.onclick = () => { document.querySelectorAll(".cb-hoja").forEach((o) => { o.hidden = true; }); h.s.hidden = false; (h.s.querySelector("button:not(.sh-cerrar)") || h.s.querySelector("button")).focus(); };
  return b;
}
function montar(bar) {
  const hm = hoja("cb-modelos", "Modelo que responde"), hp = hoja("cb-permisos", "Permisos del modelo"), hh = hoja("cb-herramientas", "Herramientas");
  const tira = el("div", "cb-herr"); tira.setAttribute("role", "group"); tira.setAttribute("aria-label", "Herramientas del chat"); hh.cuerpo.append(tira);
  const perm = el("div", "cb-perm"); hp.cuerpo.append(perm, el("p", "muted cb-nota", "IA: consultar otros modelos (herramienta llm). Agentes: delegar en agentes. System prompt: añade el prompt completo del proyecto. El servidor recuerda cada uno."));
  const bm = selector("cb-sel-modelo", "modelo", "Modelo", hm), bp = selector("cb-sel-permisos", "permisos", "Permisos", hp), bh = selector("cb-sel-herr", "herr", "Herramientas", hh);
  bar.insertBefore(bh, bar.firstChild); bar.insertBefore(bp, bh); bar.insertBefore(bm, bp);
  const pintarModelo = () => { const g = document.querySelector(".sel-resp-global"); const full = g ? g.textContent : "", t = /^Responde:/.test(full) ? (full.split("·").pop() || full).trim() : (full.replace(/^Ningún selector encendido: responde /, "").replace(/ \(por defecto del Router\)/, "") || "Por defecto"); const et = bm.querySelector(".cb-et"); if (et.textContent === t) return; et.textContent = t; bm.title = full || "Modelo"; bm.setAttribute("aria-label", "Elegir modelo. Ahora: " + t); };
  const pintarPermisos = () => { const on = CHIPS.map((id) => { const c = document.getElementById(id); return !!c && c.getAttribute("aria-pressed") === "true"; }); const html = on.map((v) => '<i class="cb-punto' + (v ? " on" : "") + '"></i>').join(""), et = bp.querySelector(".cb-dots"); if (et.innerHTML === html) return; et.innerHTML = html; bp.setAttribute("aria-label", "Permisos: IA " + (on[0] ? "ON" : "OFF") + ", Agentes " + (on[1] ? "ON" : "OFF") + ", System prompt " + (on[2] ? "ON" : "OFF")); };
  const ordenar = () => {
    [...bar.children].forEach((e) => { if (CHIPS.includes(e.id)) perm.append(e); else if (!QUEDAN(e)) tira.append(e); });
    tira.querySelectorAll(":scope > button.secondary").forEach((b) => { if (!b.dataset.et) b.dataset.et = NOMBRE[b.id] || (b.getAttribute("aria-label") || b.title || "").split(/[·:(]/)[0].trim().slice(0, 14); });
    const sec = document.getElementById("selectores"); if (sec && sec.parentElement !== hm.cuerpo) hm.cuerpo.append(sec);
    pintarModelo(); pintarPermisos();
  };
  ordenar(); new MutationObserver(ordenar).observe(bar, { childList: true });
  const comp = bar.closest("#composer"); if (comp) comp.addEventListener("submit", () => comp.classList.add("cb-ocupado"));  // Detener aparece al enviar, sin esperar al siguiente sondeo
  setInterval(() => { let o = false; try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); o = !!(c && c.ocupado); } catch (e) {} if (comp && comp.classList.contains("cb-ocupado") !== o) comp.classList.toggle("cb-ocupado", o); }, 300);  // Detener solo mientras trabaja
  new MutationObserver(() => { pintarModelo(); pintarPermisos(); }).observe(document.body, { subtree: true, characterData: true, childList: true, attributes: true, attributeFilter: ["aria-pressed"] });
}
function ampliar(hist) {
  if (!hist || hist.querySelector(".riu-ampliar")) return;
  const b = el("button", "riu-ampliar"); b.type = "button"; b.setAttribute("aria-pressed", "false"); b.title = "Ampliar la salida"; b.setAttribute("aria-label", "Ampliar la salida");
  b.innerHTML = SVG('<path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/>');
  b.onclick = () => { const on = document.body.classList.toggle("salida-grande"); b.setAttribute("aria-pressed", String(on)); b.title = on ? "Volver al tamaño normal" : "Ampliar la salida"; b.setAttribute("aria-label", b.title); try { localStorage.setItem("riu_salida_grande", on ? "1" : ""); } catch (e) {} };
  hist.append(b); try { if (localStorage.getItem("riu_salida_grande")) b.click(); } catch (e) {}
}
const revisar = () => {
  const bar = document.querySelector("#composer .composer-bar");
  if (bar && !bar.dataset.filas) { bar.dataset.filas = "1"; montar(bar); }
  ampliar(document.querySelector("#histories"));
};
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
