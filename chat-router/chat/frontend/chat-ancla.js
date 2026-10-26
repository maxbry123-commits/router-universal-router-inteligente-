// Ventana ⚓ de friccion cero + instrucciones fijas + historial persistente.
// Solo frontend del chat. Sin tocar el Router. Todo se guarda en el navegador (localStorage) y sobrevive a recargas y a cambios de chat.
const CLAVE_HIST = "riu_hist_v1";

const leer = (k) => { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } };
const escribir = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
const el = (tag, texto, cls) => { const d = document.createElement(tag); if (texto) d.textContent = texto; if (cls) d.className = cls; return d; };

// ---- historial por sesion: la copia COMPLETA vive en IndexedDB y localStorage guarda solo una cache corta; nunca se borra nada por falta de cuota ----
const memo = {};
const idb = () => new Promise((ok, no) => { const r = indexedDB.open("riu_hist", 1); r.onupgradeneeded = () => r.result.createObjectStore("h"); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); });
const idbLeer = async (k) => { try { const d = await idb(); return await new Promise((ok) => { const q = d.transaction("h").objectStore("h").get(k); q.onsuccess = () => ok(Array.isArray(q.result) ? q.result : []); q.onerror = () => ok([]); }); } catch (e) { return []; } };
const idbEscribir = async (k, v) => { try { const d = await idb(); await new Promise((ok) => { const tx = d.transaction("h", "readwrite"); if (v === null) tx.objectStore("h").delete(k); else tx.objectStore("h").put(v, k); tx.oncomplete = ok; tx.onerror = ok; tx.onabort = ok; }); } catch (e) {} };
const cache = (sesion) => { const t = leer(CLAVE_HIST) || {}; return Array.isArray(t[sesion]) ? t[sesion] : []; };
export const cargarHistorial = (sesion) => memo[sesion] || cache(sesion);
const guardar = (sesion) => { idbEscribir(sesion, memo[sesion]); const t = leer(CLAVE_HIST) || {}; t[sesion] = memo[sesion].slice(-40); escribir(CLAVE_HIST, t); };
// ---- respaldo en el Router: cada mensaje COMPLETO (user/bot/err, sin recorte) va a /memoria (SQLite + sync al bucket); si falla, queda en cola y se reintenta ----
let API = null; const CLAVE_PEND = "riu_hist_pend_v1", SC_HIST = "chat-ui:hist:", SC_TABS = "chat-ui:pestanas";
const pend = () => leer(CLAVE_PEND) || [];
let vaciando = false;
const vaciar = async () => {
  if (!API || vaciando) return; vaciando = true;
  try { let l = pend(); while (l.length) { try { await API("/memoria/save", { method: "POST", body: l[0] }); } catch (e) { break; } l = pend(); l.shift(); escribir(CLAVE_PEND, l); } } finally { vaciando = false; }
};
const subir = (scope, key, data) => { const l = pend(); l.push({ scope, key, data }); escribir(CLAVE_PEND, l.slice(-500)); vaciar(); };  // cola con tope (sin red mucho tiempo no llena localStorage)
const subirMsg = (sesion, m) => subir((SC_HIST + sesion).slice(0, 80), "m-" + m.ts + "-" + m.rol, m);
export const conectarRespaldo = (api) => { API = api; vaciar(); try { addEventListener("online", vaciar); } catch (e) {} };
export const registrar = (sesion, rol, texto) => {
  if (!memo[sesion]) memo[sesion] = cache(sesion).slice();
  const m = { rol, texto: String(texto == null ? "" : texto), ts: Date.now() };
  memo[sesion].push(m);
  guardar(sesion); subirMsg(sesion, m);
};
export const reemplazar = (sesion, viejo, nuevo) => {  // editar una salida SUSTITUYE la anterior (sin duplicados)
  const l = memo[sesion] || (memo[sesion] = cache(sesion).slice());
  for (let i = l.length - 1; i >= 0; i--) if (l[i].rol !== "user" && l[i].texto === viejo) { l[i].texto = nuevo; guardar(sesion); subirMsg(sesion, l[i]); return true; }  // misma llave: el registro más nuevo manda
  return false;
};
export const olvidar = (sesion) => { marcarBorrado(sesion); delete memo[sesion]; idbEscribir(sesion, null); const t = leer(CLAVE_HIST) || {}; delete t[sesion]; escribir(CLAVE_HIST, t); };  // solo al eliminar ese chat
// vuelve a pintar el historial completo en el chat c (c.hist = contenedor). burbuja = la funcion de panel-chat.js
export const restaurar = async (c, burbuja) => {
  const completo = await idbLeer(c.sesion), corto = cache(c.sesion), ult0 = completo.length ? completo[completo.length - 1].ts : 0;
  const l = completo.concat(corto.filter((m) => m.ts > ult0)); memo[c.sesion] = l;
  if (!l.length) return;
  for (const m of l) c.hist.append(m.rol === "user" ? burbuja(m.texto, "user") : m.rol === "err" ? burbuja(m.texto, "error") : burbuja(m.texto));
  const ult = l[l.length - 1];
  if (ult.rol === "user" && !(window.RIU_PENDIENTE && window.RIU_PENDIENTE(c.sesion))) c.hist.append(burbuja("La respuesta se interrumpió al recargar la página. Reenvía tu mensaje si hace falta.", "meta"));
};

