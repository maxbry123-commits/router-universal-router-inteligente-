// almacen-archivos.js — sistema de almacenamiento de archivos (panel Archivos) con 20 mejoras. Usa el MISMO almacén del chat (acciones archivos, subir, archivo_borrar, xray).
//  1 almacén real (adiós «Not Found») · 2 carpeta por chat · 3 subida múltiple · 4 arrastrar y soltar · 5 progreso y reintento · 6 límite 2 MB amable
//  7 duplicados · 8 buscador · 9 filtros por tipo · 10 orden · 11 iconos · 12 selección múltiple · 13 anclar a cualquier objetivo · 14 insignias «anclado en»
//  15 borrar · 16 papelera con restaurar · 17 X-Ray · 18 copiar nombre · 19 contador y medidor · 20 recarga al volver + atajos (Supr, Ctrl+A)
import { leer, escribir, KEYS } from "./almacen.js";
import { crearObjetivo, listaWF, listaProyectos } from "./objetivos-ancla.js";
import { el, boton } from "./ventanas-comun.js";
const KB = "riu_archivos_borrados_v1", KV = "riu_arch_vistos_v1", MAX = 2000000;
export const TIPOS = [["todos", "Todos"], ["texto", "Texto"], ["codigo", "Código"], ["imagen", "Imagen"], ["pdf", "PDF"], ["datos", "Datos"], ["otro", "Otros"]];
const ICONO = { texto: "📄", codigo: "🧩", imagen: "🖼️", pdf: "📕", datos: "📊", otro: "📦" };
export function tipoDe(n) {
  const e = (String(n).split(".").pop() || "").toLowerCase();
  if (["md", "txt", "rtf", "log"].includes(e)) return "texto"; if (["js", "ts", "py", "html", "css", "json", "yaml", "yml", "sh", "sql", "jsx", "tsx", "c", "cpp", "java", "go", "rs"].includes(e)) return "codigo";
  if (["png", "jpg", "jpeg", "gif", "webp", "svg", "bmp"].includes(e)) return "imagen"; if (e === "pdf") return "pdf"; if (["csv", "tsv", "xlsx", "xls", "xml"].includes(e)) return "datos"; return "otro";
}
const chatsGuardados = () => { try { const a = JSON.parse(localStorage.getItem("riu_chats_v1") || "[]"); return Array.isArray(a) ? a : []; } catch (e) { return []; } };
const guardarChats = (a) => { try { localStorage.setItem("riu_chats_v1", JSON.stringify(a)); } catch (e) {} };
const sesionesDisp = () => { const c = chatsGuardados(); return c.length ? c.map((x, i) => ({ sesion: x.sesion, nombre: "Chat " + (i + 1) })) : [{ sesion: "general", nombre: "General" }]; };
const sesionActiva = () => { const c = chatsGuardados(); if (!c.length) return "general"; const i = Number(localStorage.getItem("riu_chat_activo")) || 0; return (c[Math.min(Math.max(i, 0), c.length - 1)] || {}).sesion || "general"; };
function anclarChat(sesion, nombre, on) { const c = chatsGuardados(), x = c.find((y) => y.sesion === sesion); if (!x) return false; const s = new Set(x.anclados || []); if (on) s.add(nombre); else s.delete(nombre); x.anclados = [...s]; guardarChats(c); return true; }
function quitarDeTodo(nombre) {
  const c = chatsGuardados(); let cc = false; c.forEach((x) => { if ((x.anclados || []).includes(nombre)) { x.anclados = x.anclados.filter((t) => t !== nombre); cc = true; } }); if (cc) guardarChats(c);
  const con = Object.assign({ items: [] }, leer(KEYS.constitucion, {})); if ((con.items || []).includes(nombre)) { con.items = con.items.filter((x) => x !== nombre); escribir(KEYS.constitucion, con); }
  const wf = leer(KEYS.workflows, { lista: [] }); let cw = false; (wf.lista || []).forEach((w) => { if ((w.items || []).includes(nombre)) { w.items = w.items.filter((x) => x !== nombre); cw = true; } }); if (cw) escribir(KEYS.workflows, wf);
  [KEYS.agentes, KEYS.sandbox].forEach((k) => { const s = leer(k, null); if (s && (s.items || []).includes(nombre)) { s.items = s.items.filter((x) => x !== nombre); escribir(k, s); } });
  const pr = leer("riu_proy_v1", {}); let cp = false; Object.keys(pr).forEach((k) => (Array.isArray(pr[k]) ? pr[k] : []).forEach((p) => { if ((p.items || []).includes(nombre)) { p.items = p.items.filter((x) => x !== nombre); cp = true; } })); if (cp) escribir("riu_proy_v1", pr);
}
function ancladoEn(nombre, sesion) {
  const en = [], x = chatsGuardados().find((y) => y.sesion === sesion); if (x && (x.anclados || []).includes(nombre)) en.push("Chat");
  if ((leer(KEYS.constitucion, {}).items || []).includes(nombre)) en.push("Constitución");
  listaWF().forEach((w) => { if ((w.items || []).includes(nombre)) en.push("Workflow " + w.nombre); });
  [[KEYS.agentes, "Agentes"], [KEYS.sandbox, "Sandbox"]].forEach(([k, n]) => { if ((leer(k, {}).items || []).includes(nombre)) en.push(n); });
  listaProyectos().forEach((p) => { if ((p.items || []).includes(nombre)) en.push("Proyecto " + p.nombre); });
  return en;
}
const destinos = () => [["chat", "Chat"], ["constitucion", "Constitución"], ...listaWF().map((w) => ["workflows:" + w.id, "Workflow · " + w.nombre]), ["agentes", "Agentes remotos"], ...listaProyectos().map((p) => ["proyecto:" + p.nombre, "Proyecto · " + p.nombre]), ["sandbox", "Sandbox"]];
export function montarAlmacenArchivos(root, { tell }) {
  const tab = root.querySelector("#tab-archivos"); if (!tab || typeof window.RIU_ACCION !== "function" || tab.dataset.alm) return false; tab.dataset.alm = "1";
  [...tab.children].forEach((c) => { c.style.display = "none"; });  // lo viejo (ruta que daba «Not Found») queda oculto, no se borra
  const app = el("div", "ar-app"); tab.append(app);
  let sesion = sesionActiva(), archivos = [], busq = "", tipo = "todos", orden = "nombre", sel = new Set(), subidas = [], bytes = 0;
  const borrados = () => { const l = leer(KB, {})[sesion]; return Array.isArray(l) ? l : []; };
  const marcar = (n, on) => { const t = leer(KB, {}), l = Array.isArray(t[sesion]) ? t[sesion] : []; t[sesion] = on ? [...new Set([...l, n])] : l.filter((x) => x !== n); escribir(KB, t); };
  // ---- cabecera ----
  const selS = el("select", "vn-in"); selS.setAttribute("aria-label", "Carpeta de archivos del chat");
  sesionesDisp().forEach((s) => { const o = el("option", "", s.nombre + " · " + String(s.sesion).slice(-6)); o.value = s.sesion; selS.append(o); }); selS.value = sesion;
  selS.addEventListener("change", () => { sesion = selS.value; sel.clear(); cargar(); });
  const estado = el("div", "vn-estado"); estado.setAttribute("role", "status");
  const cab = el("div", "vn-fila"); cab.append(selS, boton("Actualizar", "mini", () => cargar())); app.append(cab, estado);
  // ---- zona de subida ----
  const zona = el("div", "ar-zona"), inp = el("input"); inp.type = "file"; inp.multiple = true; inp.hidden = true;
  zona.append(el("strong", "", "Arrastra archivos aquí"), el("span", "vn-estado", "o"), boton("Elegir archivos", "mini", () => inp.click()), inp, el("span", "vn-estado", "Máx. 2 MB por archivo"));
  inp.addEventListener("change", () => { subirVarios(inp.files || []); inp.value = ""; });
  const listaSub = el("div", "vn-lista"); app.append(zona, listaSub);
  ;["dragenter", "dragover"].forEach((ev) => app.addEventListener(ev, (e) => { if (e.dataTransfer && [...(e.dataTransfer.types || [])].includes("Files")) { e.preventDefault(); zona.classList.add("suelta"); } }));
  app.addEventListener("dragleave", (e) => { if (!app.contains(e.relatedTarget)) zona.classList.remove("suelta"); });
  app.addEventListener("drop", (e) => { if (!e.dataTransfer || !e.dataTransfer.files || !e.dataTransfer.files.length) return; e.preventDefault(); zona.classList.remove("suelta"); subirVarios(e.dataTransfer.files); });
  // ---- herramientas ----
  const buscar = el("input", "vn-in"); buscar.type = "search"; buscar.placeholder = "Buscar archivo…"; buscar.autocomplete = "off"; buscar.setAttribute("aria-label", "Buscar archivo");
  buscar.addEventListener("input", () => { busq = buscar.value.trim().toLowerCase(); pintar(); });
  const chips = el("div", "vn-fila"), ord = el("select", "vn-in"); ord.setAttribute("aria-label", "Ordenar");
  [["nombre", "Nombre A→Z"], ["nombre-", "Nombre Z→A"], ["tipo", "Tipo"], ["recientes", "Subidos hace poco"]].forEach(([v, n]) => { const o = el("option", "", n); o.value = v; ord.append(o); });
  ord.addEventListener("change", () => { orden = ord.value; pintar(); });
  const barraSel = el("div", "ar-sel"), lista = el("div", "vn-lista ar-lista"), papelera = el("details", "ar-papelera"), salida = el("pre", "ar-xray"); salida.hidden = true; const pie = el("div", "vn-estado");
  app.append(buscar, chips, ord, barraSel, lista, papelera, salida, pie);
  // ---- datos ----
  async function cargar() {
    estado.textContent = "Cargando…";
    try { const r = await window.RIU_ACCION("archivos", { sesion }); archivos = (r.archivos || []).map(String); estado.textContent = ""; }
    catch (e) { archivos = []; estado.textContent = "No se pudo leer el almacén: " + e.message + ". Reintenta con Actualizar."; }
    pintar();
  }
  const visibles = () => {
    const b = borrados(), rec = leer(KV, {})[sesion] || {}; let l = archivos.filter((n) => !b.includes(n));
    if (busq) l = l.filter((n) => n.toLowerCase().includes(busq)); if (tipo !== "todos") l = l.filter((n) => tipoDe(n) === tipo);
    return l.sort((a, c) => (orden === "nombre" ? a.localeCompare(c) : orden === "nombre-" ? c.localeCompare(a) : orden === "tipo" ? tipoDe(a).localeCompare(tipoDe(c)) || a.localeCompare(c) : (rec[c] || 0) - (rec[a] || 0)));
  };
  // ---- subir ----
  async function subirUno(s) {
    const f = s.f;
    try {
      if (f.size > MAX) throw new Error("pesa más de 2 MB");
      const buf = await f.arrayBuffer(); let bin = ""; const by = new Uint8Array(buf); for (let i = 0; i < by.length; i += 8192) bin += String.fromCharCode.apply(null, by.subarray(i, i + 8192));
      const r = await window.RIU_ACCION("subir", { nombre: f.name, tipo: f.type || "texto", datos_b64: btoa(bin), sesion });
      if (r && r.error) throw new Error(String(r.error)); s.estado = "ok"; s.nota = ""; bytes += f.size; marcar(f.name, false);
      const v = leer(KV, {}); v[sesion] = Object.assign(v[sesion] || {}, { [f.name]: Date.now() }); escribir(KV, v);
    } catch (e) { s.estado = "error"; s.nota = e.message; }
    pintarSub();
  }
  async function subirVarios(files) {
    files = [...files]; if (!files.length) return;
    const ya = new Set(archivos.filter((n) => !borrados().includes(n))), dup = files.filter((f) => ya.has(f.name));
    const reemplazar = dup.length ? confirm("Ya existen: " + dup.map((f) => f.name).join(", ") + ".\n¿Reemplazarlos? (Cancelar = omitirlos)") : true;
    for (const f of files) { if (ya.has(f.name) && !reemplazar) continue; const s = { nombre: f.name, estado: "subiendo", nota: "", f }; subidas.unshift(s); pintarSub(); await subirUno(s); }
    await cargar();
  }
  function pintarSub() {
    listaSub.replaceChildren(); subidas = subidas.slice(0, 12);
    subidas.forEach((s) => { const f = el("div", "vn-item"); f.append(el("span", "", (s.estado === "ok" ? "✓ " : s.estado === "error" ? "⚠ " : "… ") + s.nombre + (s.nota ? " · " + s.nota : "")), s.estado === "error" ? boton("Reintentar", "mini", async () => { s.estado = "subiendo"; s.nota = ""; pintarSub(); await subirUno(s); await cargar(); }) : el("span")); listaSub.append(f); });
  }
  // ---- borrar / restaurar ----
  async function borrar(nombres) {
    if (!nombres.length || !confirm("¿Borrar " + (nombres.length === 1 ? "«" + nombres[0] + "»" : nombres.length + " archivos") + "? Se quitan de la lista y de todo lo anclado. Puedes restaurarlos desde la papelera.")) return;
    for (const n of nombres) { quitarDeTodo(n); marcar(n, true); sel.delete(n); try { await window.RIU_ACCION("archivo_borrar", { nombre: n, sesion }); } catch (e) { /* el servidor aun no tiene la accion: queda borrado en este navegador */ } }
    tell(nombres.length + " archivo(s) en la papelera"); pintar();
  }
  async function restaurar(n) { marcar(n, false); try { await window.RIU_ACCION("archivo_borrar", { nombre: n, sesion, restaurar: true }); } catch (e) { /* idem */ } tell("Restaurado: " + n); await cargar(); }
  async function xray(n) {
    salida.hidden = false; salida.textContent = "Analizando " + n + "…";
    try { const r = await window.RIU_ACCION("xray", { nombre: n, sesion }); salida.textContent = "X-RAY " + (r.nombre || n) + "\n" + (r.estructura || "") + "\nURLs: " + (r.urls || []).join(", ") + "\nMAPA:\n" + (r.mapa_mental || "") + "\nFLUJO: " + (r.microflujo || "") + "\n" + (r.resumen_goals || ""); }
    catch (e) { salida.textContent = "No se pudo analizar: " + e.message; }
  }
  function anclarA(nombres, destino, on) {
    let n = 0;
    nombres.forEach((nom) => { if (destino === "chat") { if (anclarChat(sesion, nom, on)) n++; return; } const i = destino.indexOf(":"), o = crearObjetivo(i < 0 ? destino : destino.slice(0, i), i < 0 ? undefined : destino.slice(i + 1)); if (o) { if (on) o.anclados.add(nom); else o.anclados.delete(nom); n++; } });
    tell(n ? (on ? "Anclados " : "Quitados ") + n + " archivo(s)" : "No se pudo (abre el chat una vez para anclar al chat)"); pintar();
  }
  // ---- pintar ----
  function pintarChips() { chips.replaceChildren(); TIPOS.forEach(([v, n]) => { const b = boton(n, "mini" + (v === tipo ? " on" : ""), () => { tipo = v; pintar(); }); b.setAttribute("aria-pressed", String(v === tipo)); chips.append(b); }); }
  function pintar() {
    pintarChips(); const vis = visibles(); lista.replaceChildren();
    if (!vis.length) lista.append(el("div", "fila-desc", archivos.length ? "Ningún archivo coincide." : "Aún no hay archivos en esta carpeta. Arrastra o elige arriba."));
    vis.forEach((n) => {
      const f = el("div", "ar-fila" + (sel.has(n) ? " sel" : "")), c = el("input"); c.type = "checkbox"; c.checked = sel.has(n); c.setAttribute("aria-label", "Seleccionar " + n);
      c.addEventListener("change", () => { if (c.checked) sel.add(n); else sel.delete(n); pintar(); });
      const nom = el("div", "ar-nom"); nom.append(el("span", "ar-ic", ICONO[tipoDe(n)]), el("strong", "", n)); const en = ancladoEn(n, sesion); if (en.length) nom.append(el("small", "ar-en", "Anclado en: " + en.join(", ")));
      const acc = el("div", "ar-acc"); acc.append(boton("X-Ray", "mini", () => xray(n)), boton("Copiar", "mini", async () => { try { await navigator.clipboard.writeText(n); tell("Nombre copiado"); } catch (e) { tell("No se pudo copiar"); } }), boton("✕", "mini", () => borrar([n])));
      f.append(c, nom, acc); lista.append(f);
    });
    barraSel.replaceChildren(); barraSel.hidden = !sel.size;
    if (sel.size) {
      const d = el("select", "vn-in"); d.setAttribute("aria-label", "Anclar a"); destinos().forEach(([v, n]) => { const o = el("option", "", n); o.value = v; d.append(o); });
      barraSel.append(el("strong", "", sel.size + " seleccionado(s)"), d, boton("Anclar", "mini", () => anclarA([...sel], d.value, true)), boton("Quitar ancla", "mini", () => anclarA([...sel], d.value, false)), boton("Borrar", "mini rojo", () => borrar([...sel])), boton("Limpiar selección", "mini", () => { sel.clear(); pintar(); }));
    }
    const b = borrados().filter((n) => true); papelera.replaceChildren(el("summary", "", "Papelera (" + b.length + ")"));
    b.forEach((n) => { const f = el("div", "vn-item"); f.append(el("span", "", n), boton("Restaurar", "mini", () => restaurar(n))); papelera.append(f); });
    if (b.length) papelera.append(boton("Olvidar la papelera", "mini rojo", () => { if (!confirm("¿Olvidar la papelera en este navegador? Los archivos no vuelven a la lista.")) return; const t = leer(KB, {}); delete t[sesion]; escribir(KB, t); pintar(); }));
    pie.textContent = vis.length + " de " + archivos.filter((n) => !borrados().includes(n)).length + " archivo(s)" + (sel.size ? " · " + sel.size + " seleccionado(s)" : "") + " · subido en esta visita: " + Math.round(bytes / 1024) + " KB";
  }
  app.addEventListener("keydown", (e) => {
    const t = e.target, escribiendo = t && (t.tagName === "TEXTAREA" || t.tagName === "SELECT" || (t.tagName === "INPUT" && t.type !== "checkbox"));
    if (escribiendo) return;
    if (e.key === "Delete" && sel.size) { e.preventDefault(); borrar([...sel]); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "a") { e.preventDefault(); visibles().forEach((n) => sel.add(n)); pintar(); }
  });
  const vuelve = () => { if (!root.isConnected) { document.removeEventListener("visibilitychange", vuelve); return; } if (!document.hidden) cargar(); };
  document.addEventListener("visibilitychange", vuelve);
  pintar(); cargar(); return true;
}
