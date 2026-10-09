// Ventana ⚓ de friccion cero + instrucciones fijas + historial persistente.
// Solo frontend del chat. Sin tocar el Router. Todo se guarda en el navegador (localStorage) y sobrevive a recargas y a cambios de chat.
const CLAVE_HIST = "riu_hist_v1";
const MAX_MSG = 120;
const MAX_TXT = 8000;

const leer = (k) => { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } };
const escribir = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
const el = (tag, texto, cls) => { const d = document.createElement(tag); if (texto) d.textContent = texto; if (cls) d.className = cls; return d; };

// ---- historial por sesion ----
export const cargarHistorial = (sesion) => { const t = leer(CLAVE_HIST) || {}; return Array.isArray(t[sesion]) ? t[sesion] : []; };
export const registrar = (sesion, rol, texto) => {
  const t = leer(CLAVE_HIST) || {};
  const l = Array.isArray(t[sesion]) ? t[sesion] : [];
  l.push({ rol, texto: String(texto == null ? "" : texto).slice(0, MAX_TXT), ts: Date.now() });
  t[sesion] = l.slice(-MAX_MSG);
  if (!escribir(CLAVE_HIST, t)) {  // sin espacio: recorta lo mas viejo de todos los chats y reintenta
    for (const k of Object.keys(t)) t[k] = t[k].slice(-Math.ceil(MAX_MSG / 4));
    escribir(CLAVE_HIST, t);
  }
};
// vuelve a pintar el historial guardado en el chat c (c.hist = contenedor). burbuja = la funcion de panel-chat.js
export const restaurar = (c, burbuja) => {
  const l = cargarHistorial(c.sesion);
  if (!l.length) return;
  for (const m of l) c.hist.append(m.rol === "user" ? burbuja(m.texto, "user") : m.rol === "err" ? burbuja(m.texto, "error") : burbuja(m.texto));
  const ult = l[l.length - 1];
  if (ult.rol === "user") c.hist.append(burbuja("La respuesta se interrumpió al recargar la página. Reenvía tu mensaje si hace falta.", "meta"));
};

// ---- instrucciones fijas: el modelo las revisa antes de leer la orden, despues de leerla y antes de escribir su salida ----
export const envolver = (mensaje, instr) => {
  const t = String(instr || "").trim();
  if (!t) return mensaje;
  return "[INSTRUCCIONES FIJAS. Revísalas ANTES de leer la orden, DESPUÉS de leerla y ANTES de escribir tu salida. Tu salida debe cumplirlas todas.]\n" + t + "\n[FIN INSTRUCCIONES FIJAS]\n\n" + mensaje + "\n\n[ANTES DE RESPONDER: comprueba que tu salida cumple las INSTRUCCIONES FIJAS de arriba.]";
};