// ---- pestañas: la lista (sesion, nombre, orden) y los chats borrados se respaldan en /memoria; antes de escribir se mezcla con lo remoto, así un navegador vacío no pisa el respaldo ----
let REM = null, remP = null, ultTabs = "";
const ultimo = (r) => { const rs = (r && r.records) || []; return rs.length ? rs.reduce((a, b) => (b.id > a.id ? b : a)).data : null; };
const tabsRemotas = () => { if (!remP) remP = (async () => { try { REM = ultimo(await API("/memoria/load?scope=" + encodeURIComponent(SC_TABS) + "&key=lista")) || { chats: [], borrados: [] }; } catch (e) { remP = null; return null; } return REM; })(); return remP; };
export const respaldarPestanas = async (lista) => {  // lista: [{ sesion, ... }] en orden de pestañas
  if (!API) return; const r = await tabsRemotas(); if (!r) return;
  const borr = new Set([...(r.borrados || []), ...(leer("riu_borrados_v1") || [])]);
  const loc = lista.filter((c) => !borr.has(c.sesion)).map((c, i) => Object.assign({}, c, { nombre: "Chat " + (i + 1), orden: i }));
  const ya = new Set(loc.map((c) => c.sesion));
  const chats = loc.concat((r.chats || []).filter((c) => !ya.has(c.sesion) && !borr.has(c.sesion)));  // las que solo están en el respaldo se conservan (para ↺)
  const data = { chats, borrados: [...borr] }, j = JSON.stringify(data);
  if (j === ultTabs) return; ultTabs = j; REM = data; subir(SC_TABS, "lista", Object.assign({ ts: Date.now() }, data));
};
export const marcarBorrado = (sesion) => { const b = leer("riu_borrados_v1") || []; if (!b.includes(sesion)) { b.push(sesion); escribir("riu_borrados_v1", b); } if (REM) REM.borrados = [...new Set([...(REM.borrados || []), sesion])]; };
export const pestanasPerdidas = async (activas) => {  // del respaldo remoto + IndexedDB: chats no borrados que no están abiertos, en su orden
  remP = null; const r = (await tabsRemotas()) || { chats: [], borrados: [] }, borr = new Set([...(r.borrados || []), ...(leer("riu_borrados_v1") || [])]);
  const out = (r.chats || []).filter((c) => !activas.includes(c.sesion) && !borr.has(c.sesion));
  for (const k of await huerfanas(activas)) if (!borr.has(k) && !out.some((c) => c.sesion === k)) out.push({ sesion: k });
  return out;
};

