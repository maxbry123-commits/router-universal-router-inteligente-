// contexto.js — lógica pura (sin DOM) del contexto que viaja con cada mensaje: constitución sentinela, workflows encendidos,
// agentes remotos y claves compartidas (de las claves solo viaja el NOMBRE de la referencia, nunca el valor).
import { leer, KEYS } from "./almacen.js";
export const dameWF = () => { const v = leer(KEYS.workflows, { lista: [] }); return Array.isArray(v.lista) ? v.lista : []; };
const K_MIG_CON = "riu_con_off_mig_v1";  // migración única: la Constitución arranca APAGADA para todos (también quien la tenía encendida)
try { if (typeof localStorage !== "undefined" && !localStorage.getItem(K_MIG_CON)) { const c = leer(KEYS.constitucion, null); if (c && c.encendida) { c.encendida = false; localStorage.setItem(KEYS.constitucion, JSON.stringify(c)); } localStorage.setItem(K_MIG_CON, "1"); } } catch (e) {}
export const dameCon = () => Object.assign({ encendida: false, texto: "", oficial: false, items: [] }, leer(KEYS.constitucion, {}));
export const dameClaves = () => (leer(KEYS.claves, { refs: {} }).refs) || {};
export const dameDestinos = () => Object.assign({ activos: ["chat"], wfSel: [], agentes: [] }, leer(KEYS.destinos, {}));
export const dameAg = () => Object.assign({ items: [], notas: "", on: false }, leer(KEYS.agentes, {}));
export const dameSb = () => Object.assign({ items: [], notas: "", on: false }, leer(KEYS.sandbox, {}));
export const dameProyGlobal = () => { const t = leer("riu_proy_v1", {}); return Array.isArray(t.global) ? t.global : []; };
export const refsCompartidas = (a) => { const r = dameClaves(); return Object.keys(r).filter((k) => r[k] && r[k].comparte && r[k].comparte[a]); };
export function parsearBloquesTarea(texto) {
  const out = [], re = /\[\[TAREA:([^\]\n|]{1,80})(?:\|(una|diario|semanal))?(?:\|([01]?\d|2[0-3]):([0-5]\d))?\]\]([\s\S]*?)\[\[\/TAREA\]\]/g;
  let m;
  while ((m = re.exec(String(texto))) !== null) {
    const prompt = m[5].trim();
    if (!prompt) continue;
    out.push({ titulo: m[1].trim(), cada: m[2] || "diario", hora: (m[3] ? String(m[3]).padStart(2, "0") : "08") + ":" + (m[4] || "00"), prompt });
  }
  return out;
}
export function parsearBloquesComando(texto) {
  const out = [], re = /\[\[COMANDO:([a-z0-9-]{1,24})\]\]([\s\S]*?)\[\[\/COMANDO\]\]/gi;
  let m;
  while ((m = re.exec(String(texto))) !== null) {
    const cuerpo = m[2].trim();
    if (cuerpo) out.push({ nombre: m[1].toLowerCase(), texto: cuerpo.slice(0, 500) });
  }
  return out;
}
export function parsearBloquesMemoria(texto) {
  const out = [], re = /\[\[MEMORIA\]\]([\s\S]*?)\[\[\/MEMORIA\]\]/g;
  let m;
  while ((m = re.exec(String(texto))) !== null) { const t = m[1].trim(); if (t) out.push(t.slice(0, 4000)); }
  return out;
}
export function parsearBloquesRevision(texto) {
  const out = [], re = /\[\[REVISION:(error|seguridad|aviso|nota)\]\]([\s\S]*?)\[\[\/REVISION\]\]/gi;
  let m;
  while ((m = re.exec(String(texto))) !== null) { const t = m[2].trim(); if (t) out.push({ tipo: m[1].toLowerCase(), texto: t.slice(0, 240) }); }
  return out;
}
export function parsearModo(texto) {
  const m = /\[\[MODO:(preguntar|agente)\]\]/i.exec(String(texto));
  return m ? m[1].toLowerCase() : "";
}
function bloqueSesion(tools) {
  let v = { memoria: true, nota: "", tope: 800, revisiones: [] };
  try { const g = leer("riu_sesion_v1", {}); v = { memoria: g.memoria !== false, nota: String(g.nota || ""), tope: Math.min(4000, Math.max(200, Number(g.tope) || 800)), revisiones: Array.isArray(g.revisiones) ? g.revisiones : [] }; } catch (e) {}
  const partes = [];
  if (v.memoria && v.nota.trim()) partes.push("[MEMORIA]\n" + v.nota.trim());
  if (v.revisiones.length) partes.push("[REVISION]\n" + v.revisiones.slice(0, 12).map((r) => "- " + r.tipo + ": " + String(r.texto || "").slice(0, 240)).join("\n"));
  let s = partes.join("\n").slice(0, v.tope);
  if (tools) s = (s ? s + "\n" : "") + "Memoria: [[MEMORIA]]texto[[/MEMORIA]]. Revisión: [[REVISION:error|seguridad|aviso|nota]]texto[[/REVISION]]. Modo: [[MODO:preguntar]] o [[MODO:agente]].";
  return s;
}
const IDIOMAS = { es: "español", en: "inglés", pt: "portugués" };
export function parsearIdioma(texto) {
  const m = /\[\[IDIOMA:(es|en|pt)\]\]/i.exec(String(texto));
  return m ? m[1].toLowerCase() : "";
}
export function parsearBloquesRegla(texto) {
  const out = [], re = /\[\[REGLA\]\]([\s\S]*?)\[\[\/REGLA\]\]/g;
  let m;
  while ((m = re.exec(String(texto))) !== null) { const t = m[1].trim(); if (t) out.push(t.slice(0, 240)); }
  return out;
}
function bloqueReglas(tools) {
  let v = { idioma: "", reglas: [], topeMsg: 0 };
  try { v = Object.assign(v, leer("riu_reglas_v1", {})); } catch (e) {}
  const partes = [];
  if (IDIOMAS[v.idioma]) partes.push("[IDIOMA] Responde en " + IDIOMAS[v.idioma] + ".");
  const on = (Array.isArray(v.reglas) ? v.reglas : []).filter((r) => r && r.on !== false && r.texto).slice(0, 8);
  if (on.length) partes.push("[REGLAS]\n" + on.map((r) => "- " + String(r.texto).slice(0, 240)).join("\n"));
  if (tools) partes.push("Idioma: [[IDIOMA:es]], [[IDIOMA:en]] o [[IDIOMA:pt]]. Regla: [[REGLA]]texto[[/REGLA]].");
  return partes.join("\n").slice(0, 1200);
}
export function parsearBloquesWF(texto) {  // la IA escribe en la ventana de ejecución con: [[WF:nombre]]instrucción[[/WF]]
  const out = [], re = /\[\[WF:([^\]\n]{1,60})\]\]([\s\S]*?)\[\[\/WF\]\]/g; let m;
  while ((m = re.exec(String(texto))) !== null) { const t = m[2].trim(); if (t) out.push({ ref: m[1].trim(), texto: t }); }
  return out;
}
export function buscarWF(ref, lista) { const r = String(ref).trim().toLowerCase(); return lista.find((w) => w.id.toLowerCase() === r || w.nombre.toLowerCase() === r) || null; }
export function parsearSlashWF(msg, lista) {  // "/wf <nombre> <instrucción>" desde la caja del chat
  const m = /^\/wf(?:\s+([\s\S]*))?$/i.exec(String(msg).trim()); if (!m) return null;
  const resto = (m[1] || "").trim(); if (!resto) return { wf: null, texto: "" };
  for (const w of [...lista].sort((a, b) => b.nombre.length - a.nombre.length)) {
    const n = w.nombre.toLowerCase(), r = resto.toLowerCase();
    if (r.startsWith(n) && (r.length === n.length || /\s/.test(r[n.length]))) return { wf: w, texto: resto.slice(n.length).trim() };
  }
  return { wf: null, texto: resto };
}
export const K_PIN = "riu_pin_anclas_v1", K_MUTE = "riu_mute_anclas_v1", K_ALIAS = "riu_alias_anclas_v1";
const sinMute = (clave, arr) => { const m = leer(K_MUTE, {})[clave]; return Array.isArray(m) ? (arr || []).filter((t) => !m.includes(t)) : (arr || []); };
const lineas = (arr) => arr.map((t) => "- " + String(t).slice(0, 400)).join("\n");
export function construirPrefijo(oficial) {
  const partes = [], wfs = dameWF().filter((w) => w.encendido);
  // la Constitucion ya NO viaja como texto del mensaje: va estructurada (gobernanza + constitucion) y el Harness carga la oficial
  wfs.forEach((w) => {
    let t = "[WORKFLOW LOOP «" + w.nombre + "» · ENCENDIDO]";
    if ((w.systemPrompt || "").trim()) t += "\nSystem prompt:\n" + w.systemPrompt.trim();
    if (sinMute("wf:" + w.id, w.items).length) t += "\nAnclado a este workflow:\n" + lineas(sinMute("wf:" + w.id, w.items));
    const rw = refsCompartidas("workflows"); if (rw.length) t += "\nClaves disponibles (solo referencia): " + rw.join(", ");
    t += "\nPara escribir una instrucción en la ventana de ejecución de este workflow responde con: [[WF:" + w.nombre + "]]instrucción[[/WF]]";
    partes.push(t);
  });
  const urlDe = (t) => String(t).replace(/^(enlace|raiz):/, "");
  const ag = dameAg(); if (ag.on && ((ag.items || []).length || (ag.notas || "").trim())) partes.push("[AGENTES REMOTOS · código fuente + SDK]\n" + ((ag.notas || "").trim() ? ag.notas.trim() + "\n" : "") + lineas(sinMute("agentes", ag.items).map(urlDe)));
  const sb = dameSb(); if (sb.on && ((sb.items || []).length || (sb.notas || "").trim())) partes.push("[SANDBOX ANCLADO]\n" + ((sb.notas || "").trim() ? sb.notas.trim() + "\n" : "") + lineas(sinMute("sandbox", sb.items)));
  dameProyGlobal().filter((p) => p.on).forEach((p) => partes.push("[PROYECTO «" + p.nombre + "»]\n" + ((p.notas || "").trim() ? p.notas.trim() + "\n" : "") + lineas(sinMute("proyecto:" + p.nombre, p.items))));
  try {
    const f = typeof window !== "undefined" ? (window.RIU_CHAT_TOOL_FLAGS || {}) : {};
    if (f.tools || f.llm_tool || f.agente_tool) {
      const ts = ((leer("riu_tareas_v1", { tareas: [] }).tareas) || []).filter((t) => t && t.on).slice(0, 6);
      let s = "[TAREAS] Crea una con [[TAREA:titulo|diario|08:00]]prompt[[/TAREA]]. cada: una, diario o semanal.";
      if (ts.length) s += "\n" + ts.map((t) => "- " + String(t.titulo || "").slice(0, 80) + " · " + t.cada + " " + t.hora).join("\n");
      const cs = (leer("riu_comandos_v1", []) || []).filter((c) => c && c.nombre).slice(0, 6);
      s += "\n[COMANDOS] Crea uno con [[COMANDO:nombre]]texto[[/COMANDO]]. El usuario lo llama con /nombre.";
      if (cs.length) s += "\n" + cs.map((c) => "- /" + c.nombre + " · " + String(c.texto || "").slice(0, 80)).join("\n");
      const ses = bloqueSesion(true);
      if (ses) s += "\n" + ses;
      partes.push(s);
    } else {
      const ses = bloqueSesion(false);
      if (ses) partes.push(ses);
    }
    const rg = bloqueReglas(!!(f.tools || f.llm_tool || f.agente_tool));
    if (rg) partes.push(rg);
  } catch (e) {}
  return partes.join("\n\n");
}
export function aplicarAMensaje(msg, oficial) { const p = construirPrefijo(oficial); return p ? p + "\n\n--- MENSAJE DEL DIRECTOR ---\n" + msg : msg; }
const nombresConst = (con) => sinMute("constitucion", con.items || []).map((t) => String(t).replace(/^archivo:/, "").trim()).filter((n) => !/^(enlace|raiz|secreto|constitucion):/.test(n) && /^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$/.test(n));
export function datosGobernanza() {  // Constitucion encendida -> campos estructurados para el Harness (nunca el JSON oficial: lo carga el Harness)
  const con = dameCon(); if (!con.encendida) return null;
  return { gobernanza: { enabled: true }, constitucion: { texto: String(con.texto || "").trim(), anclados: nombresConst(con) } };
}
export function ampliarAnclados(lista) {
  const c = typeof window !== "undefined" && window.RIU_CHAT ? window.RIU_CHAT.chat() : null; if (c && c.sesion) lista = sinMute(c.sesion, lista);
  const rs = refsCompartidas("chat").map((r) => "secreto:" + r);
  const con = dameCon(), cs = con.encendida ? nombresConst(con).map((n) => "constitucion:" + n) : [];  // archivos de la ventana Constitucion = fuentes constitucionales directas
  // Solo proyectos ENCEDIDOS; una asociacion almacenada con ON=false NO es ancla activa.
  const pActivas = dameProyGlobal()
    .filter(p => p.on === true && p.project_id)
    .flatMap(p => (p.items || []).map(n => 'proyecto:' + p.project_id + ':' + n));
  // El servidor acepta la lista final como snapshot del turno; no inyecta todo el almacen.
  return [...new Set([...lista, ...rs, ...cs, ...pActivas])];
}
