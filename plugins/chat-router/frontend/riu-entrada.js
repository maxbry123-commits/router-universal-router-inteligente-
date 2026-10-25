// riu-entrada.js — bienvenida (RUI 11), buscadores, ventanas accesibles (RUI 04), campo de entrada y soltar archivos. Dividido de chat-riu2.js sin cambiar la lógica.
import { crear } from "./riu-util.js";
// bienvenida (spec §5) con RUI 11 gravity-letters: el chat vacío saluda y ofrece accesos rápidos reales
export function bienvenida({ q }) {
  const hist = q("#histories"); if (!hist || hist.querySelector(".riu-bienvenida")) return;
  const w = crear("div", "riu-bienvenida"), t = crear("div", "riu-bv-titulo"); t.setAttribute("role", "heading"); t.setAttribute("aria-level", "2"); t.setAttribute("aria-label", "¿Qué hacemos hoy?");
  let n = 0;
  "¿Qué hacemos hoy?".split(" ").forEach((pal, k, arr) => {
    const wd = crear("span", "riu-pal"); wd.setAttribute("aria-hidden", "true");
    [...pal].forEach((ch) => { const s = crear("span", "", ch); s.style.setProperty("--i", n++); wd.append(s); });
    t.append(wd); if (k < arr.length - 1) t.append(document.createTextNode(" "));
  });
  const fila = crear("div", "riu-bv-acc");
  [["Mis archivos", "#btn-archivos"], ["Anclar", "#btn-ancla"], ["Sandbox", "#btn-sandbox"]].forEach(([n, sel]) => { const b = crear("button", "mini", n); b.type = "button"; b.addEventListener("click", () => { const x = q(sel); if (x) x.click(); }); fila.append(b); });
  w.append(t, crear("p", "riu-bv-sub", "Escribe una orden o /ayuda"), fila); hist.append(w);
  const act = () => { const h = [...hist.querySelectorAll(".chat-history")].find((x) => !x.hidden); { const v = !!(h && h.querySelector(".message")); if (w.hidden !== v) w.hidden = v; } hist.classList.toggle("con-bienvenida", !w.hidden); };
  new MutationObserver(act).observe(hist, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden"] }); act();
}

// buscador (skill): filtra las listas largas de archivos de las ventanas
export function buscadores({ q }) {
  ["#va-lista", "#anc-lista"].forEach((sel) => {
    const lista = q(sel); if (!lista || lista.dataset.busca) return; lista.dataset.busca = "1";
    const i = crear("input", "riu-buscar"); i.type = "search"; i.placeholder = "Buscar archivo…"; i.setAttribute("aria-label", "Buscar archivo"); i.autocomplete = "off"; i.hidden = true;
    lista.before(i);
    const filtrar = () => { const t = i.value.trim().toLowerCase(); [...lista.children].forEach((r) => { r.style.display = t && !r.textContent.toLowerCase().includes(t) ? "none" : ""; }); };
    i.addEventListener("input", filtrar);
    new MutationObserver(() => { i.hidden = lista.children.length < 6; filtrar(); }).observe(lista, { childList: true });
  });
}

// RUI 04 family-drawer (hojas con rebote, en CSS) + accesibilidad: dialogo, foco al abrir y de vuelta al boton
export function ventanasA11y({ root }) {
  let origen = null;
  root.querySelectorAll("[data-sheet]").forEach((b) => b.addEventListener("click", () => { origen = b; }, true));
  root.querySelectorAll(".sheet").forEach((s) => {
    const t = s.querySelector(".va-head strong");
    s.setAttribute("role", "dialog"); s.setAttribute("aria-modal", "true"); if (t) s.setAttribute("aria-label", t.textContent);
    new MutationObserver(() => {
      if (!s.hidden) { const x = s.querySelector(".sh-cerrar"); if (x) setTimeout(() => x.focus({ preventScroll: true }), 30); }
      else if (origen && !root.querySelector(".sheet:not([hidden])")) origen.focus({ preventScroll: true });
    }).observe(s, { attributes: true, attributeFilter: ["hidden"] });
  });
}

// entrada: el borrador sobrevive a recargas, el campo crece con el texto
export function entrada({ q }) {
  const m = q("#message"), f = q("#composer"); if (!m || !f) return;
  const K = "riu_borrador_v1";
  try { if (!m.value) m.value = sessionStorage.getItem(K) || ""; } catch (e) {}
  const alto = () => { m.style.height = "auto"; m.style.height = Math.min(m.scrollHeight, 160) + "px"; };
  m.addEventListener("input", () => { alto(); try { sessionStorage.setItem(K, m.value); } catch (e) {} });
  f.addEventListener("submit", () => setTimeout(() => { if (!m.value) { try { sessionStorage.removeItem(K); } catch (e) {} alto(); } }, 400));
  alto();
}

// V07 "selector de archivos (táctil + soltar)": arrastrar archivos encima del chat los adjunta como el botón del clip
export function soltarArchivos({ root, q, tell }) {
  const inp = q("#adjunto"), btn = q("#btn-adjunto"); if (!inp || !btn || root.dataset.soltar) return; root.dataset.soltar = "1";
  const cap = crear("div", "riu-soltar", "Suelta aquí para adjuntar"); cap.hidden = true; root.append(cap);
  let n = 0;
  const hay = (e) => !!(e.dataTransfer && [...(e.dataTransfer.types || [])].includes("Files"));
  root.addEventListener("dragenter", (e) => { if (!hay(e)) return; e.preventDefault(); n++; cap.hidden = false; });
  root.addEventListener("dragover", (e) => { if (hay(e)) e.preventDefault(); });
  root.addEventListener("dragleave", (e) => { if (!hay(e)) return; n = Math.max(0, n - 1); if (!n) cap.hidden = true; });
  root.addEventListener("drop", (e) => {
    if (!hay(e)) return; e.preventDefault(); n = 0; cap.hidden = true;
    const dt = new DataTransfer(); [...e.dataTransfer.files].forEach((f) => dt.items.add(f)); if (!dt.files.length) return;
    btn.dataset.directo = "1"; inp.click = () => {}; try { btn.click(); } finally { delete inp.click; delete btn.dataset.directo; }  // fija "solo subir" como el clip, sin abrir el selector
    inp.files = dt.files; inp.dispatchEvent(new Event("change", { bubbles: true }));
    tell(dt.files.length + " archivo(s) soltado(s)");
  });
}
