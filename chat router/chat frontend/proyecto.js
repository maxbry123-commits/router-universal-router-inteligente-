// proyecto.js — pestaña "Proyecto" del panel Archivos: los proyectos (grupos de lo anclado) creados en el anclaje del chat, de todos los chats,
// con acciones reales: ver, copiar a un workflow o a la constitución, borrar, y crear uno a mano.
import { leer, escribir, KEYS, uid } from "./almacen.js";
import { dameWF } from "./contexto.js";
import { el, boton, etiqueta } from "./ventanas-comun.js";
const CLAVE_PROY = "riu_proy_v1";
const unico = (a) => [...new Set(a)];
export function montarProyecto(root, { tell }) {
  const tabs = root.querySelectorAll("[data-tab]"), pa = root.querySelector("#tab-archivos"), pp = root.querySelector("#tab-proyecto"), lista = root.querySelector("#proyecto-lista");
  if (!pa || !pp || !lista) return;
  const mostrar = (t) => { pa.hidden = t !== "archivos"; pp.hidden = t !== "proyecto"; tabs.forEach((b) => { const on = b.dataset.tab === t; b.classList.toggle("on", on); b.setAttribute("aria-selected", String(on)); }); if (t === "proyecto") pintar(); };
  tabs.forEach((b) => b.addEventListener("click", () => mostrar(b.dataset.tab)));
  const todos = () => { const t = leer(CLAVE_PROY, {}), out = []; Object.keys(t).forEach((ses) => (Array.isArray(t[ses]) ? t[ses] : []).forEach((p, i) => out.push({ ses, i, p }))); return out; };
  function pintar() {
    lista.replaceChildren();
    const nom = el("input", "vn-in"), ta = el("textarea", "vn-ta"); nom.placeholder = "Nombre del proyecto nuevo"; nom.maxLength = 60; nom.setAttribute("aria-label", "Nombre del proyecto"); ta.placeholder = "Enlaces o texto, uno por línea…"; ta.setAttribute("aria-label", "Contenido del proyecto");
    const crear = boton("Crear proyecto", "mini", () => {
      const n = nom.value.trim(), items = ta.value.split(/\n/).map((l) => l.trim()).filter(Boolean).map((l) => (/^https?:\/\//i.test(l) ? "enlace:" + l.split(/\s+/)[0] : "texto:" + l.slice(0, 2000)));
      if (!n || !items.length) { tell("Pon un nombre y al menos un enlace o texto"); return; }
      const t = leer(CLAVE_PROY, {}); t.manual = Array.isArray(t.manual) ? t.manual : []; t.manual.push({ nombre: n, items: unico(items) }); escribir(CLAVE_PROY, t); tell("Proyecto creado: " + n); pintar();
    });
    const nuevo = el("div", "vn-sec"); nuevo.append(el("div", "vn-t", "Proyecto nuevo"), nom, ta, crear); lista.append(nuevo);
    const ps = todos();
    if (!ps.length) lista.append(el("div", "fila-desc", "Aún no hay proyectos. Se crean en la ventana de anclaje (campo «Nombre del proyecto») o aquí arriba."));
    ps.forEach(({ ses, i, p }) => {
      const card = el("div", "vn-entrada"), items = Array.isArray(p.items) ? p.items : [];
      card.append(el("strong", "", (p.nombre || "Proyecto") + " · " + items.length), el("small", "", ses === "manual" ? "creado aquí" : "chat " + String(ses).slice(-6)));
      const det = el("details"); det.append(el("summary", "", "Ver lo anclado")); items.forEach((t) => det.append(el("div", "vn-item", etiqueta(t)))); card.append(det);
      const acc = el("div", "vn-fila"), sel = el("select", "vn-in"); sel.setAttribute("aria-label", "Workflow destino");
      const wfs = dameWF(); wfs.forEach((w) => { const o = el("option", "", w.nombre); o.value = w.id; sel.append(o); }); sel.hidden = !wfs.length;
      if (wfs.length) acc.append(sel, boton("Copiar al workflow", "mini", () => { const d = leer(KEYS.workflows, { lista: [] }), w = d.lista.find((x) => x.id === sel.value); if (!w) return; w.items = unico([...(w.items || []), ...items]); escribir(KEYS.workflows, d); tell("Copiado a «" + w.nombre + "»"); }));
      acc.append(boton("Copiar a la constitución", "mini", () => { const c = Object.assign({ encendida: false, texto: "", oficial: false, items: [] }, leer(KEYS.constitucion, {})); c.items = unico([...(c.items || []), ...items]); escribir(KEYS.constitucion, c); tell("Copiado a la constitución"); }),
        boton("Borrar", "mini rojo", () => { if (!confirm("¿Borrar el proyecto «" + (p.nombre || "") + "»? (lo anclado en el chat no se toca)")) return; const t = leer(CLAVE_PROY, {}); if (Array.isArray(t[ses])) { t[ses].splice(i, 1); escribir(CLAVE_PROY, t); } pintar(); }));
      card.append(acc); lista.append(card);
    });
  }
  mostrar("archivos");
}
