// objetivos-ancla.js — a qué se ancla: el chat u otro objetivo (constitución, workflow, agentes remotos, proyecto, sandbox).
// La ventana de anclaje es UNA sola; solo cambia el objetivo. Cada objetivo se comporta como un chat: { sesion, anclados (Set que se guarda solo), instrucciones }.
// Los archivos son compartidos: viven en la carpeta de archivos del chat y cualquier objetivo puede anclarlos.
import { leer, escribir, KEYS, uid } from "./almacen.js";
export const OBJETIVOS = [["chat", "Chat"], ["constitucion", "Constitución"], ["workflows", "Workflows"], ["agentes", "Agentes remotos"], ["proyecto", "Proyecto"], ["sandbox", "Sandbox"]];
export class SetGuardable extends Set {
  constructor(items, alCambiar) { super(items || []); this._cb = alCambiar; }
  add(v) { const ya = super.has(v); super.add(v); if (!ya && this._cb) this._cb(this); return this; }
  delete(v) { const r = super.delete(v); if (r && this._cb) this._cb(this); return r; }
  clear() { super.clear(); if (this._cb) this._cb(this); }
}
const KP = "riu_proy_v1", arr = (v) => (Array.isArray(v) ? v : []);
export const slugProy = (nombre) => (String(nombre || "").toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9_-]/g, "").slice(0, 48) || "proyecto");
export const proyId = (nombre) => { const p = listaProyectos().find((x) => x.nombre === nombre); return (p && p.project_id) || slugProy(nombre); };  // id real guardado; compat: proyectos viejos solo tenian slug
const upsertRemoto = (nombre, pid, extra) => { try { if (window.RIU_ACCION) window.RIU_ACCION("proyecto", { op: "upsert", project_id: pid || slugProy(nombre), nombre, ...(extra || {}) }).catch(() => {}); } catch (e) {} };  // un solo upsert (dos en paralelo pisaban el nombre)
const upsertMeta = (pid, campos) => { try { if (window.RIU_ACCION && pid) window.RIU_ACCION("proyecto", { op: "upsert", project_id: pid, ...campos }).catch(() => {}); } catch (e) {} };  // MERGE backend: solo campos modificados
const conGet = () => Object.assign({ encendida: false, texto: "", oficial: false, items: [] }, leer(KEYS.constitucion, {}));
const wfStore = () => { const v = leer(KEYS.workflows, { lista: [], sel: null }); if (!Array.isArray(v.lista)) v.lista = []; return v; };
const simple = (k) => Object.assign({ items: [], notas: "", on: false }, leer(k, {}));
export const listaWF = () => wfStore().lista;
export const listaProyectos = () => {  // compat: proyectos viejos sin project_id reciben el slug (el mismo id que ya usaba el backend); se guarda una sola vez
  const t = leer(KP, {}), l = arr(t.global); let cambio = false;
  l.forEach((p) => { if (p && !p.project_id) { p.project_id = slugProy(p.nombre); cambio = true; } });
  if (cambio) { t.global = l; escribir(KP, t); }
  return l;
};
export const buscarProyecto = (ref) => listaProyectos().find((x) => x.project_id === ref) || listaProyectos().find((x) => x.nombre === ref) || null;  // por project_id (nuevo) o por nombre (viejo)
export function crearProyecto(nombre) {
  const n = String(nombre || "").trim().slice(0, 60); if (!n) return null;
  const t = leer(KP, {}); t.global = arr(t.global);
  if (!t.global.some((p) => p.nombre.toLowerCase() === n.toLowerCase())) { const pid = "p-" + uid(); const fecha = new Date().toISOString(); t.global.push({ nombre: n, project_id: pid, fecha, items: [], on: false, notas: "" }); escribir(KP, t); upsertRemoto(n, pid, { fecha }); }  // project_id p-<uid> independiente del nombre
  return (t.global.find((p) => p.nombre.toLowerCase() === n.toLowerCase()) || {}).nombre || n;
}
export function nuevoProyectoPrompt(tell) {  // '+ Nuevo proyecto' (lo usan el panel clásico y las vistas A/B/C): pide nombre, crea (id+fecha) y devuelve el registro
  const n = (window.prompt("Nombre del nuevo proyecto") || "").trim(); if (!n) return null;
  const ya = listaProyectos().some((p) => p.nombre.toLowerCase() === n.toLowerCase()), p = buscarProyecto(crearProyecto(n));
  if (tell) tell(p ? (ya ? "Ya existía: " : "Proyecto creado: ") + p.nombre : "No se pudo crear");
  return p;
}
export function crearObjetivo(tipo, id) {
  if (tipo === "constitucion") {
    return { tipo, nombre: "Constitución", sesion: "constitucion", anclados: new SetGuardable(conGet().items, (s) => { const c = conGet(); c.items = [...s]; escribir(KEYS.constitucion, c); }),
      get instrucciones() { return conGet().texto || ""; }, set instrucciones(v) { const c = conGet(); c.texto = String(v).slice(0, 12000); escribir(KEYS.constitucion, c); },
      get encendido() { return !!conGet().encendida; }, set encendido(v) { const c = conGet(); c.encendida = !!v; escribir(KEYS.constitucion, c); } };
  }
  if (tipo === "workflows") {
    const w0 = wfStore().lista.find((x) => x.id === id); if (!w0) return null;
    const mod = (fn) => { const d = wfStore(), x = d.lista.find((y) => y.id === id); if (x) { fn(x); escribir(KEYS.workflows, d); } };
    return { tipo, id, nombre: w0.nombre, sesion: "wf:" + id, anclados: new SetGuardable(w0.items, (s) => mod((x) => { x.items = [...s]; })),
      get instrucciones() { const x = wfStore().lista.find((y) => y.id === id); return x ? x.systemPrompt || "" : ""; }, set instrucciones(v) { mod((x) => { x.systemPrompt = String(v).slice(0, 8000); }); },
      get encendido() { const x = wfStore().lista.find((y) => y.id === id); return !!(x && x.encendido); }, set encendido(v) { mod((x) => { x.encendido = !!v; }); } };
  }
  if (tipo === "agentes" || tipo === "sandbox") {
    const k = tipo === "agentes" ? KEYS.agentes : KEYS.sandbox, mod = (fn) => { const x = simple(k); fn(x); escribir(k, x); };
    return { tipo, nombre: tipo === "agentes" ? "Agentes remotos" : "Sandbox", sesion: tipo, anclados: new SetGuardable(simple(k).items, (s) => mod((x) => { x.items = [...s]; })),
      get instrucciones() { return simple(k).notas || ""; }, set instrucciones(v) { mod((x) => { x.notas = String(v).slice(0, 8000); }); },
      get encendido() { return !!simple(k).on; }, set encendido(v) { mod((x) => { x.on = !!v; }); } };
  }
  if (tipo === "proyecto") {
    const p0 = buscarProyecto(id); if (!p0) return null; id = p0.nombre;  // acepta project_id o nombre; internamente sigue por nombre (sesion/claves sin cambios)
    const mod = (fn) => { const t = leer(KP, {}); t.global = arr(t.global); const x = t.global.find((y) => y.nombre === id); if (x) { fn(x); escribir(KP, t); } };
    const dame = () => listaProyectos().find((y) => y.nombre === id) || {};
    return { tipo, id, nombre: "Proyecto «" + id + "»", sesion: "proyecto:" + id, project_id: p0.project_id || null,
      anclados: new SetGuardable(p0.items, (s) => { mod((x) => { x.items = [...s]; }); upsertMeta(dame().project_id, { anclas: [...s] }); }),
      get instrucciones() { return dame().notas || ""; }, set instrucciones(v) { mod((x) => { x.notas = String(v).slice(0, 8000); }); upsertMeta(dame().project_id, { notas: String(v).slice(0, 8000) }); },
      get encendido() { return !!dame().on; }, set encendido(v) { mod((x) => { x.on = !!v; }); upsertMeta(dame().project_id, { encendido: !!v }); } };
  }
  return null;
}
