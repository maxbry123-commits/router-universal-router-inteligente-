// contexto.js — lógica pura (sin DOM) del contexto que viaja con cada mensaje: constitución sentinela, workflows encendidos,
// agentes remotos y claves compartidas (de las claves solo viaja el NOMBRE de la referencia, nunca el valor).
import { leer, KEYS } from "./almacen.js";
export const dameWF = () => { const v = leer(KEYS.workflows, { lista: [] }); return Array.isArray(v.lista) ? v.lista : []; };
export const dameCon = () => Object.assign({ encendida: false, texto: "", oficial: false, items: [] }, leer(KEYS.constitucion, {}));
export const dameClaves = () => (leer(KEYS.claves, { refs: {} }).refs) || {};
export const dameDestinos = () => Object.assign({ activos: ["chat"], wfSel: [], agentes: [] }, leer(KEYS.destinos, {}));
export const refsCompartidas = (a) => { const r = dameClaves(); return Object.keys(r).filter((k) => r[k] && r[k].comparte && r[k].comparte[a]); };
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
const lineas = (arr) => arr.map((t) => "- " + String(t).slice(0, 400)).join("\n");
export function construirPrefijo(oficial) {
  const partes = [], con = dameCon(), wfs = dameWF().filter((w) => w.encendido), des = dameDestinos();
  if (con.encendida) {
    let t = "[CONSTITUCIÓN SENTINELA · ENCENDIDA]";
    if ((con.texto || "").trim()) t += "\n" + con.texto.trim();
    if (con.oficial && oficial) t += "\nConstitución YAIWES oficial:\n" + String(oficial).slice(0, 8000);
    if ((con.items || []).length) t += "\nAnclado a la constitución:\n" + lineas(con.items);
    const rc = refsCompartidas("constitucion"); if (rc.length) t += "\nClaves disponibles (solo referencia): " + rc.join(", ");
    partes.push(t);
  }
  wfs.forEach((w) => {
    let t = "[WORKFLOW LOOP «" + w.nombre + "» · ENCENDIDO]";
    if ((w.systemPrompt || "").trim()) t += "\nSystem prompt:\n" + w.systemPrompt.trim();
    if ((w.items || []).length) t += "\nAnclado a este workflow:\n" + lineas(w.items);
    const rw = refsCompartidas("workflows"); if (rw.length) t += "\nClaves disponibles (solo referencia): " + rw.join(", ");
    t += "\nPara escribir una instrucción en la ventana de ejecución de este workflow responde con: [[WF:" + w.nombre + "]]instrucción[[/WF]]";
    partes.push(t);
  });
  if (wfs.length && des.agentes.length) partes.push("[AGENTES REMOTOS · código fuente + SDK]\n" + lineas(des.agentes.map((a) => a.url + (a.sdk ? " (con SDK)" : ""))));
  return partes.join("\n\n");
}
export function aplicarAMensaje(msg, oficial) { const p = construirPrefijo(oficial); return p ? p + "\n\n--- MENSAJE DEL DIRECTOR ---\n" + msg : msg; }
export function ampliarAnclados(lista) { const rs = refsCompartidas("chat").map((r) => "secreto:" + r); return [...lista, ...rs.filter((x) => !lista.includes(x))]; }
