// canvas-visor.js — panel 2 «Canvas e imagen / video»: visor REAL de imagen, video, audio y PDF desde un enlace o desde un archivo de este dispositivo.
// Antes llamaba a /chat/org/files (ruta que este sitio no tiene: «Not Found»). La generación de imagen/video es GAP: el motor no está conectado y no se simula.
import { leer, escribir } from "./almacen.js";
import { el, boton, cargarCss } from "./ventanas-comun.js";
const K = "riu_canvas_v1";
export const tipoMedio = (n) => { const e = String(n).split(/[?#]/)[0].split(".").pop().toLowerCase(); if (["png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "avif"].includes(e)) return "imagen"; if (["mp4", "webm", "mov", "m4v", "ogv"].includes(e)) return "video"; if (["mp3", "wav", "ogg", "m4a", "flac"].includes(e)) return "audio"; if (e === "pdf") return "pdf"; return "otro"; };
const sesionActiva = () => { try { const c = JSON.parse(localStorage.getItem("riu_chats_v1") || "[]"), i = Number(localStorage.getItem("riu_chat_activo")) || 0; return (c[Math.min(Math.max(i, 0), c.length - 1)] || {}).sesion || "general"; } catch (e) { return "general"; } };
export function montarCanvas(root, { tell }) {
  if (root.querySelector(".cv-app")) return true;
  cargarCss("ventanas-comun"); cargarCss("paneles-reales");
  [...root.children].forEach((c) => { if (c.tagName !== "H1") c.style.display = "none"; });
  const app = el("div", "cv-app"); root.append(app);
  const visor = el("div", "cv-visor"), info = el("div", "vn-estado"), hist = el("div", "vn-lista");
  let actual = null, objeto = null;
  const vacio = () => { visor.replaceChildren(el("div", "fila-desc", "Abre una imagen, un video, un audio o un PDF con un enlace o desde este dispositivo.")); info.textContent = ""; actual = null; };
  function mostrar(src, nombre, tipo) {
    const t = tipo || tipoMedio(nombre || src); visor.replaceChildren(); let nodo;
    if (t === "imagen") { nodo = el("img"); nodo.alt = nombre || "imagen"; } else if (t === "video") { nodo = el("video"); nodo.controls = true; nodo.playsInline = true; } else if (t === "audio") { nodo = el("audio"); nodo.controls = true; } else if (t === "pdf") { nodo = el("iframe"); nodo.title = nombre || "PDF"; } else { visor.append(el("div", "fila-desc", "No sé mostrar este tipo de archivo. Puedes abrirlo en una pestaña nueva.")); info.textContent = nombre || src; actual = { src, nombre, t }; return; }
    nodo.src = src; nodo.addEventListener("error", () => { info.textContent = "No se pudo cargar (revisa el enlace o que permita mostrarse aquí)."; }); visor.append(nodo); info.textContent = (nombre || src) + " · " + t; actual = { src, nombre, t };
  }
  function recordar(url, nombre, t) { const l = leer(K, { l: [] }).l.filter((x) => x.url !== url); l.unshift({ url, nombre: nombre || url, t }); escribir(K, { l: l.slice(0, 12) }); pintarHist(); }
  function pintarHist() { hist.replaceChildren(); const l = leer(K, { l: [] }).l; if (!l.length) { hist.append(el("div", "fila-desc", "Lo que abras con un enlace aparece aquí.")); return; } l.forEach((x) => { const f = el("div", "vn-item"); f.append(el("span", "", (x.t === "imagen" ? "🖼️ " : x.t === "video" ? "🎬 " : x.t === "audio" ? "🎵 " : x.t === "pdf" ? "📕 " : "🔗 ") + String(x.nombre).slice(0, 80)), boton("Abrir", "mini", () => mostrar(x.url, x.nombre, x.t)), boton("✕", "mini", () => { escribir(K, { l: leer(K, { l: [] }).l.filter((y) => y.url !== x.url) }); pintarHist(); })); hist.append(f); }); }
  // ---- abrir por enlace ----
  const url = el("input", "vn-in"); url.type = "url"; url.placeholder = "https://… imagen, video, audio o PDF"; url.autocomplete = "off"; url.setAttribute("aria-label", "Enlace del medio");
  const abrir = () => { const u = url.value.trim(); if (!/^https?:\/\//i.test(u)) { tell("Pega un enlace que empiece con http o https"); return; } const t = tipoMedio(u); mostrar(u, u.split("/").pop().split("?")[0] || u, t); recordar(u, u.split("/").pop().split("?")[0] || u, t); };
  url.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); abrir(); } });
  const f1 = el("div", "vn-fila"); f1.append(url, boton("Abrir", "mini", abrir));
  // ---- abrir desde el dispositivo ----
  const inp = el("input"); inp.type = "file"; inp.accept = "image/*,video/*,audio/*,application/pdf"; inp.hidden = true;
  inp.addEventListener("change", () => { const f = inp.files && inp.files[0]; if (!f) return; if (objeto) URL.revokeObjectURL(objeto); objeto = URL.createObjectURL(f); const t = f.type.startsWith("image/") ? "imagen" : f.type.startsWith("video/") ? "video" : f.type.startsWith("audio/") ? "audio" : f.type === "application/pdf" ? "pdf" : tipoMedio(f.name); mostrar(objeto, f.name, t); actual.archivo = f; tell("Abierto en este dispositivo: " + f.name); });
  const bFile = boton("Elegir archivo", "mini", () => inp.click());
  // ---- acciones sobre lo abierto ----
  const bSub = boton("Subir al almacén del chat", "mini", async () => {
    if (!actual || !actual.archivo) { tell("Elige primero un archivo de este dispositivo"); return; } if (typeof window.RIU_ACCION !== "function") { tell("El chat aún no tiene conexión con el servidor"); return; }
    const f = actual.archivo; if (f.size > 2000000) { tell("Pesa más de 2 MB"); return; }
    try { const buf = await f.arrayBuffer(); let bin = ""; const by = new Uint8Array(buf); for (let i = 0; i < by.length; i += 8192) bin += String.fromCharCode.apply(null, by.subarray(i, i + 8192)); const r = await window.RIU_ACCION("subir", { nombre: f.name, tipo: f.type || "texto", datos_b64: btoa(bin), sesion: sesionActiva() }); if (r && r.error) throw new Error(String(r.error)); tell("Subido al almacén: " + f.name); } catch (e) { tell("No se pudo subir: " + e.message); }
  });
  const bAnc = boton("Anclar enlace al chat", "mini", () => {
    if (!actual || !/^https?:\/\//.test(actual.src)) { tell("Abre primero algo con un enlace"); return; }
    try { const k = "riu_chats_v1", a = JSON.parse(localStorage.getItem(k) || "[]"); if (!Array.isArray(a) || !a.length) { tell("Abre el chat una vez para poder anclar"); return; } const i = Math.min(Math.max(Number(localStorage.getItem("riu_chat_activo")) || 0, 0), a.length - 1), s = new Set(a[i].anclados || []); s.add("enlace:" + actual.src); a[i].anclados = [...s]; localStorage.setItem(k, JSON.stringify(a)); tell("Enlace anclado al chat activo"); } catch (e) { tell("No se pudo anclar"); }
  });
  const bNue = boton("Abrir en pestaña nueva", "mini", () => { if (actual && /^(https?:|blob:)/.test(actual.src)) window.open(actual.src, "_blank", "noopener"); else tell("No hay nada abierto"); });
  const bCop = boton("Copiar enlace", "mini", async () => { if (!actual || !/^https?:/.test(actual.src)) { tell("No hay un enlace que copiar"); return; } try { await navigator.clipboard.writeText(actual.src); tell("Enlace copiado"); } catch (e) { tell("No se pudo copiar"); } });
  const f2 = el("div", "vn-fila"); f2.append(bFile, bSub, bAnc, bNue, bCop, inp);
  app.append(f1, f2, visor, info, el("div", "vn-t", "Abiertos recientemente"), hist, el("div", "vn-estado", "Generar imagen o video: GAP, el motor de generación todavía no está conectado. Aquí solo se muestra lo que tú abres."));
  vacio(); pintarHist(); return true;
}
