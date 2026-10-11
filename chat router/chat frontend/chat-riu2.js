// chat-riu2.js — resto de componentes RUI del skill (12, 13, 14, 15, 17, 18, 19, 21, 04, 05, 02) llevados a JS simple
// + mejoras de flujo (ventanas accesibles, borrador, campo que crece, aviso sin conexion). Archivo propio, solo frontend, datos reales:
// nada se inventa; lo que muestra sale del chat, del historial local y de los avisos reales.
import { cargar } from "./apariencia-aplicar.js";
const $ = (s, r = document) => r.querySelector(s);
const crear = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const leer = (k, def) => { try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? def : v; } catch (e) { return def; } };
const escribir = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
const SVG = (p, w = 18) => '<svg viewBox="0 0 24 24" width="' + w + '" height="' + w + '" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
const seguro = (f, ...a) => { try { f(...a); } catch (e) { console.warn("riu2:", f.name, e); } };

// ---------- GLOBAL (una sola vez): campana de avisos (RUI 14), nav con indicador/rebote/proximidad (RUI 17, 02, 05), sin conexion ----------
function campana() {
  const acceso = $(".access"), aviso = $("#notice");
  if (window.__riuCampana || !acceso || !aviso) return;
  window.__riuCampana = true;
  const lista = leer("riu_avisos_v1", []);
  const b = crear("button", "riu-campana"); b.type = "button"; b.title = "Avisos"; b.setAttribute("aria-label", "Avisos"); b.setAttribute("aria-expanded", "false");
  b.innerHTML = SVG('<path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>', 20);
  const ins = crear("span", "riu-insignia"); ins.hidden = true; b.append(ins);
  acceso.prepend(b);
  const panel = crear("div", "riu-avisos"); panel.hidden = true; panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Avisos");
  document.body.append(panel);
  let nuevos = 0;
  const hora = (t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const pintar = () => {
    panel.replaceChildren();
    const cab = crear("div", "riu-avisos-cab"); cab.append(crear("strong", "", "Avisos"));
    const v = crear("button", "mini", "Vaciar"); v.type = "button";
    v.addEventListener("click", () => { lista.length = 0; escribir("riu_avisos_v1", lista); pintar(); });
    cab.append(v); panel.append(cab);
    if (!lista.length) panel.append(crear("div", "fila-desc", "Sin avisos todavía"));
    [...lista].reverse().forEach((a) => { const f = crear("div", "riu-aviso"); f.append(crear("small", "", hora(a.t)), crear("span", "", a.m)); panel.append(f); });
  };
  const insignia = () => { ins.hidden = nuevos < 1; ins.textContent = nuevos > 9 ? "9+" : String(nuevos); };
  let ult = "", ultT = 0;
  new MutationObserver(() => {
    const m = (aviso.textContent || "").trim(); if (!m) return;
    const t = Date.now(); if (m === ult && t - ultT < 1500) return; ult = m; ultT = t;
    const err = /error|no se pudo|fall|sin conexi|denegad|negado|HTTP [45]|BRIDGE|caído/i.test(m); aviso.classList.toggle("err", err);
    setTimeout(() => { if ((aviso.textContent || "").trim() === m) aviso.textContent = ""; }, Math.round((Number(cargar().avisoSeg) || 4.5) * 1000 * (err ? 2 : 1)));  // toast: se limpia solo; el historial queda en la campana
    lista.push({ t, m: m.slice(0, 220) }); if (lista.length > 30) lista.shift(); escribir("riu_avisos_v1", lista);
    if (panel.hidden) { nuevos++; insignia(); b.classList.remove("suena"); void b.offsetWidth; b.classList.add("suena"); } else pintar();
  }).observe(aviso, { childList: true, characterData: true, subtree: true });
  const abrir = (s) => { panel.hidden = !s; b.setAttribute("aria-expanded", String(s)); if (s) { nuevos = 0; insignia(); pintar(); } };
  b.addEventListener("click", (e) => { e.stopPropagation(); abrir(panel.hidden); });
  document.addEventListener("click", (e) => { if (!panel.hidden && !panel.contains(e.target)) abrir(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") abrir(false); });
}
function navegacion() {
  const nav = $("#navigation");
  if (!nav || nav.dataset.riu) return;
  nav.dataset.riu = "1"; nav.classList.add("con-ind");
  const ind = crear("span", "nav-ind"); ind.setAttribute("aria-hidden", "true"); nav.append(ind);
  const mover = () => {
    const a = nav.querySelector("[aria-current=page]"); if (!a) return;
    ind.style.cssText = matchMedia("(max-width:720px)").matches
      ? "left:" + a.offsetLeft + "px;top:" + (a.offsetTop + a.offsetHeight - 3) + "px;width:" + a.offsetWidth + "px;height:3px"
      : "left:0;top:" + a.offsetTop + "px;width:3px;height:" + a.offsetHeight + "px";
  };
  new MutationObserver(mover).observe(nav, { attributes: true, attributeFilter: ["aria-current"], subtree: true });
  addEventListener("resize", mover); mover();
  nav.addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; b.classList.remove("rebote"); void b.offsetWidth; b.classList.add("rebote"); });
  if (matchMedia("(hover:hover) and (pointer:fine) and (min-width:721px)").matches) {
    const bs = () => [...nav.querySelectorAll("button")];
    nav.addEventListener("pointermove", (e) => bs().forEach((b) => { const r = b.getBoundingClientRect(); const k = Math.max(0, 1 - Math.abs(e.clientY - (r.top + r.height / 2)) / 90); b.style.transform = "translateX(" + (k * 8).toFixed(1) + "px)"; }));
    nav.addEventListener("pointerleave", () => bs().forEach((b) => { b.style.transform = ""; }));
  }
}
function sinConexion() {
  if (window.__riuRed) return; window.__riuRed = true;
  const nota = (m) => { const n = $("#notice"); if (n) n.textContent = m; };
  addEventListener("offline", () => nota("Sin conexión: tus mensajes no se enviarán hasta que vuelva internet"));
  addEventListener("online", () => nota("Conexión recuperada"));
}

// ---------- POR PANEL ----------
// RUI 18 delete-button: cerrar un chat con confirmacion (basura que abre la tapa -> Cerrar / Mantener). Tambien aria de pestañas.
function cerrarChats({ root, q }) {
  const tabs = q("#chat-tabs"); if (!tabs) return;
  tabs.setAttribute("role", "tablist");
  let t = 0;
  const poner = () => {
    obs.disconnect();
    try {
      tabs.querySelectorAll(".chip-borrar,.chip-confirmar").forEach((x) => x.remove());
      const chips = [...tabs.querySelectorAll(".chip")].filter((c) => c.textContent.trim() !== "＋");
      chips.forEach((c, i) => {
        c.setAttribute("role", "tab"); c.setAttribute("aria-selected", String(c.classList.contains("on")));
        const b = crear("button", "chip-borrar"); b.type = "button"; b.title = "Borrar este chat"; b.setAttribute("aria-label", "Borrar " + c.textContent.replace("…", "").trim());
        b.innerHTML = SVG('<path d="M6 6l12 12M18 6L6 18"/>', 14);
        c.after(b);
        b.addEventListener("click", () => {
          const cf = crear("span", "chip-confirmar");
          const si = crear("button", "mini rojo", chips.length > 1 ? "Borrar" : "Vaciar"), no = crear("button", "mini", "Mantener");
          si.type = no.type = "button";
          si.addEventListener("click", () => { clearTimeout(t); root.dispatchEvent(new CustomEvent("riu:cerrar-chat", { detail: i })); });
          no.addEventListener("click", () => { clearTimeout(t); poner(); });
          obs.disconnect(); cf.append(si, no); b.replaceWith(cf); obs.observe(tabs, { childList: true });
          clearTimeout(t); t = setTimeout(() => { if (cf.isConnected) poner(); }, 4000);
        });
      });
    } finally { obs.observe(tabs, { childList: true }); }
  };
  let p = 0;
  const obs = new MutationObserver(() => { if (!p) p = requestAnimationFrame(() => { p = 0; poner(); }); });
  poner();
}
// RUI 19 animated-counter: cuantos anclados llevas, en el boton del ancla
function contadorAncla({ q }) {
  const b = q("#btn-ancla"); if (!b || b.querySelector(".riu-contador")) return;
  const n = crear("span", "riu-contador"); n.hidden = true; b.append(n); b.classList.add("con-contador");
  const act = () => {
    const v = Number(b.dataset.n || 0);
    if (!n.hidden && n.textContent === String(v)) return;
    n.hidden = v < 1; n.textContent = String(v); n.classList.remove("sube"); void n.offsetWidth; n.classList.add("sube");
  };
  new MutationObserver(act).observe(b, { attributes: true, attributeFilter: ["data-n"] }); act();
}
// RUI 13 emoji-reaction: reacciones a cada respuesta (se guardan en este navegador)
function reacciones({ q }) {
  const hist = q("#histories"); if (!hist) return;
  const R = leer("riu_reac_v1", {});
  const clave = (t) => { const s = t.replace(/[\s`]/g, "").slice(0, 80); let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h + ":" + s.length; };
  const EMO = [["👍", "Me sirvió"], ["👎", "No me sirvió"], ["✅", "Resuelto"]];
  const poner = (m) => {
    if (m.querySelector(".riu-reac")) return;
    const sp = m.querySelector(".txt"); if (!sp || sp.textContent.trim().length < 20) return;
    const k = clave(sp.textContent);
    const fila = crear("div", "riu-reac"); fila.setAttribute("role", "group"); fila.setAttribute("aria-label", "Reacciones");
    EMO.forEach(([e, t]) => {
      const b = crear("button", "riu-r" + (R[k] === e ? " on" : ""), e); b.type = "button"; b.title = t; b.setAttribute("aria-label", t); b.setAttribute("aria-pressed", String(R[k] === e));
      b.addEventListener("click", () => {
        const ya = R[k] === e; if (ya) delete R[k]; else R[k] = e;
        const ks = Object.keys(R); if (ks.length > 300) delete R[ks[0]];
        escribir("riu_reac_v1", R);
        fila.querySelectorAll(".riu-r").forEach((x) => { const on = !ya && x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", String(on)); });
        b.classList.remove("pop"); void b.offsetWidth; b.classList.add("pop");
      });
      fila.append(b);
    });
    m.append(fila);
  };
  let p = 0;
  const revisar = () => { p = 0; hist.querySelectorAll(".message:not(.user):not(.meta):not(.pending):not(.error)").forEach(poner); };
  new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  revisar();
}
// RUI 15 step-player: recorrer paso a paso el diagrama de cada selector
function reproductor({ root }) {
  const poner = (d) => {
    let b = d.nextElementSibling && d.nextElementSibling.classList.contains("dg-play") ? d.nextElementSibling : null;
    if (!b) {
      b = crear("button", "mini dg-play", "▶ Recorrer"); b.type = "button";
      let t = null;
      const parar = () => { clearInterval(t); t = null; b.textContent = "▶ Recorrer"; d.querySelectorAll(".dg-activo").forEach((x) => x.classList.remove("dg-activo")); };
      b.addEventListener("click", () => {
        if (t) { parar(); return; }
        const pasos = [...d.querySelectorAll(".dg-paso")]; let i = 0; b.textContent = "■ Parar";
        const paso = () => {
          d.querySelectorAll(".dg-activo").forEach((x) => x.classList.remove("dg-activo"));
          if (i >= pasos.length) { parar(); return; }
          pasos[i].classList.add("dg-activo"); pasos[i].scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" }); i++;
        };
        paso(); t = setInterval(paso, 900);
      });
      d.after(b);
    }
    b.hidden = d.hidden || !d.querySelector(".dg-paso");
  };
  root.querySelectorAll(".consil-diagrama").forEach((d) => { poner(d); new MutationObserver(() => poner(d)).observe(d, { childList: true, attributes: true, attributeFilter: ["hidden"] }); });
}
// RUI 21 task-list: la cola del motor como lista de tareas con tilde (URLs reales de la cola)
function colaMotor({ q }) {
  const cola = q("#motor-cola"), urls = q("#motor-urls"), sh = q("#sh-motor"); if (!cola || !urls) return;
  const lista = crear("ul", "riu-tareas"); lista.setAttribute("aria-label", "Cola de descargas"); cola.after(lista);
  const pintar = () => {
    const us = urls.value.match(/https?:\/\/[^\s"'<>)]+/g) || [];
    const txt = cola.textContent || "", m = /(\d+)\/(\d+)/.exec(txt), fin = /terminada/.test(txt);
    const hechas = !m ? 0 : fin ? Number(m[1]) : Math.max(0, Number(m[1]) - 1);
    lista.replaceChildren();
    us.slice(0, 50).forEach((u, i) => {
      const li = crear("li", i < hechas ? "hecha" : (m && !fin && i === hechas ? "en-curso" : ""));
      li.append(crear("span", "riu-tilde", i < hechas ? "✓" : ""), crear("span", "riu-tarea-t", u.replace(/^https?:\/\//, "").slice(0, 64)));
      lista.append(li);
    });
  };
  urls.addEventListener("input", pintar); urls.addEventListener("change", pintar);
  new MutationObserver(pintar).observe(cola, { childList: true, characterData: true, subtree: true });
  if (sh) new MutationObserver(() => { if (!sh.hidden) pintar(); }).observe(sh, { attributes: true, attributeFilter: ["hidden"] });
  pintar();
}
// RUI 12 github-activity: tus mensajes de los ultimos 28 dias (del historial local), en "Mas opciones"
function actividad({ q }) {
  const sh = q("#sh-mas"), caja = sh && sh.querySelector(".va-caja"); if (!caja || caja.querySelector(".riu-actividad")) return;
  const t = crear("div", "mod-grupo-t", "Actividad (28 días)"), g = crear("div", "riu-actividad"); g.setAttribute("role", "img"); caja.append(t, g);
  const pintar = () => {
    const h = leer("riu_hist_v1", {}), dias = {};
    Object.values(h).forEach((l) => (Array.isArray(l) ? l : []).forEach((m) => { if (m && m.rol === "user" && m.ts) { const k = new Date(m.ts).toDateString(); dias[k] = (dias[k] || 0) + 1; } }));
    g.replaceChildren(); let tot = 0;
    for (let i = 27; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i); const n = dias[d.toDateString()] || 0; tot += n;
      const c = crear("i", "riu-dia n" + (n ? Math.min(4, Math.ceil(n / 3)) : 0)); c.title = d.toLocaleDateString() + ": " + n + " mensaje(s)"; g.append(c);
    }
    g.setAttribute("aria-label", tot + " mensajes tuyos en 28 días");
  };
  new MutationObserver(() => { if (!sh.hidden) pintar(); }).observe(sh, { attributes: true, attributeFilter: ["hidden"] });
}
// RUI 01 folder: carpeta que se abre cuando "Archivos en memoria" está vacía
function carpetaVacia({ q }) {
  const lista = q("#va-lista"); if (!lista || lista.dataset.carpeta) return; lista.dataset.carpeta = "1";
  const c = crear("div", "riu-carpeta"); c.hidden = true;
  c.innerHTML = '<svg viewBox="0 0 64 56" width="64" height="56" aria-hidden="true"><path class="fondo" d="M4 12a4 4 0 0 1 4-4h14l6 6h28a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path class="tapa" d="M4 24h56v24a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/></svg><span>Aún no hay archivos en memoria</span>';
  lista.after(c);
  const act = () => { const n = lista.children.length; c.hidden = !(n === 0 || (n === 1 && /sin |vac[ií]o|no hay|ning/i.test(lista.textContent))); };
  new MutationObserver(act).observe(lista, { childList: true }); act();
}
// bienvenida (spec §5) con RUI 11 gravity-letters: el chat vacío saluda y ofrece accesos rápidos reales
function bienvenida({ q }) {
  const hist = q("#histories"); if (!hist || hist.querySelector(".riu-bienvenida")) return;
  const w = crear("div", "riu-bienvenida"), t = crear("div", "riu-bv-titulo"); t.setAttribute("aria-label", "¿Qué hacemos hoy?");
  let n = 0;
  "¿Qué hacemos hoy?".split(" ").forEach((pal, k, arr) => {
    const wd = crear("span", "riu-pal"); wd.setAttribute("aria-hidden", "true");
    [...pal].forEach((ch) => { const s = crear("span", "", ch); s.style.setProperty("--i", n++); wd.append(s); });
    t.append(wd); if (k < arr.length - 1) t.append(document.createTextNode(" "));
  });
  const fila = crear("div", "riu-bv-acc");
  [["Mis archivos", "#btn-archivos"], ["Anclar", "#btn-ancla"], ["Sandbox", "#btn-sandbox"]].forEach(([n, sel]) => { const b = crear("button", "mini", n); b.type = "button"; b.addEventListener("click", () => { const x = q(sel); if (x) x.click(); }); fila.append(b); });
  w.append(t, crear("p", "riu-bv-sub", "Escribe una orden o /ayuda"), fila); hist.append(w);
  const act = () => { const h = [...hist.querySelectorAll(".chat-history")].find((x) => !x.hidden); w.hidden = !!(h && h.querySelector(".message")); hist.classList.toggle("con-bienvenida", !w.hidden); };
  new MutationObserver(act).observe(hist, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden"] }); act();
}
// buscador (skill): filtra las listas largas de archivos de las ventanas
function buscadores({ q }) {
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
function ventanasA11y({ root }) {
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
function entrada({ q }) {
  const m = q("#message"), f = q("#composer"); if (!m || !f) return;
  const K = "riu_borrador_v1";
  try { if (!m.value) m.value = sessionStorage.getItem(K) || ""; } catch (e) {}
  const alto = () => { m.style.height = "auto"; m.style.height = Math.min(m.scrollHeight, 160) + "px"; };
  m.addEventListener("input", () => { alto(); try { sessionStorage.setItem(K, m.value); } catch (e) {} });
  f.addEventListener("submit", () => setTimeout(() => { if (!m.value) { try { sessionStorage.removeItem(K); } catch (e) {} alto(); } }, 400));
  alto();
}

// RUI 20 matrix-orb: orbe del estado de la conexión (naranja girando = sin verificar, verde = conectado, rojo = fallo)
function orbeConexion() {
  const c = $("#connection"); if (!c || window.__riuOrbe) return; window.__riuOrbe = true;
  const o = crear("span", "riu-orbe"), w = crear("span", "riu-estado"); o.setAttribute("aria-hidden", "true"); c.before(w); w.append(o, c);
  const act = () => {
    const t = (c.textContent || "").toLowerCase();
    o.dataset.e = /error|ca[ií]do|fall|sin conexi|offline|desconect|bloquead|no disponible|timeout/.test(t) ? "mal" : (/conectad|disponible|\bok\b|listo|activo|en l[ií]nea|online|verificad/.test(t) && !/sin verificar/.test(t)) ? "bien" : "espera";
    c.title = c.textContent;
  };
  new MutationObserver(act).observe(c, { childList: true, characterData: true, subtree: true }); act();
}
// V07 "selector de archivos (táctil + soltar)": arrastrar archivos encima del chat los adjunta como el botón del clip
function soltarArchivos({ root, q, tell }) {
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
export function conectarRiu2(ctx) {
  [campana, navegacion, sinConexion, orbeConexion].forEach((f) => seguro(f));
  [cerrarChats, contadorAncla, reacciones, reproductor, colaMotor, actividad, buscadores, carpetaVacia, bienvenida, soltarArchivos, ventanasA11y, entrada].forEach((f) => seguro(f, ctx));
}
