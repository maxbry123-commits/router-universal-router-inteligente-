// ventana-proyectos.js — "Nuevo proyecto" + ventana Proyectos: cada proyecto con su backend (acción proyecto del harness:
// upsert/list/get + subir con destino proyecto) y su vista de archivos y procesos. Misma memoria que el resto del chat.
import { el, boton, crearVentana, abrirVentana } from "./ventanas-comun.js";
import { crearProyecto, listaProyectos, proyId } from "./objetivos-ancla.js";
const acc = (op, x) => (window.RIU_ACCION ? window.RIU_ACCION("proyecto", { op, ...x }) : Promise.reject(new Error("SIN_ROUTER")));
export function nuevoProyecto(tell, nombre) {
  const n = String(nombre || prompt("Nombre del proyecto nuevo") || "").trim();
  if (!n) return null;
  const real = crearProyecto(n);  // cache UI + upsert remoto con project_id p-<uid>
  if (tell) tell("Proyecto creado: " + real);
  return real;
}
export function montarProyectos(root, { tell }) {
  const { sheet, caja } = crearVentana(root, { id: "ventana-proyectos", titulo: "Proyectos" });
  const cuerpo = el("div", "vn-sec"); caja.append(cuerpo);
  let abierto = null;
  async function pintar() {
    cuerpo.replaceChildren();
    const fila = el("div", "vn-fila");
    fila.append(boton("＋ Nuevo proyecto", "mini on", () => { const n = nuevoProyecto(tell); if (n) { abierto = n; setTimeout(pintar, 400); } }));
    cuerpo.append(fila);
    const l = listaProyectos();
    if (!l.length) cuerpo.append(el("div", "fila-desc", "Aún no hay proyectos."));
    l.forEach((p) => {
      const b = boton((abierto === p.nombre ? "▾ " : "▸ ") + p.nombre, "toggle" + (abierto === p.nombre ? " on" : ""), () => { abierto = abierto === p.nombre ? null : p.nombre; pintar(); });
      b.dataset.proyecto = p.nombre; cuerpo.append(b);
      if (abierto === p.nombre) cuerpo.append(detalle(p));
    });
  }
  function detalle(p) {
    const pid = p.project_id || proyId(p.nombre), d = el("div", "vn-entrada proy-detalle"); d.dataset.pid = pid;
    const arch = el("div", "proy-archivos"), proc = el("div", "proy-procesos");
    arch.append(el("div", "vn-t", "Archivos · cargando…")); proc.append(el("div", "vn-t", "Procesos · cargando…"));
    const inp = el("input"); inp.type = "file"; inp.multiple = true; inp.hidden = true;
    inp.addEventListener("change", async () => {
      for (const f of inp.files) {
        try {
          const buf = new Uint8Array(await f.arrayBuffer()); let bin = ""; for (let i = 0; i < buf.length; i += 32768) bin += String.fromCharCode.apply(null, buf.subarray(i, i + 32768));
          await window.RIU_ACCION("subir", { nombre: f.name, tipo: f.type || "texto", datos_b64: btoa(bin), destino: "proyecto", project_id: pid });
          tell("Subido a «" + p.nombre + "»: " + f.name);
        } catch (e) { tell("No se pudo subir " + f.name + ": " + (e.message || e)); }
      }
      cargar();
    });
    const vincular = boton("Añadir chat actual", "mini", async () => { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (!c) return; try { await acc("link_chat", { project_id: pid, sesion: c.sesion }); c.project_id = pid; if (window.RIU_CHAT.pintar) window.RIU_CHAT.pintar(); tell("Chat añadido a «" + p.nombre + "»: sus procesos aparecen aquí"); cargar(); } catch (e) { tell("No se pudo: " + e.message); } });
    d.append(el("div", "vn-fila"), arch, proc);
    d.firstChild.append(boton("Subir archivo", "mini", () => inp.click()), vincular, boton("Actualizar", "mini", () => cargar()), inp);
    async function cargar() {
      try {
        const r = await acc("get", { project_id: pid });
        if (r && r.error) throw new Error(r.error);
        const a = (r && r.archivos) || [], ps = (r && r.procesos) || [], ch = (r && r.chats) || [];
        arch.replaceChildren(el("div", "vn-t", "Archivos · " + a.length)); a.forEach((n) => arch.append(el("div", "vn-item proy-archivo", "📄 " + n)));
        if (!a.length) arch.append(el("div", "fila-desc", "Sin archivos. Usa «Subir archivo»."));
        proc.replaceChildren(el("div", "vn-t", "Procesos · " + ps.length + " · chats vinculados " + ch.length));
        ps.forEach((x) => proc.append(el("div", "vn-item proy-proceso", (x.estado === "corriendo" ? "▶ " : x.estado === "en cola" ? "… " : "✓ ") + x.estado + " · " + new Date((x.ts || 0) * 1000).toLocaleString() + " · " + (x.texto || x.proceso_id))));
        if (!ps.length) proc.append(el("div", "fila-desc", "Sin procesos. Añade el chat actual y envía un mensaje."));
      } catch (e) { arch.replaceChildren(el("div", "fila-desc", "GAP: " + (e.message || e))); proc.replaceChildren(); }
    }
    cargar(); return d;
  }
  window.RIU_PROYECTOS_ABRIR = (nombre) => { if (nombre) abierto = nombre; pintar(); abrirVentana(root, sheet); };
  try { if (localStorage.getItem("riu_abrir_proyectos")) { localStorage.removeItem("riu_abrir_proyectos"); setTimeout(() => window.RIU_PROYECTOS_ABRIR(), 800); } } catch (e) {}
  return { abrir: window.RIU_PROYECTOS_ABRIR };
}
