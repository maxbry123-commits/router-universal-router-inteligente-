// Ventana ⚓ de friccion cero + instrucciones fijas + historial persistente.
// Solo frontend del chat. Sin tocar el Router. Todo se guarda en el navegador (localStorage) y sobrevive a recargas y a cambios de chat.
const CLAVE_HIST = "riu_hist_v1";
const MAX_MSG = 120;
const MAX_TXT = 8000;
// habla con la memoria del Router por el puente del chat; si falla devuelve null (el navegador sigue de respaldo)
const srv = (acc, p) => { try { return typeof window.RIU_ACCION === "function" ? window.RIU_ACCION(acc, p).catch(() => null) : Promise.resolve(null); } catch (e) { return Promise.resolve(null); } };

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
  if (!l.length) {  // sin copia local: se recupera de la memoria del Router
    srv("historial", { sesion: c.sesion }).then((r) => {
      const t = r && Array.isArray(r.turnos) ? r.turnos : [];
      if (!t.length || cargarHistorial(c.sesion).length) return;
      for (const x of t) { c.hist.append(burbuja(x.pregunta, "user")); registrar(c.sesion, "user", x.pregunta); c.hist.append(burbuja(x.respuesta)); registrar(c.sesion, "bot", x.respuesta); }
    });
    return;
  }
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
  const pintarResumen = () => { pintarResumen0(); pintarProyectos(); };
  const pintarResumen0 = () => {
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
  instr.addEventListener("input", () => { clearTimeout(t0); t0 = setTimeout(() => { chat().instrucciones = instr.value; guardar(); pintarAnclados(); srv("estado_chat", { op: "guardar", sesion: chat().sesion, instrucciones: instr.value }); }, 300); });
  const estadoInstr = el("div", "", "fila-desc");

  // 4) proyectos de ESTE chat: grupos con nombre de lo anclado (archivos, enlaces, raices). Tocar = anclar o quitar todo el grupo
  const CLAVE_PROY = "riu_proy_v1";
  const proys = () => { const t = leer(CLAVE_PROY) || {}; return Array.isArray(t[chat().sesion]) ? t[chat().sesion] : []; };
  const salvarLocal = (l) => { const t = leer(CLAVE_PROY) || {}; t[chat().sesion] = l; escribir(CLAVE_PROY, t); };
  const salvarProys = (l) => { salvarLocal(l); srv("proyectos", { op: "guardar", sesion: chat().sesion, lista: l }); };
  const nombreProy = el("input"); nombreProy.id = "anc-proy-nombre"; nombreProy.placeholder = "Nombre del proyecto (opcional)"; nombreProy.autocomplete = "off";
  const bCrear = el("button", "Crear con lo anclado", "mini"); bCrear.type = "button";
  const listaProy = el("div", "", "list"); listaProy.id = "anc-proyectos";
  const pintarProyectos = () => {
    listaProy.replaceChildren();
    const l = proys();
    if (!l.length) { listaProy.append(el("div", "Sin proyectos en este chat", "fila-desc")); return; }
    l.forEach((p, i) => {
      const f = el("div", "", "va-item");
      const todos = p.items.length > 0 && p.items.every((a) => chat().anclados.has(a));
      const t = el("button", p.nombre + " · " + p.items.length, "toggle" + (todos ? " on" : "")); t.type = "button";
      t.addEventListener("click", () => { const ya = p.items.length > 0 && p.items.every((a) => chat().anclados.has(a)); p.items.forEach((a) => (ya ? chat().anclados.delete(a) : chat().anclados.add(a))); pintarAnclados(); guardar(); pintarResumen(); });
      const u = el("button", "Actualizar", "mini"); u.type = "button"; u.title = "Guardar en este proyecto lo que está anclado ahora";
      u.addEventListener("click", () => { p.items = [...chat().anclados]; salvarProys(l); pintarProyectos(); tell("Proyecto actualizado: " + p.nombre); });
      const x = el("button", "✕", "mini"); x.type = "button";
      x.addEventListener("click", () => { l.splice(i, 1); salvarProys(l); pintarProyectos(); });
      f.append(t, u, x); listaProy.append(f);
    });
  };
  bCrear.addEventListener("click", () => {
    const items = [...chat().anclados];
    if (!items.length) { tell("Ancla primero archivos, enlaces o una raíz"); return; }
    const l = proys();
    l.push({ nombre: nombreProy.value.trim() || "Proyecto " + (l.length + 1), items });
    salvarProys(l); nombreProy.value = ""; pintarProyectos(); tell("Proyecto creado con " + items.length + " ítems");
  });
  const filaProy = el("div", "", "row"); filaProy.append(nombreProy, bCrear);

  const cab = caja.querySelector(".va-head");
  const ref = cab ? cab.nextSibling : caja.firstChild;
  const etiqueta = (t) => el("div", t, "fila-desc");
  [pegar, filaPegar, resumen, etiqueta("Instrucciones fijas del chat"), instr, estadoInstr, etiqueta("Proyectos de este chat"), filaProy, listaProy].forEach((n) => caja.insertBefore(n, ref));

  const desdeServidor = () => {
    const ses = chat().sesion;
    if (!(chat().instrucciones || "").trim()) srv("estado_chat", { op: "leer", sesion: ses }).then((r) => { if (r && r.instrucciones && chat().sesion === ses && !(chat().instrucciones || "").trim()) { chat().instrucciones = r.instrucciones; instr.value = r.instrucciones; guardar(); pintarAnclados(); } });
    if (!proys().length) srv("proyectos", { op: "listar", sesion: ses }).then((r) => { if (r && Array.isArray(r.proyectos) && r.proyectos.length && chat().sesion === ses && !proys().length) { salvarLocal(r.proyectos); pintarProyectos(); } });
  };
  const refrescar = () => {
    desdeServidor();
    instr.value = chat().instrucciones || "";
    estadoInstr.textContent = instr.value.trim() ? "Encendidas: se envían con cada mensaje." : "Apagadas (escribe para encender).";
    pintarResumen();
    pintarProyectos();
  };
  instr.addEventListener("input", () => { estadoInstr.textContent = instr.value.trim() ? "Encendidas: se envían con cada mensaje." : "Apagadas (escribe para encender)."; });
  refrescar();
  return { refrescar };
}
