// panel-apariencia.js — ventana "Apariencia": estudio de letras (V10), colores, estilos listos, tema, iconos de botones (V09), avisos y tamaño.
// Panel propio (se llama por HTML desde el shell). Aplica en vivo con apariencia-aplicar.js y guarda en este navegador.
import { ICONOS, TRAZOS, PALETA, SENAL, FUENTES, FUENTES_ETQ, TEMAS, PRESETS, ROLES, DESTINOS, COLOR_DEF } from "./apariencia-datos.js";
import { cargar, guardarEstado, construirCSS, HEX } from "./apariencia-aplicar.js";

const svg = (id, w = 20) => '<svg viewBox="0 0 24 24" width="' + w + '" height="' + w + '" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (TRAZOS[id] || TRAZOS.info) + "</svg>";
const lum = (h) => { const c = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4))); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
const contraste = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const bajar = (nombre, texto, tipo) => {
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([texto], { type: tipo })); a.download = nombre;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
};
const sanear = (o) => {  // solo valores conocidos y validos (importar / datos rotos)
  const r = { colores: {}, tipo: {}, iconos: {} }; if (!o || typeof o !== "object") return r;
  if (HEX.test(o.senal)) r.senal = o.senal;
  const num = (v, a, b) => (Number.isFinite(Number(v)) ? Math.min(b, Math.max(a, Number(v))) : undefined);
  for (const [id, , , d] of ROLES) {
    if (o.colores && HEX.test(o.colores[id])) r.colores[id] = o.colores[id];
    const t = o.tipo && o.tipo[id]; if (!t || typeof t !== "object") continue;
    const x = {};
    if (FUENTES[t.fuente]) x.fuente = t.fuente;
    [["tam", 10, 48], ["peso", 300, 900], ["esp", -1, 4], ["alto", 1, 2.3]].forEach(([k, a, b]) => { const v = num(t[k], a, b); if (v !== undefined) x[k] = v; });
    ["cursiva", "subrayado", "mayus"].forEach((k) => { if (t[k] === true) x[k] = true; });
    if (t.alinear === "center" || t.alinear === "right") x.alinear = t.alinear;
    if (typeof t.muestra === "string") x.muestra = t.muestra.slice(0, 200);
    if (Object.keys(x).length) r.tipo[id] = x;
  }
  for (const [id] of DESTINOS) if (o.iconos && TRAZOS[o.iconos[id]]) r.iconos[id] = o.iconos[id];
  const e = num(o.escala, 90, 115); if (e !== undefined && e !== 100) r.escala = e;
  const s = num(o.avisoSeg, 2, 15); if (s !== undefined) r.avisoSeg = s;
  return r;
};

