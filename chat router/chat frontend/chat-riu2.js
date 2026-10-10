// chat-riu2.js — resto de componentes RUI del skill (12, 13, 14, 15, 17, 18, 19, 21, 04, 05, 02) llevados a JS simple
// + mejoras de flujo (ventanas accesibles, borrador, campo que crece, aviso sin conexion). Archivo propio, solo frontend, datos reales:
// nada se inventa; lo que muestra sale del chat, del historial local y de los avisos reales.
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
      chips.forEach((c) => { c.setAttribute("role", "tab"); c.setAttribute("aria-selected", String(c.classList.contains("on"))); });
      const i = chips.findIndex((c) => c.classList.contains("on"));
      if (chips.length < 2 || i < 0) return;
      const b = crear("button", "chip-borrar"); b.type = "button"; b.title = "Cerrar este chat"; b.setAttribute("aria-label", "Cerrar este chat");
      b.innerHTML = SVG('<path class="tapa" d="M4 7h16M9 7V4h6v3"/><path d="M6 7l1 13h10l1-13M10 11v6M14 11v6"/>', 16);
      chips[i].after(b);
      b.addEventListener("click", () => {
        const c = crear("span", "chip-confirmar");
        const si = crear("button", "mini rojo", "Cerrar"), no = crear("button", "mini", "Mantener");
        si.type = no.type = "button";
        si.addEventListener("click", () => { clearTimeout(t); root.dispatchEvent(new CustomEvent("riu:cerrar-chat", { detail: i })); });
        no.addEventListener("click", () => { clearTimeout(t); poner(); });
        obs.disconnect(); c.append(si, no); b.replaceWith(c); obs.observe(tabs, { childList: true });
        clearTimeout(t); t = setTimeout(() => { if (c.isConnected) poner(); }, 4000);
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

export function conectarRiu2(ctx) {
  [campana, navegacion, sinConexion].forEach((f) => seguro(f));
  [cerrarChats, contadorAncla, reacciones, reproductor, colaMotor, actividad, ventanasA11y, entrada].forEach((f) => seguro(f, ctx));
}