// ---- recuperar: une la copia local (IndexedDB + cache) con la memoria del Router (/memoria SQLite, sincronizada al bucket) y repinta ----
const idbClaves = async () => { try { const d = await idb(); return await new Promise((ok) => { const q = d.transaction("h").objectStore("h").getAllKeys(); q.onsuccess = () => ok(q.result || []); q.onerror = () => ok([]); }); } catch (e) { return []; } };
export const huerfanas = async (activas) => { const out = []; for (const k of await idbClaves()) if (typeof k === "string" && !activas.includes(k) && (await idbLeer(k)).length) out.push(k); return out; };  // chats con historial cuya pestaña se perdió (borrar un chat lo quita de IndexedDB)
const limpiar = (t) => { let s = String(t || ""); const f = s.lastIndexOf("[FIN INSTRUCCIONES FIJAS]"); if (f >= 0) s = s.slice(f + 25).replace(/\n\n\[ANTES DE RESPONDER:[\s\S]*$/, ""); const p = s.lastIndexOf("\nPREGUNTA:\n"); if (p >= 0) s = s.slice(p + 11); return s.trim(); };  // el Router guarda la pregunta con envoltorios
const delRespaldo = async (api, sesion) => {
  try {
    const r = await api("/memoria/search?scope=" + encodeURIComponent((SC_HIST + sesion).slice(0, 80)) + "&query=&k=100000"), m = new Map();
    for (const f of (r && r.results && r.results.sqlite) || []) if (f.data && f.data.ts && (!m.has(f.key) || f.id > m.get(f.key).id)) m.set(f.key, f);  // por llave, el registro más nuevo (ediciones)
    return [...m.values()].map((f) => ({ rol: f.data.rol, texto: String(f.data.texto == null ? "" : f.data.texto), ts: f.data.ts }));
  } catch (e) { return null; }
};
const delRouter = async (api, sesion) => {
  const comp = await delRespaldo(api, sesion); if (comp && comp.length) return comp;
  try {
    const r = await api("/memoria/search?scope=" + encodeURIComponent("chat-ui:chat:" + sesion) + "&query=&k=500");
    const out = [];
    ((r && r.results && r.results.sqlite) || []).map((f) => ({ ts: Number(String(f.key || "").replace(/\D/g, "")) || 0, d: f.data || {} })).filter((x) => x.ts && x.d.pregunta !== undefined).sort((a, b) => a.ts - b.ts)
      .forEach((x) => { out.push({ rol: "user", texto: limpiar(x.d.pregunta), ts: x.ts - 1 }); if (x.d.respuesta) out.push({ rol: "bot", texto: String(x.d.respuesta), ts: x.ts }); });
    return out;
  } catch (e) { return null; }
};
export const recuperar = async (c, burbuja, api) => {
  const vistos = new Set(), l = [];
  for (const m of [...(await idbLeer(c.sesion)), ...cache(c.sesion), ...(memo[c.sesion] || [])]) { const k = m.ts + m.rol + m.texto; if (!vistos.has(k)) { vistos.add(k); l.push(m); } }
  const rem = api ? await delRouter(api, c.sesion) : null, ya = new Set(l.map((m) => m.rol + "\u0000" + String(m.texto).trim()));
  let nuevos = 0;
  for (const m of rem || []) if (m.texto && !ya.has(m.rol + "\u0000" + m.texto)) { l.push(m); nuevos++; }
  l.sort((a, b) => (a.ts || 0) - (b.ts || 0));
  memo[c.sesion] = l; if (l.length) guardar(c.sesion);
  c.hist.replaceChildren(...l.map((m) => m.rol === "user" ? burbuja(m.texto, "user") : m.rol === "err" ? burbuja(m.texto, "error") : burbuja(m.texto)));
  return { total: l.length, router: nuevos, routerOk: rem !== null };
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
    if (/^(enlace|raiz|handoff|constitucion):/.test(l)) toks.push(l);
    else if (/https?:\/\//i.test(l)) toks.push(...l.split(/\s+/).filter((t) => /^https?:\/\//i.test(t)));  // solo los enlaces de la linea, no las palabras de alrededor
    else if (l.includes("/")) toks.push(l);  // ruta sin http (raiz del repo)
    // texto suelto (sin enlace ni ruta) ya no se ancla: antes cada linea de un mensaje pegado salia como un enlace falso
  }
  for (let tok of toks) {
    tok = tok.replace(/[,;]+$/, "");
    if (!tok) continue;
    let clave;
    if (/^(enlace|raiz|handoff|constitucion):/.test(tok)) clave = tok;
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
    const otros = [...chat().anclados].filter((a) => /^(enlace|raiz|handoff|constitucion):/.test(a));
    if (!otros.length) { resumen.append(el("div", "Nada anclado todavía (enlaces / raíces / handoffs)", "fila-desc")); return; }
    const basura = otros.filter((a) => a.startsWith("enlace:") && !/https?:\/\/|\//.test(a.slice(7)));  // texto suelto anclado por error (no es enlace ni ruta)
    if (basura.length) {
      const b = el("button", "Limpiar texto suelto (" + basura.length + ")", "mini"); b.type = "button";
      b.addEventListener("click", () => { basura.forEach((a) => chat().anclados.delete(a)); pintarAnclados(); guardar(); pintarResumen(); });
      resumen.append(b);
    }
    for (const a of otros) {
      const f = el("div", "", "va-item");
      f.append(el("span", (a.startsWith("raiz:") ? "📁 " : a.startsWith("handoff:") ? "📌 " : a.startsWith("constitucion:") ? "📜 Constitución: " : "🔗 ") + a.replace(/^(enlace|raiz|handoff|constitucion):/, ""), "fila-nom"));
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

  // 4) proyectos de ESTE chat: grupos con nombre de lo anclado (archivos, enlaces, raices). Tocar = anclar o quitar todo el grupo
  const CLAVE_PROY = "riu_proy_v1";
  const proys = () => { const t = leer(CLAVE_PROY) || {}; return Array.isArray(t[chat().sesion]) ? t[chat().sesion] : []; };
  const salvarProys = (l) => { const t = leer(CLAVE_PROY) || {}; t[chat().sesion] = l; escribir(CLAVE_PROY, t); };
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

  const refrescar = () => {
    instr.value = chat().instrucciones || "";
    estadoInstr.textContent = instr.value.trim() ? "Encendidas: se envían con cada mensaje." : "Apagadas (escribe para encender).";
    pintarResumen();
    pintarProyectos();
  };
  instr.addEventListener("input", () => { estadoInstr.textContent = instr.value.trim() ? "Encendidas: se envían con cada mensaje." : "Apagadas (escribe para encender)."; });
  refrescar();
  return { refrescar };
}