export async function mount(root, { tell } = {}) {
  const q = (s) => root.querySelector(s);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const avisa = (m) => { if (tell) tell(m); };
  let est = sanear(cargar()), rol = ROLES[0][0], destino = DESTINOS[0][0];
  const guardar = () => guardarEstado(est);
  const def = (id) => ROLES.find((r) => r[0] === id)[3];
  const tipo = (id) => ({ ...def(id), ...(est.tipo[id] || {}) });
  const colorDe = (id) => est.colores[id] || COLOR_DEF[id] || "#EDEDED";
  const cambiaTipo = (id, k, v) => { est.tipo[id] = { ...(est.tipo[id] || {}), [k]: v }; guardar(); };
  const swatch = (hex, nombre, on, fn) => { const b = el("button", "ap-sw"); b.type = "button"; b.style.background = hex; b.title = nombre + " " + hex.toUpperCase(); b.setAttribute("aria-label", nombre); b.setAttribute("aria-pressed", String(on)); b.addEventListener("click", fn); return b; };
  const chip = (txt, on, fn, rolAria) => { const b = el("button", "ap-chip" + (on ? " on" : ""), txt); b.type = "button"; if (rolAria) { b.setAttribute("role", rolAria); b.setAttribute(rolAria === "tab" ? "aria-selected" : "aria-checked", String(on)); } b.addEventListener("click", fn); return b; };

  // 1 · tema (el mismo selector del encabezado: se guarda como siempre)
  const pintarTemas = () => {
    const sel = document.querySelector("#theme"), actual = document.documentElement.dataset.theme || "gris", box = q("#ap-temas"); box.replaceChildren();
    TEMAS.forEach(([id, nombre]) => box.append(chip(nombre, id === actual, () => { if (sel) { sel.value = id; sel.dispatchEvent(new Event("change")); } else document.documentElement.dataset.theme = id; pintarTemas(); }, "radio")));
  };
  // 2 · color de señal
  const pintarSenal = () => {
    const box = q("#ap-senal"); box.replaceChildren();
    SENAL.forEach(([n, h]) => box.append(swatch(h, n, (est.senal || "").toLowerCase() === h.toLowerCase(), () => { est.senal = h; guardar(); pintarSenal(); })));
    q("#ap-senal-custom").value = est.senal || "#0848f7";
  };
  q("#ap-senal-custom").addEventListener("input", (e) => { est.senal = e.target.value; guardar(); pintarSenal(); });
  q("#ap-senal-reset").addEventListener("click", () => { delete est.senal; guardar(); pintarSenal(); });
  // 3 · estilos listos
  const pintarPresets = () => {
    const box = q("#ap-presets"); box.replaceChildren();
    PRESETS.forEach(([n, mapa]) => box.append(chip(n, false, () => { est.colores = {}; for (const [k, v] of Object.entries(mapa)) if (HEX.test(v)) est.colores[k] = v; guardar(); pintarEstudio(); avisa("Estilo aplicado: " + n); })));
  };
  // 4 · estudio de letras
  const pintarRoles = () => {
    const box = q("#ap-roles"); box.replaceChildren();
    ROLES.forEach(([id, n]) => box.append(chip(n, id === rol, () => { rol = id; pintarRoles(); pintarEstudio(); }, "tab")));
  };
  const fuenteSel = q("#ap-fuente"); Object.keys(FUENTES).forEach((k) => { const o = el("option", "", FUENTES_ETQ[k] || k); o.value = k; fuenteSel.append(o); });
  const flags = [["cursiva", "Cursiva"], ["subrayado", "Subrayado"], ["mayus", "MAYÚSCULAS"]], alin = [["left", "Izquierda"], ["center", "Centro"], ["right", "Derecha"]];
  const pintarEstudio = () => {
    const t = tipo(rol), c = colorDe(rol), caja = q("#ap-colores"); caja.replaceChildren();
    PALETA.forEach(([n, h]) => caja.append(swatch(h, n, h.toLowerCase() === c.toLowerCase(), () => { est.colores[rol] = h; guardar(); pintarEstudio(); })));
    q("#ap-color-custom").value = c; q("#ap-hex").textContent = c.toUpperCase();
    const fondo = (getComputedStyle(document.documentElement).getPropertyValue("--panel") || "").trim(), bg = HEX.test(fondo) ? fondo : "#2A2A2A", r = contraste(c, bg);
    const cs = q("#ap-contraste"); cs.textContent = "Contraste " + r.toFixed(1) + ":1 · " + (r >= 7 ? "AAA" : r >= 4.5 ? "AA" : r >= 3 ? "solo texto grande" : "bajo, difícil de leer"); cs.dataset.nivel = r >= 4.5 ? "ok" : r >= 3 ? "medio" : "bajo";
    fuenteSel.value = t.fuente;
    [["tam", "ap-tam", "ap-v-tam", " px"], ["peso", "ap-peso", "ap-v-peso", ""], ["esp", "ap-esp", "ap-v-esp", " px"], ["alto", "ap-alto", "ap-v-alto", ""]].forEach(([k, i, o, u]) => { q("#" + i).value = t[k]; q("#" + o).textContent = t[k] + u; });
    q("#ap-flags").querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(!!t[b.dataset.k])));
    q("#ap-alinear").querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.a === t.alinear)));
    q("#ap-muestra-txt").value = t.muestra; pintarMuestra();
  };
  const pintarMuestra = () => {
    const t = tipo(rol), m = q("#ap-muestra"); m.textContent = t.muestra || "Texto de ejemplo";
    Object.assign(m.style, { color: colorDe(rol), fontFamily: FUENTES[t.fuente], fontSize: t.tam + "px", fontWeight: t.peso, letterSpacing: t.esp + "px", lineHeight: t.alto, fontStyle: t.cursiva ? "italic" : "normal", textDecoration: t.subrayado ? "underline" : "none", textTransform: t.mayus ? "uppercase" : "none", textAlign: t.alinear });
  };
  flags.forEach(([k, n]) => { const b = el("button", "ap-chip", n); b.type = "button"; b.dataset.k = k; b.addEventListener("click", () => { cambiaTipo(rol, k, !tipo(rol)[k]); pintarEstudio(); }); q("#ap-flags").append(b); });
  alin.forEach(([a, n]) => { const b = el("button", "ap-chip", n); b.type = "button"; b.dataset.a = a; b.addEventListener("click", () => { cambiaTipo(rol, "alinear", a); pintarEstudio(); }); q("#ap-alinear").append(b); });
  fuenteSel.addEventListener("change", () => { cambiaTipo(rol, "fuente", fuenteSel.value); pintarEstudio(); });
  [["tam", "ap-tam", "ap-v-tam", " px"], ["peso", "ap-peso", "ap-v-peso", ""], ["esp", "ap-esp", "ap-v-esp", " px"], ["alto", "ap-alto", "ap-v-alto", ""]].forEach(([k, i, o, u]) => q("#" + i).addEventListener("input", (e) => { const v = Number(e.target.value); cambiaTipo(rol, k, v); q("#" + o).textContent = v + u; pintarMuestra(); }));
  q("#ap-color-custom").addEventListener("input", (e) => { est.colores[rol] = e.target.value; guardar(); pintarEstudio(); });
  q("#ap-muestra-txt").addEventListener("input", (e) => { cambiaTipo(rol, "muestra", e.target.value.slice(0, 200)); pintarMuestra(); });
  q("#ap-rol-reset").addEventListener("click", () => { delete est.colores[rol]; delete est.tipo[rol]; guardar(); pintarEstudio(); avisa("Letra restablecida"); });
  q("#ap-letras-reset").addEventListener("click", () => { est.colores = {}; est.tipo = {}; guardar(); pintarEstudio(); avisa("Todas las letras restablecidas"); });
  const cssTexto = () => "/* YAIWES · apariencia */\n" + (est.senal ? ":root{--active:" + est.senal + ";--status-blue:" + est.senal + "}\n" : "") + (construirCSS(est) || "/* sin cambios */");
  q("#ap-css-bajar").addEventListener("click", () => { bajar("yaiwes-apariencia.css", cssTexto(), "text/css"); avisa("CSS descargado"); });
  q("#ap-css-copiar").addEventListener("click", async () => { try { await navigator.clipboard.writeText(cssTexto()); avisa("CSS copiado"); } catch (e) { avisa("No se pudo copiar: usa Descargar CSS"); } });
  // 5 · iconos
  const pintarDestinos = () => {
    const box = q("#ap-destinos"); box.replaceChildren();
    DESTINOS.forEach(([id, n]) => { const b = chip("", id === destino, () => { destino = id; pintarDestinos(); pintarIconos(); }, "tab"); if (est.iconos[id]) b.insertAdjacentHTML("beforeend", svg(est.iconos[id], 16)); b.append(document.createTextNode(n)); box.append(b); });
  };
  const pintarIconos = () => {
    const box = q("#ap-iconos"), f = q("#ap-icono-buscar").value.trim().toLowerCase(); box.replaceChildren();
    ICONOS.filter(([id, n, d]) => !f || (id + " " + n + " " + d).toLowerCase().includes(f)).forEach(([id, n, d], i) => {
      const b = el("button", "ap-icono"); b.type = "button"; b.style.setProperty("--i", i); b.title = n + " · " + d; b.setAttribute("aria-label", n);
      b.setAttribute("aria-pressed", String(est.iconos[destino] === id)); b.innerHTML = svg(id, 22); b.append(el("span", "", n));
      b.addEventListener("click", () => { if (est.iconos[destino] === id) delete est.iconos[destino]; else est.iconos[destino] = id; guardar(); pintarDestinos(); pintarIconos(); });
      box.append(b);
    });
    if (!box.children.length) box.append(el("p", "muted", "Ningún icono coincide."));
  };
  q("#ap-icono-buscar").addEventListener("input", pintarIconos);
  q("#ap-iconos-reset").addEventListener("click", () => { est.iconos = {}; guardar(); pintarDestinos(); pintarIconos(); avisa("Iconos restablecidos"); });
  // 6 · avisos y tamaño (duration-picker)
  const pintarAvisos = () => { q("#ap-aviso-v").textContent = String(est.avisoSeg || 4.5).replace(".", ",") + " s"; q("#ap-escala").value = est.escala || 100; q("#ap-v-escala").textContent = (est.escala || 100) + " %"; };
  const paso = (d) => { est.avisoSeg = Math.min(15, Math.max(2, Math.round(((est.avisoSeg || 4.5) + d) * 2) / 2)); guardar(); pintarAvisos(); };
  q("#ap-aviso-menos").addEventListener("click", () => paso(-0.5)); q("#ap-aviso-mas").addEventListener("click", () => paso(0.5));
  q("#ap-aviso-probar").addEventListener("click", () => avisa("Así se ve un aviso"));
  q("#ap-escala").addEventListener("input", (e) => { const v = Number(e.target.value); if (v === 100) delete est.escala; else est.escala = v; guardar(); pintarAvisos(); });
  // 7 · guardar y recuperar
  q("#ap-exportar").addEventListener("click", () => { bajar("yaiwes-apariencia.json", JSON.stringify(est, null, 2), "application/json"); avisa("Apariencia exportada"); });
  q("#ap-importar").addEventListener("change", async (e) => {
    const f = e.target.files && e.target.files[0]; if (!f) return;
    try { est = sanear(JSON.parse(await f.text())); guardar(); pintarTodo(); avisa("Apariencia importada"); } catch (err) { avisa("Ese archivo no es una apariencia válida"); }
    e.target.value = "";
  });
  q("#ap-todo-reset").addEventListener("click", () => {
    est = { colores: {}, tipo: {}, iconos: {} }; guardar();
    const sel = document.querySelector("#theme"); if (sel) { sel.value = "gris"; sel.dispatchEvent(new Event("change")); }
    pintarTodo(); avisa("Apariencia restablecida");
  });
  const pintarTodo = () => { pintarTemas(); pintarSenal(); pintarPresets(); pintarRoles(); pintarEstudio(); pintarDestinos(); pintarIconos(); pintarAvisos(); };
  pintarTodo();
}
