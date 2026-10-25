// ventanas-comun.js — piezas comunes de las ventanas nuevas (workflows, constitución, claves). Cada ventana vive en su propio archivo.
export const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
export const boton = (txt, cls, fn) => { const b = el("button", cls || "mini", txt); b.type = "button"; if (fn) b.addEventListener("click", fn); return b; };
export function cargarCss(nombre) {
  const id = "css-" + nombre; if (document.getElementById(id)) return;
  const l = document.createElement("link"); l.id = id; l.rel = "stylesheet"; l.href = "/chat/ui/" + nombre + ".css"; document.head.append(l);
}
export function crearVentana(root, { id, titulo, css }) {
  cargarCss("ventanas-comun"); if (css) cargarCss(css);
  let s = root.querySelector("#" + id);
  if (s) return { sheet: s, caja: s.querySelector(".va-caja") };
  s = el("div", "sheet"); s.id = id; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-modal", "true"); s.setAttribute("aria-label", titulo);
  const caja = el("div", "va-caja va-ancho"), head = el("div", "row va-head"), x = boton("✕", "secondary sh-cerrar", () => { s.hidden = true; });
  x.setAttribute("aria-label", "Cerrar"); head.append(el("strong", "", titulo), x); caja.append(head); s.append(caja); root.append(s);
  s.addEventListener("click", (e) => { if (e.target === s) s.hidden = true; });
  return { sheet: s, caja };
}
export function abrirVentana(root, sheet) { root.querySelectorAll(".sheet").forEach((h) => { h.hidden = true; }); sheet.hidden = false; }
export function agregarPill(q, id, texto, onClick) {
  const ya = q("#" + id); if (ya) return ya;
  const b = el("button", "pill", texto); b.type = "button"; b.id = id; b.addEventListener("click", onClick);
  const fila = (q("#motor") && q("#motor").parentElement) || q(".row.fields"); if (fila) fila.append(b);
  return b;
}
export function etiqueta(t) {
  const m = /^([a-z]+):([\s\S]*)$/.exec(String(t)); if (!m) return String(t);
  const ic = { enlace: "🔗", raiz: "📁", texto: "📝", secreto: "🔑", handoff: "📌" }[m[1]] || "•";
  return ic + " " + m[2].slice(0, 300);
}
// bloque de anclas con la misma lógica que el anclaje del chat: pegar URL/texto, traer lo anclado en el chat o subir un archivo
export function seccionAnclas(caja, { titulo, leerTokens, escribirTokens, destino, tell }) {
  const sec = el("div", "vn-sec"), lista = el("div", "vn-lista"), ta = el("textarea", "vn-ta"), traer = el("div", "vn-traer");
  ta.rows = 2; ta.placeholder = "Pega URLs o texto para anclar aquí…"; ta.setAttribute("aria-label", "Anclar a " + titulo); traer.hidden = true;
  const pintar = () => {
    const ts = leerTokens(); lista.replaceChildren();
    if (!ts.length) lista.append(el("div", "fila-desc", "Nada anclado todavía."));
    ts.forEach((t) => { const f = el("div", "vn-item"); f.append(el("span", "", etiqueta(t)), boton("✕", "mini", () => { escribirTokens(leerTokens().filter((x) => x !== t)); pintar(); })); lista.append(f); });
  };
  const agregar = (nuevos) => { const ya = leerTokens(), mas = nuevos.filter((t) => !ya.includes(t)); if (mas.length) escribirTokens([...ya, ...mas]); pintar(); return mas.length; };
  const anclar = boton("Anclar aquí", "mini", () => {
    const toks = ta.value.split(/\n/).map((l) => l.trim()).filter(Boolean).map((l) => (/^https?:\/\//i.test(l) ? "enlace:" + l.split(/\s+/)[0] : "texto:" + l.slice(0, 2000)));
    const n = agregar(toks); ta.value = ""; tell(n ? n + " ancla(s) añadidas a " + titulo : "Nada nuevo que anclar");
  });
  const bTraer = boton("Traer del anclaje del chat", "mini", () => {
    traer.hidden = !traer.hidden; if (traer.hidden) return; traer.replaceChildren();
    const toks = (window.RIU_CHAT && window.RIU_CHAT.tokens()) || [];
    if (!toks.length) { traer.append(el("div", "fila-desc", "El chat no tiene nada anclado.")); return; }
    const marcas = [];
    toks.forEach((t) => { const l = el("label", "vn-check"), c = el("input"); c.type = "checkbox"; c.value = t; marcas.push(c); l.append(c, el("span", "", etiqueta(t))); traer.append(l); });
    traer.append(boton("Copiar los marcados", "mini", () => { const n = agregar(marcas.filter((c) => c.checked).map((c) => c.value)); traer.hidden = true; tell(n + " ancla(s) copiadas a " + titulo); }));
  });
  const bSubir = boton("Subir archivo", "mini", () => {
    const b = document.querySelector("#anc-subir"); if (!b) { tell("El botón de subir no está disponible"); return; }
    window.RIU_ANCLAS = window.RIU_ANCLAS || {}; window.RIU_ANCLAS.temporal = destino;
    setTimeout(() => { if (window.RIU_ANCLAS.temporal === destino) window.RIU_ANCLAS.temporal = null; }, 120000); b.click();
  });
  const acc = el("div", "vn-fila"); acc.append(anclar, bTraer, bSubir);
  sec.append(el("div", "vn-t", titulo), lista, ta, acc, traer); caja.append(sec); pintar();
  return { pintar };
}
