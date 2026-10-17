// anclaje-propuestas.js — 3 propuestas de panel de anclaje con 0 fricción. Se abren con ?panel=a|b|c (el ⚓ del chat abre la propuesta)
// sin reemplazar el panel clásico. Usan los MISMOS datos del chat: anclados de cada objetivo, encendido de cada ancla (Constitución OFF por
// defecto) y «silenciadas» (fila OFF = sigue anclada pero no viaja; contexto.js ya las filtra al enviar).
//  A · una barra: pegas / arrastras / escribes para buscar; ON/OFF por fila.   B · tarjetas por destino.   C · mínimo: un botón ⚓ y una lista.
import { leer, escribir } from "./almacen.js";
import { crearObjetivo, listaWF, listaProyectos, crearProyecto, proyId } from "./objetivos-ancla.js";
import { K_MUTE } from "./contexto.js";
import { clasificar } from "./chat-ancla.js";
import { el, boton, cargarCss } from "./ventanas-comun.js";
const K_DEST = "riu_ancla_prop_dest_v1", VARS = { a: "A · Barra", b: "B · Tarjetas", c: "C · Mínimo" };
const ICO = { chat: "💬", constitucion: "📜", workflows: "🔁", agentes: "🛰", proyecto: "🗂", sandbox: "🧪" };
const chatObj = () => { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return c ? { tipo: "chat", nombre: "Chat", sesion: c.sesion, anclados: c.anclados, siempre: true, get encendido() { return true; }, set encendido(v) {} } : null; };
function objDe(k) {
  if (k === "chat") return chatObj();
  const i = k.indexOf(":"), t = i < 0 ? k : k.slice(0, i), id = i < 0 ? undefined : k.slice(i + 1);
  if (t === "proyecto" && !id) { const n = crearProyecto("Proyecto 1"); return n ? crearObjetivo("proyecto", n) : null; }
  return crearObjetivo(t, id);
}
export function destinos() {
  const d = [["chat", "Chat"], ["constitucion", "Constitución"]];
  listaWF().forEach((w) => d.push(["workflows:" + w.id, "Workflow · " + w.nombre]));
  d.push(["agentes", "Agentes"]);
  const ps = listaProyectos(); if (ps.length) ps.forEach((p) => d.push(["proyecto:" + p.nombre, "Proyecto · " + p.nombre])); else d.push(["proyecto", "Proyecto"]);
  d.push(["sandbox", "Sandbox"]);
  return d.map(([k, n]) => ({ k, n, ic: ICO[k.split(":")[0]] }));
}
const mutes = (ses) => { const m = leer(K_MUTE, {})[ses]; return Array.isArray(m) ? m : []; };
const tras = (o) => { if (o && o.tipo === "chat" && window.RIU_CHAT) window.RIU_CHAT.pintar(); };  // el Set del chat no se guarda solo
export const icono = (t) => (/^raiz:/.test(t) ? "📁" : /^enlace:/.test(t) ? "🔗" : /^handoff:/.test(t) ? "📌" : /^constitucion:/.test(t) ? "📜" : /^secreto:/.test(t) ? "🔑" : "📄");
export const nombre = (t) => { const s = String(t).replace(/^(enlace|raiz|handoff|constitucion|secreto|archivo):/, ""); return s.replace(/^https?:\/\/(www\.)?/, "").replace(/\/+$/, "") || s; };
// ---- modelo: lo comparten las 3 propuestas ----
export const M = {
  filas(filtro) {
    const f = String(filtro || "").trim().toLowerCase(), out = [];
    destinos().forEach((d) => { if (d.k === "proyecto") return; const o = objDe(d.k); if (!o) return; const mu = mutes(o.sesion);
      [...o.anclados].forEach((tok) => { if (!f || tok.toLowerCase().includes(f) || d.n.toLowerCase().includes(f)) out.push({ d, o, tok, on: !mu.includes(tok) }); }); });
    return out;
  },
  cuenta(k) { if (k === "proyecto") return 0; const o = objDe(k); return o ? o.anclados.size : 0; },
  encendido(k) { if (k === "proyecto") return false; const o = objDe(k); return !!(o && o.encendido); },
  alternarDestino(k) { const o = objDe(k); if (!o || o.siempre) return null; o.encendido = !o.encendido; return o.encendido; },
  alternarFila(k, tok) { const o = objDe(k); if (!o) return; const t = leer(K_MUTE, {}), l = Array.isArray(t[o.sesion]) ? t[o.sesion] : [], era = l.includes(tok);
    t[o.sesion] = era ? l.filter((x) => x !== tok) : [...l, tok]; escribir(K_MUTE, t); return era; },
  anclar(k, toks) { const o = objDe(k); if (!o) return 0; let n = 0; toks.forEach((t) => { if (!o.anclados.has(t)) { o.anclados.add(t); n++; } }); tras(o); return n; },
  quitar(k, tok) { const o = objDe(k); if (!o) return false; const r = o.anclados.delete(tok); tras(o); return r; },
  claveReal(k) { if (k !== "proyecto") return k; const o = objDe(k); return o ? "proyecto:" + o.id : k; },
  async subir(k, file) {
    if (file.size > 2_000_000) throw new Error(file.name + ": muy grande (máx ~2 MB)");
    const o = objDe(k), c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (!o || !c || !window.RIU_ACCION) throw new Error("chat no listo");
    const bytes = new Uint8Array(await file.arrayBuffer()); let bin = ""; for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    const dest = o.tipo === "constitucion" ? { destino: "constitucion" } : o.tipo === "proyecto" ? { destino: "proyecto", project_id: o.project_id || proyId(o.id) } : {};
    const r = await window.RIU_ACCION("subir", { nombre: file.name, tipo: file.type || "texto", datos_b64: btoa(bin), sesion: c.sesion, ...dest });
    const n = (r && r.nombre) || file.name; o.anclados.add(n); tras(o); return n;
  },
  async archivos() { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); const r = await window.RIU_ACCION("archivos", { sesion: c ? c.sesion : undefined }); return Array.isArray(r.archivos) ? r.archivos : []; } catch (e) { return []; } },
  // texto pegado: enlaces/raíces se anclan tal cual; texto largo sin enlaces se guarda como nota .txt y se ancla (real, en la carpeta del chat)
  async pegar(k, texto) {
    const items = clasificar(texto); if (items.length) return { n: M.anclar(k, items), tipo: "enlace" };
    const t = String(texto || "").trim(); if (!t) return { n: 0 };
    const d = new Date(), p = (x) => String(x).padStart(2, "0"), nom = "nota-" + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + "-" + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds()) + ".txt";
    await M.subir(k, new File([t], nom, { type: "text/plain" })); return { n: 1, tipo: "nota", nom };
  },
};
// ---- piezas de interfaz ----
const sw = (on, etq, fn, fijo) => { const b = el("button", "ap-sw" + (on ? " on" : "") + (fijo ? " fijo" : "")); b.type = "button"; b.setAttribute("role", "switch"); b.setAttribute("aria-checked", String(!!on)); b.setAttribute("aria-label", etq); b.title = fijo ? "Siempre encendido" : on ? "ON · viaja con cada mensaje" : "OFF · no se envía"; if (fijo) b.disabled = true; else b.addEventListener("click", fn); return b; };
function fila(f, { tag, alCambio, tell, deshacer }) {
  const r = el("div", "ap-fila" + (f.on ? "" : " off")); r.dataset.tok = f.tok; r.dataset.dest = f.d.k;
  const n = el("span", "ap-nom"); n.append(el("span", "ap-ic", icono(f.tok)), el("span", "ap-txt", nombre(f.tok))); n.title = f.tok;
  if (tag) n.append(el("small", "ap-tag", f.d.ic + " " + f.d.n));
  if (/^(enlace|raiz):https?:\/\//.test(f.tok)) { n.classList.add("ap-link"); n.addEventListener("click", () => window.open(f.tok.replace(/^[a-z]+:/, ""), "_blank", "noopener")); }
  const s = sw(f.on, "Encender o apagar " + nombre(f.tok), () => { const ahora = M.alternarFila(f.d.k, f.tok); tell(nombre(f.tok) + (ahora ? ": ON" : ": OFF · sigue anclado, no viaja")); alCambio(); });
  const x = boton("✕", "ap-x", () => { M.quitar(f.d.k, f.tok); deshacer(f.d.k, f.tok); alCambio(); }); x.setAttribute("aria-label", "Quitar " + nombre(f.tok));
  r.append(n, s, x); return r;
}
function selectorDestino(val, fn) {
  const s = el("select", "ap-dest"); s.setAttribute("aria-label", "Anclar en");
  destinos().forEach((d) => { const o = el("option", "", d.ic + " " + d.n); o.value = d.k; s.append(o); });
  s.value = destinos().some((d) => d.k === val) ? val : "chat"; s.addEventListener("change", () => fn(s.value)); return s;
}
export function montarPropuestasAncla({ root, q, tell }) {
  // ⚓ abre la propuesta A (barra única) por defecto; ?panel=b|c abre B o C; el panel clásico queda detrás del botón «Clásico».
  const vUrl = (new URLSearchParams(location.search).get("panel") || "").toLowerCase(), v0 = VARS[vUrl] ? vUrl : "a";
  let clasico = false;  // true = este clic va al panel clásico (botón «Clásico» o RIU_ANCLA_ABRIR de workflow/constitución)
  const abrirClasico = () => { const b = q("#btn-ancla"), s = q("#ventana-ancla"); if (!b || !s) return; clasico = true; try { if (s.hidden) b.click(); else if (window.RIU_ANCLA_REFRESCAR) window.RIU_ANCLA_REFRESCAR(); } finally { clasico = false; } };
  const ba = q("#btn-ancla"); if (ba) ba.addEventListener("click", (e) => { if (clasico) return; e.stopImmediatePropagation(); e.preventDefault(); if (sheet && !sheet.hidden) cerrar(); else abrir(); }, true);
  const abrirObj = window.RIU_ANCLA_ABRIR; if (typeof abrirObj === "function") window.RIU_ANCLA_ABRIR = (...a) => { clasico = true; try { return abrirObj(...a); } finally { clasico = false; } };
  window.RIU_ANCLA_PROP = (v) => abrir(v);
  if (VARS[vUrl]) setTimeout(() => abrir(vUrl), 0);  // ?panel=a|b|c abre el panel al cargar (enlace directo)
  const abiertas = new Set(["chat"]);  // tarjetas abiertas en B
  let sheet, caja, cuerpo, aviso, variante = v0, destSel = leer(K_DEST, "chat"), filtro = "", archivos = [], tAviso = 0, ultimo = null;
  const decir = (t, conDeshacer) => { if (!aviso) { tell(t); return; } aviso.replaceChildren(el("span", "", t)); if (conDeshacer) aviso.append(boton("Deshacer", "ap-undo", () => { if (ultimo) { M.anclar(ultimo.k, [ultimo.tok]); ultimo = null; aviso.hidden = true; pintar(); } })); aviso.hidden = false; clearTimeout(tAviso); tAviso = setTimeout(() => { aviso.hidden = true; }, conDeshacer ? 7000 : 3500); };
  const deshacer = (k, tok) => { ultimo = { k, tok }; decir("Quitado: " + nombre(tok), true); };
  const fijarDest = (k) => { destSel = k; escribir(K_DEST, k); };
  async function soltar(k, files) { for (const f of files) { try { const n = await M.subir(k, f); decir("Anclado: " + n); } catch (e) { decir("No se pudo subir: " + (e.message || e)); } } fijarDest(M.claveReal(k)); abiertas.add(M.claveReal(k)); pintar(); }
  async function pegarEn(k, texto) { try { const r = await M.pegar(k, texto); decir(r.n ? (r.tipo === "nota" ? "Nota anclada: " + r.nom : r.n + " anclado(s)") : "Ya estaba anclado"); fijarDest(M.claveReal(k)); abiertas.add(M.claveReal(k)); pintar(); return r.n > 0 || r.tipo === "nota"; } catch (e) { decir("No se pudo: " + (e.message || e)); return false; } }
  const picker = el("input"); picker.type = "file"; picker.multiple = true; picker.hidden = true; let pickDest = "chat";
  picker.addEventListener("change", () => { const fs = [...picker.files]; picker.value = ""; if (fs.length) soltar(pickDest, fs); });
  const elegir = (k) => { pickDest = k; picker.click(); };
  const zonaDrop = (nodo, kFn) => {
    nodo.addEventListener("dragover", (e) => { e.preventDefault(); nodo.classList.add("ap-drop"); });
    nodo.addEventListener("dragleave", () => nodo.classList.remove("ap-drop"));
    nodo.addEventListener("drop", (e) => { e.preventDefault(); e.stopPropagation(); nodo.classList.remove("ap-drop"); const fs = [...((e.dataTransfer && e.dataTransfer.files) || [])], t = e.dataTransfer && e.dataTransfer.getData("text"); if (fs.length) soltar(kFn(), fs); else if (t) pegarEn(kFn(), t); });
  };
  function crear() {
    sheet = el("div", "sheet ap-sheet"); sheet.id = "ancla-prop"; sheet.hidden = true; sheet.setAttribute("role", "dialog"); sheet.setAttribute("aria-modal", "true"); sheet.setAttribute("aria-label", "Anclaje");
    caja = el("div", "va-caja ap-caja"); const head = el("div", "ap-head"), tabs = el("div", "ap-tabs");
    Object.keys(VARS).forEach((k) => { const b = boton(k.toUpperCase(), "ap-tab", () => abrir(k)); b.dataset.v = k; b.title = VARS[k]; tabs.append(b); });
    const bClasico = boton("Clásico", "ap-clasico", () => { cerrar(); abrirClasico(); });
    const x = boton("✕", "ap-cerrar", cerrar); x.setAttribute("aria-label", "Cerrar");
    head.append(el("strong", "", "⚓ Anclaje"), tabs, bClasico, x);
    cuerpo = el("div", "ap-cuerpo"); aviso = el("div", "ap-aviso"); aviso.hidden = true; aviso.setAttribute("role", "status");
    caja.append(head, cuerpo, aviso, picker); sheet.append(caja); root.append(sheet);
    sheet.addEventListener("click", (e) => { if (e.target === sheet) cerrar(); });
    sheet.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(); });
    window.addEventListener("riu:almacen", () => { if (!sheet.hidden && !sheet.contains(document.activeElement && document.activeElement.closest ? document.activeElement : null)) pintar(); });
  }
  function abrir(v) {
    if (!sheet) { cargarCss("anclaje-propuestas"); crear(); }
    if (VARS[v]) { variante = v; try { const u = new URL(location.href); u.searchParams.set("panel", v); history.replaceState(null, "", u); } catch (e) {} }
    root.querySelectorAll(".sheet").forEach((h) => { if (h !== sheet) h.hidden = true; });
    sheet.hidden = false; sheet.dataset.v = variante; filtro = ""; pintar(true);
    M.archivos().then((l) => { archivos = l; if (!sheet.hidden) pintar(); });
  }
  function cerrar() { if (sheet) sheet.hidden = true; }
  function pintar(enfocar) {
    if (!sheet) return;
    caja.querySelectorAll(".ap-tab").forEach((b) => { const on = b.dataset.v === variante; b.classList.toggle("on", on); b.setAttribute("aria-pressed", String(on)); });
    const foco = document.activeElement && sheet.contains(document.activeElement) ? document.activeElement.dataset.ap : null, pos = foco && document.activeElement.selectionStart;
    cuerpo.replaceChildren(variante === "b" ? vistaB() : variante === "c" ? vistaC() : vistaA());
    const f = foco ? cuerpo.querySelector('[data-ap="' + foco + '"]') : enfocar ? cuerpo.querySelector("[data-ap=omni],[data-ap=ancla]") : null;
    if (f) { try { f.focus({ preventScroll: true }); if (pos != null && f.setSelectionRange) f.setSelectionRange(pos, pos); } catch (e) {} }
  }
  const ctx = () => ({ tell: (t) => decir(t), alCambio: pintar, deshacer });
  const sugerencias = (k) => { const f = filtro.trim().toLowerCase(); if (f.length < 2) return null; const o = objDe(k), ya = o ? o.anclados : new Set();
    const l = archivos.filter((a) => a.toLowerCase().includes(f) && !ya.has(a)).slice(0, 5); if (!l.length) return null;
    const box = el("div", "ap-sug"); box.append(el("small", "ap-sub", "Archivos del chat"));
    l.forEach((a) => box.append(boton("＋ 📄 " + a, "ap-sug-b", () => { M.anclar(k, [a]); decir("Anclado: " + a); pintar(); }))); return box; };
  const vacio = (t) => el("div", "ap-vacio", t);
  // ---------- A · una sola barra ----------
  function vistaA() {
    const w = el("div", "ap-a"), barra = el("div", "ap-barra"), inp = el("input", "ap-omni");
    inp.type = "search"; inp.dataset.ap = "omni"; inp.placeholder = "Pega enlace, suelta archivo o busca"; inp.value = filtro; inp.autocomplete = "off"; inp.setAttribute("aria-label", "Anclar o buscar");
    inp.addEventListener("input", () => { filtro = inp.value; pintar(); });
    inp.addEventListener("paste", (e) => { const fs = [...((e.clipboardData && e.clipboardData.files) || [])], t = (e.clipboardData && e.clipboardData.getData("text")) || "";
      if (fs.length) { e.preventDefault(); soltar(destSel, fs); return; }
      if (clasificar(t).length || t.length > 80 || /\n/.test(t)) { e.preventDefault(); filtro = ""; pegarEn(destSel, t); } });
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter" && inp.value.trim()) { e.preventDefault(); const t = inp.value; filtro = ""; pegarEn(destSel, t); } });
    const clip = boton("📎", "ap-ic-b", () => elegir(destSel)); clip.setAttribute("aria-label", "Subir y anclar archivo");
    barra.append(inp, clip); zonaDrop(w, () => destSel);
    const pie = el("div", "ap-pie"); pie.append(el("span", "", "Se ancla en"), selectorDestino(destSel, (k) => { fijarDest(k); pintar(); }), el("span", "ap-hint", "Enter ancla · ✕ quita"));
    w.append(barra, pie); const sg = sugerencias(destSel); if (sg) w.append(sg);
    const lista = el("div", "ap-lista"), fs = M.filas(filtro), c = ctx();
    if (!fs.length) lista.append(vacio(filtro ? "Nada coincide con «" + filtro + "». Enter para anclarlo." : "Nada anclado. Pega un enlace aquí arriba o suelta un archivo."));
    let g = null;
    fs.forEach((f) => { if (g !== f.d.k) { g = f.d.k; const h = el("div", "ap-grupo"); h.append(el("span", "", f.d.ic + " " + f.d.n), f.o.siempre ? el("small", "ap-sub", "siempre") : sw(f.o.encendido, f.d.n + " encendido", () => { const on = M.alternarDestino(f.d.k); decir(f.d.n + (on ? ": ON · viaja con cada mensaje" : ": OFF · no se envía")); pintar(); })); lista.append(h); } lista.append(fila(f, c)); });
    const con = destinos().find((d) => d.k === "constitucion"); if (!fs.some((f) => f.d.k === "constitucion") && !filtro) { const h = el("div", "ap-grupo ap-grupo-sola"); h.append(el("span", "", con.ic + " Constitución"), sw(M.encendido("constitucion"), "Constitución encendida", () => { const on = M.alternarDestino("constitucion"); decir("Constitución" + (on ? ": ON" : ": OFF")); pintar(); })); lista.append(h); }
    w.append(lista); return w;
  }
  // ---------- B · tarjetas por destino ----------
  function vistaB() {
    const w = el("div", "ap-b"), bus = el("input", "ap-buscar"); bus.type = "search"; bus.dataset.ap = "buscar"; bus.placeholder = "🔎 Buscar en todas las anclas"; bus.value = filtro; bus.setAttribute("aria-label", "Buscar");
    bus.addEventListener("input", () => { filtro = bus.value; pintar(); }); w.append(bus);
    const todas = M.filas(filtro), c = ctx(), grid = el("div", "ap-grid");
    destinos().forEach((d) => {
      const mias = todas.filter((f) => f.d.k === d.k), n = M.cuenta(d.k), abierta = abiertas.has(d.k) || (filtro && mias.length);
      if (filtro && !mias.length) return;
      const card = el("div", "ap-card" + (abierta ? " abierta" : "") + (M.encendido(d.k) || d.k === "chat" ? " encendida" : "")); card.dataset.dest = d.k;
      const h = el("div", "ap-card-h"), t = el("button", "ap-card-t"); t.type = "button"; t.setAttribute("aria-expanded", String(!!abierta));
      t.append(el("span", "ap-card-ic", d.ic), el("span", "ap-card-n", d.n), el("span", "ap-cnt", String(n)));
      t.addEventListener("click", () => { abiertas.has(d.k) ? abiertas.delete(d.k) : abiertas.add(d.k); pintar(); });
      h.append(t, d.k === "chat" ? sw(true, "Chat", null, true) : sw(M.encendido(d.k), d.n + " encendido", () => { const on = M.alternarDestino(d.k); if (on === null) { decir("Ancla algo primero"); return; } decir(d.n + (on ? ": ON · viaja con cada mensaje" : ": OFF · no se envía")); pintar(); }));
      card.append(h); zonaDrop(card, () => d.k);
      if (abierta) {
        const body = el("div", "ap-card-b"), inp = el("input", "ap-card-in"); inp.dataset.ap = "in-" + d.k; inp.placeholder = "Pega enlace o texto · suelta archivo"; inp.setAttribute("aria-label", "Anclar en " + d.n);
        inp.addEventListener("paste", (e) => { const fs = [...((e.clipboardData && e.clipboardData.files) || [])]; if (fs.length) { e.preventDefault(); soltar(d.k, fs); return; } setTimeout(() => { const v = inp.value; if (v.trim()) { inp.value = ""; pegarEn(d.k, v); } }, 0); });
        inp.addEventListener("keydown", (e) => { if (e.key === "Enter" && inp.value.trim()) { e.preventDefault(); const v = inp.value; inp.value = ""; pegarEn(d.k, v); } });
        const clip = boton("📎", "ap-ic-b", () => elegir(d.k)); clip.setAttribute("aria-label", "Subir a " + d.n);
        const r = el("div", "ap-card-r"); r.append(inp, clip); body.append(r);
        if (!mias.length) body.append(vacio(d.k === "constitucion" ? "Ancla aquí las reglas; enciende la tarjeta para que viajen." : "Vacío."));
        mias.forEach((f) => body.append(fila(f, c))); card.append(body);
      }
      grid.append(card);
    });
    if (!grid.children.length) grid.append(vacio("Nada coincide con «" + filtro + "»."));
    w.append(grid); return w;
  }
  // ---------- C · mínimo: un botón ⚓ y una lista ----------
  let buscando = false;
  function vistaC() {
    const w = el("div", "ap-c"), top = el("div", "ap-c-top"), d = destinos().find((x) => x.k === destSel) || destinos()[0];
    const big = boton("⚓", "ap-big", async () => {
      let t = ""; try { t = navigator.clipboard && navigator.clipboard.readText ? await navigator.clipboard.readText() : ""; } catch (e) {}
      if (t && clasificar(t).length) pegarEn(destSel, t); else elegir(destSel);
    }); big.dataset.ap = "ancla"; big.setAttribute("aria-label", "Anclar: lo copiado o un archivo"); big.title = "Ancla lo que copiaste; si no hay enlace, elige archivo";
    const info = el("div", "ap-c-info"); info.append(el("strong", "", "Anclar"), el("small", "ap-sub", "Toca: ancla lo copiado o elige archivo · también puedes pegar o soltar aquí"));
    const lupa = boton("🔎", "ap-ic-b" + (buscando ? " on" : ""), () => { buscando = !buscando; if (!buscando) filtro = ""; pintar(); if (buscando) { const b = cuerpo.querySelector("[data-ap=buscarc]"); if (b) b.focus(); } }); lupa.setAttribute("aria-label", "Buscar");
    top.append(big, info, lupa); w.append(top);
    const pie = el("div", "ap-pie"); pie.append(el("span", "", "en"), selectorDestino(destSel, (k) => { fijarDest(k); pintar(); }));
    if (d.k !== "chat") pie.append(sw(M.encendido(d.k), d.n + " encendido", () => { const on = M.alternarDestino(d.k); if (on === null) return; decir(d.n + (on ? ": ON" : ": OFF")); pintar(); }));
    w.append(pie);
    if (buscando) { const b = el("input", "ap-buscar"); b.type = "search"; b.dataset.ap = "buscarc"; b.placeholder = "Buscar…"; b.value = filtro; b.setAttribute("aria-label", "Buscar"); b.addEventListener("input", () => { filtro = b.value; pintar(); }); w.append(b); const sg = sugerencias(destSel); if (sg) w.append(sg); }
    const lista = el("div", "ap-lista"), fs = M.filas(filtro).filter((f) => f.d.k === destSel || M.claveReal(destSel) === f.d.k), c = ctx();
    if (!fs.length) lista.append(vacio(filtro ? "Nada coincide." : "Nada anclado en " + d.n + "."));
    fs.forEach((f) => lista.append(fila(f, { ...c, tag: false })));
    w.append(lista);
    w.addEventListener("paste", (e) => { if (e.target && e.target.dataset && e.target.dataset.ap === "buscarc") return; const fs2 = [...((e.clipboardData && e.clipboardData.files) || [])], t = (e.clipboardData && e.clipboardData.getData("text")) || ""; e.preventDefault(); if (fs2.length) soltar(destSel, fs2); else if (t.trim()) pegarEn(destSel, t); });
    zonaDrop(w, () => destSel); return w;
  }
}