// ---- anclar muchos enlaces o una raiz de una sola vez ----
export const clasificar = (texto) => {
  const vistos = new Set(), salida = [];
  const toks = [];
  for (const linea of String(texto || "").split(/\r?\n/)) {  // linea con prefijo o ruta con espacios = un solo item; con enlaces = uno por enlace
    const l = linea.trim();
    if (!l) continue;
    if (/^(enlace|raiz|handoff):/.test(l) || !/https?:\/\//i.test(l)) toks.push(l); else toks.push(...l.split(/\s+/));
  }
  for (let tok of toks) {
    tok = tok.replace(/[,;]+$/, "");
    if (!tok) continue;
    let clave;
    if (/^(enlace|raiz|handoff):/.test(tok)) clave = tok;
    else if (/^https?:\/\//i.test(tok)) {
      const sinQ = tok.split(/[?#]/)[0].replace(/\/+$/, "");
      const ruta = sinQ.replace(/^https?:\/\/[^/]+\/?/, "").split("/").filter(Boolean);
      const esGit = /^https?:\/\/(www\.)?github\.com\//i.test(tok);
      const raiz = /\/$/.test(tok.split(/[?#]/)[0]) || /\/tree\//.test(sinQ) || (esGit && ruta.length <= 2) || ruta.length === 0;
      clave = (raiz ? "raiz:" : "enlace:") + tok;
    } else clave = /\/$/.test(tok) ? "raiz:" + tok : "enlace:" + tok;
    if (!vistos.has(clave)) { vistos.add(clave); salida.push(clave); }
  }
  return salida;
};

export function montarAncla({ q, chat, tell, guardar, pintarAnclados }) {
  const caja = q("#ventana-ancla .va-caja");
  if (!caja) return { refrescar() {} };
  const desc = caja.querySelector(".fila-desc");
  if (desc) desc.textContent = "Subir desde aquí ancla al instante. Lo que subes con el clip no se ancla.";

  // 1) pegar enlaces / raiz: se anclan al pegar, sin tocar nada mas
  const pegar = el("textarea");
  pegar.id = "anc-pegar"; pegar.rows = 2; pegar.autocomplete = "off";
  pegar.placeholder = "Pega aquí enlaces (1, 10, 50…) o una raíz. Se anclan solos al pegar.";
  const anclarEnlaces = () => {
    const items = clasificar(pegar.value);
    if (!items.length) return false;
    const antes = chat().anclados.size;
    items.forEach((i) => chat().anclados.add(i));
    pegar.value = "";
    pintarAnclados(); guardar(); pintarResumen();
    tell((chat().anclados.size - antes) + " anclado(s) · total " + chat().anclados.size);
    return true;
  };
  pegar.addEventListener("paste", () => setTimeout(anclarEnlaces, 0));
  pegar.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); anclarEnlaces(); } });
  const bAnclar = el("button", "Anclar", "mini"); bAnclar.type = "button";
  bAnclar.addEventListener("click", () => { if (!anclarEnlaces()) tell("Pega primero un enlace o una raíz"); });
  const bHand = el("button", "Handoffs…", "mini"); bHand.type = "button";
  bHand.addEventListener("click", () => { const p = q("#ancla"); if (p) p.click(); });
  const filaPegar = el("div", "", "row"); filaPegar.append(bAnclar, bHand);

  // 2) lo que ya esta anclado (enlaces, raices, handoffs): con X para quitar uno o todo
  const resumen = el("div", "", "list"); resumen.id = "anc-resumen";
  resumen.style.maxHeight = "110px"; resumen.style.overflowY = "auto";
  const pintarResumen = () => {
    resumen.replaceChildren();
    const otros = [...chat().anclados].filter((a) => /^(enlace|raiz|handoff):/.test(a));
    if (!otros.length) { resumen.append(el("div", "Nada anclado todavía (enlaces / raíces / handoffs)", "fila-desc")); return; }
    for (const a of otros) {
      const f = el("div", "", "va-item");
      f.append(el("span", (a.startsWith("raiz:") ? "📁 " : a.startsWith("handoff:") ? "📌 " : "🔗 ") + a.replace(/^(enlace|raiz|handoff):/, ""), "fila-nom"));
      const x = el("button", "✕", "mini"); x.type = "button";
      x.addEventListener("click", () => { chat().anclados.delete(a); pintarAnclados(); guardar(); pintarResumen(); });
      f.append(x); resumen.append(f);
    }
    const t = el("button", "Quitar enlaces y raíces (" + otros.length + ")", "mini"); t.type = "button";
    t.addEventListener("click", () => { otros.forEach((a) => chat().anclados.delete(a)); pintarAnclados(); guardar(); pintarResumen(); });
    resumen.append(t);
  };

  // 3) instrucciones fijas: se guardan al escribir (sin boton). Vacio = apagado.
  const instr = el("textarea"); instr.id = "anc-instr"; instr.rows = 3; instr.autocomplete = "off";
  instr.placeholder = "Instrucciones fijas: el modelo las revisa antes y después de cada input y antes de responder. Se guardan solas.";
  let t0;
  instr.addEventListener("input", () => { clearTimeout(t0); t0 = setTimeout(() => { chat().instrucciones = instr.value; guardar(); pintarAnclados(); }, 300); });
  const estadoInstr = el("div", "", "fila-desc");

  const cab = caja.querySelector(".va-head");
  const ref = cab ? cab.nextSibling : caja.firstChild;
  const etiqueta = (t) => el("div", t, "fila-desc");
  [pegar, filaPegar, resumen, etiqueta("Instrucciones fijas del chat"), instr, estadoInstr].forEach((n) => caja.insertBefore(n, ref));

  const refrescar = () => {
    instr.value = chat().instrucciones || "";
    estadoInstr.textContent = instr.value.trim() ? "Encendidas: se envían con cada mensaje." : "Apagadas (escribe para encender).";
    pintarResumen();
  };
  instr.addEventListener("input", () => { estadoInstr.textContent = instr.value.trim() ? "Encendidas: se envían con cada mensaje." : "Apagadas (escribe para encender)."; });
  refrescar();
  return { refrescar };
}
