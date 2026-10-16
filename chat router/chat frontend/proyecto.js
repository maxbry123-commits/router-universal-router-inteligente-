// proyecto.js — pestaña "Proyecto" del panel Archivos: los proyectos (grupos de lo anclado) creados en el anclaje del chat, de todos los chats,
// con acciones reales: ver, copiar a un workflow o a la constitución, borrar, y crear uno a mano.
import { leer, escribir, KEYS, uid } from "./almacen.js";
import { dameWF } from "./contexto.js";
import { el, boton, etiqueta } from "./ventanas-comun.js";
const CLAVE_PROY = "riu_proy_v1";
const slugP = (n) => (String(n || "").toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9_-]/g, "").slice(0, 48) || "proyecto");
const remoto = (op, x) => { try { if (window.RIU_ACCION) return window.RIU_ACCION("proyecto", { op, ...x }); } catch (e) {} return Promise.resolve(null); };  // memoria_yaiwes = verdad; riu_proy_v1 = cache de UI
const etiquetaSesion = (s) => {
  if (s === "manual") return "creado aquí"; if (s === "global") return "carpeta de proyecto"; if (s === "constitucion") return "Constitución"; if (s === "agentes") return "Agentes remotos"; if (s === "sandbox") return "Sandbox";
  if (s.startsWith("wf:")) { const w = dameWF().find((x) => x.id === s.slice(3)); return "Workflow " + (w ? w.nombre : s.slice(3)); }
  if (s.startsWith("proyecto:")) return "dentro de " + s.slice(9); return "chat " + String(s).slice(-6);
};
const unico = (a) => [...new Set(a)];
export function montarProyecto(root, { tell }) {
  const tabs = root.querySelectorAll("[data-tab]"), pa = root.querySelector("#tab-archivos"), pp = root.querySelector("#tab-proyecto"), lista = root.querySelector("#proyecto-lista");
  if (!pa || !pp || !lista) return;
  const mostrar = (t) => { pa.hidden = t !== "archivos"; pp.hidden = t !== "proyecto"; tabs.forEach((b) => { const on = b.dataset.tab === t; b.classList.toggle("on", on); b.setAttribute("aria-selected", String(on)); }); if (t === "proyecto") pintar(); };
  tabs.forEach((b) => b.addEventListener("click", () => mostrar(b.dataset.tab)));
  const todos = () => { const t = leer(CLAVE_PROY, {}), out = []; Object.keys(t).forEach((ses) => (Array.isArray(t[ses]) ? t[ses] : []).forEach((p, i) => out.push({ ses, i, p }))); return out; };
  remoto("list").then((r) => {  // fuente de verdad: proyectos del backend (scope project:<id>); el cache local se fusiona conservando project_id REAL
    try {
      if (!r || !Array.isArray(r.proyectos)) return;
      const t = leer(CLAVE_PROY, {}); t.global = Array.isArray(t.global) ? t.global : []; let nuevos = 0;
      r.proyectos.forEach((p) => {
        const n = String(p.nombre || p.project_id || ""), pid = String(p.project_id || "");
        if (!n) return;
        const ex = t.global.find((x) => (pid && x.project_id === pid) || x.nombre.toLowerCase() === n.toLowerCase());
        if (ex) { if (pid && !ex.project_id) { ex.project_id = pid; nuevos++; } }  // hidratar id real tambien en los ya cacheados
        else { t.global.push({ nombre: n, project_id: pid || slugP(n), items: [], on: !!p.encendido, notas: p.notas || "" }); nuevos++; }
      });
      if (nuevos) { escribir(CLAVE_PROY, t); pintar(); }
    } catch (e) {}
  }).catch(() => {});
  function pintar() {
    lista.replaceChildren();
    const nom = el("input", "vn-in"), ta = el("textarea", "vn-ta"); nom.placeholder = "Nombre del proyecto nuevo"; nom.maxLength = 60; nom.setAttribute("aria-label", "Nombre del proyecto"); ta.placeholder = "Enlaces o texto, uno por línea…"; ta.setAttribute("aria-label", "Contenido del proyecto");
    const crear = boton("Crear proyecto", "mini", () => {
      const n = nom.value.trim(), items = ta.value.split(/\n/).map((l) => l.trim()).filter(Boolean).map((l) => (/^https?:\/\//i.test(l) ? "enlace:" + l.split(/\s+/)[0] : "texto:" + l.slice(0, 2000)));
      if (!n || !items.length) { tell("Pon un nombre y al menos un enlace o texto"); return; }
      const pid = "p-" + uid();  // project_id estable, independiente del nombre (renombrar no lo cambia)
      const t = leer(CLAVE_PROY, {}); t.manual = Array.isArray(t.manual) ? t.manual : []; t.manual.push({ nombre: n, project_id: pid, items: unico(items) }); escribir(CLAVE_PROY, t);
      remoto("upsert", { project_id: pid, nombre: n }).then(() => remoto("list")).catch(() => {});
      tell("Proyecto creado: " + n); pintar();
    });
    const nuevo = el("div", "vn-sec"); nuevo.append(el("div", "vn-t", "Proyecto nuevo"), nom, ta, crear); lista.append(nuevo);
    const ps = todos();
    if (!ps.length) lista.append(el("div", "fila-desc", "Aún no hay proyectos. Se crean en la ventana de anclaje (campo «Nombre del proyecto») o aquí arriba."));
    ps.forEach(({ ses, i, p }) => {
      const card = el("div", "vn-entrada"), items = Array.isArray(p.items) ? p.items : [];
      card.append(el("strong", "", (p.nombre || "Proyecto") + " · " + items.length), el("small", "", etiquetaSesion(ses)));
      const det = el("details"); det.append(el("summary", "", "Ver lo anclado")); items.forEach((t) => det.append(el("div", "vn-item", etiqueta(t)))); card.append(det);
      const acc = el("div", "vn-fila"), sel = el("select", "vn-in"); sel.setAttribute("aria-label", "Workflow destino");
      const wfs = dameWF(); wfs.forEach((w) => { const o = el("option", "", w.nombre); o.value = w.id; sel.append(o); }); sel.hidden = !wfs.length;
      if (wfs.length) acc.append(sel, boton("Copiar al workflow", "mini", () => { const d = leer(KEYS.workflows, { lista: [] }), w = d.lista.find((x) => x.id === sel.value); if (!w) return; w.items = unico([...(w.items || []), ...items]); escribir(KEYS.workflows, d); tell("Copiado a «" + w.nombre + "»"); }));
      acc.append(boton("Copiar a la constitución", "mini", () => { const c = Object.assign({ encendida: false, texto: "", oficial: false, items: [] }, leer(KEYS.constitucion, {})); c.items = unico([...(c.items || []), ...items]); escribir(KEYS.constitucion, c); tell("Copiado a la constitución"); }),
        boton("Borrar", "mini rojo", async () => { if (!confirm("¿Borrar el proyecto «" + (p.nombre || "") + "»? (lo anclado en el chat no se toca)")) return;
          const pid = p.project_id || slugP(p.nombre);
          try { const r = await remoto("delete", { project_id: pid }); if (r && r.error) { tell("El backend no confirmó el borrado: " + r.error); return; } } catch (e) { tell("Sin respuesta del backend: no se borra el cache"); return; }
          const t = leer(CLAVE_PROY, {}); if (Array.isArray(t[ses])) { t[ses].splice(i, 1); escribir(CLAVE_PROY, t); } pintar(); }));  // backend primero; el cache solo cae si confirma
      if (ses === "global") { const tg = boton(p.on ? "Encendido" : "Apagado · encender", "toggle" + (p.on ? " on" : ""), () => { const t = leer(CLAVE_PROY, {}), x = (t.global || [])[i]; if (x) { x.on = !x.on; escribir(CLAVE_PROY, t); remoto("upsert", { project_id: x.project_id || slugP(x.nombre), encendido: !!x.on }).catch(() => {}); } pintar(); }); tg.setAttribute("aria-pressed", String(!!p.on)); acc.append(tg); }
      card.append(acc); lista.append(card);
    });
  }
  mostrar("archivos");
}
