// handoff-editor.js — "Mi handoff" editable con TEXTO, ENLACES y ARCHIVOS ADJUNTOS. Todo queda dentro del mismo handoff (mismo guardado de siempre).
import { el, boton, cargarCss } from "./ventanas-comun.js";
export function montarHandoffEditor({ root, q, tell }) {
  const ta = q("#mi-handoff"); if (!ta || ta.dataset.ed) return; ta.dataset.ed = "1"; cargarCss("ventanas-comun");
  const barra = el("div", "vn-sec vn-hoed");
  const guardar = () => { const b = q("#mh-guardar"); if (b) b.click(); };
  const insertar = (linea) => { const v = ta.value.replace(/\s*$/, ""); ta.value = (v ? v + "\n" : "") + linea; ta.dispatchEvent(new Event("input", { bubbles: true })); guardar(); };
  const sesion = () => { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return c ? c.sesion : "general"; };
  const en = el("input", "vn-in"); en.placeholder = "Enlace para el handoff…"; en.autocomplete = "off"; en.setAttribute("aria-label", "Enlace para el handoff");
  const bEn = boton("＋ Enlace", "mini", () => { const u = en.value.trim(); if (!/^https?:\/\//i.test(u)) { tell("Pega un enlace que empiece con http o https"); return; } insertar("Enlace: " + u); en.value = ""; tell("Enlace añadido al handoff"); });
  const fe = el("div", "vn-fila"); fe.append(en, bEn);
  const lista = el("div", "vn-traer"); lista.hidden = true;
  const bAr = boton("＋ Archivo", "mini", async () => {
    lista.hidden = !lista.hidden; if (lista.hidden) return; lista.replaceChildren(el("div", "fila-desc", "Cargando…"));
    try {
      const r = await window.RIU_ACCION("archivos", { sesion: sesion() }); lista.replaceChildren();
      const nombres = r.archivos || [];
      if (!nombres.length) lista.append(el("div", "fila-desc", "Aún no hay archivos. Usa «Subir y añadir»."));
      nombres.forEach((n) => lista.append(boton("📄 " + n, "mini", () => { insertar("Archivo: " + n); lista.hidden = true; tell("Archivo añadido al handoff: " + n); })));
    } catch (e) { lista.replaceChildren(el("div", "fila-desc", "No se pudo leer la carpeta de archivos: " + e.message)); }
  });
  const inp = el("input"); inp.type = "file"; inp.hidden = true;
  inp.addEventListener("change", async () => {
    const f = inp.files && inp.files[0]; if (!f) return;
    try {
      const buf = await f.arrayBuffer(); if (buf.byteLength > 2000000) { tell("Archivo muy grande (máx ~2 MB)"); return; }
      let bin = ""; const bytes = new Uint8Array(buf); for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
      const r = await window.RIU_ACCION("subir", { nombre: f.name, tipo: f.type || "texto", datos_b64: btoa(bin), sesion: sesion() });
      insertar("Archivo: " + (r.nombre || f.name)); tell("Subido y añadido al handoff: " + (r.nombre || f.name));
    } catch (e) { tell("No se pudo subir: " + e.message); }
    inp.value = "";
  });
  const bSub = boton("Subir y añadir", "mini", () => inp.click());
  const fa = el("div", "vn-fila"); fa.append(bAr, bSub);
  barra.append(el("div", "vn-t", "Handoff editable: texto, enlaces y archivos"), fe, fa, lista, inp);
  ta.after(barra);
}
