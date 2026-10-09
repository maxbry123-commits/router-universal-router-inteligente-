// PUNTO 4 — Archivos persistentes.
// "Los archivos subidos deben quedar asociados a chat_id/session_id." -> la acción subir ya lleva la sesion del chat.
// "Al refrescar, el frontend vuelve a pedir la lista al backend." -> al montar (y al cambiar de chat o anclar) se pide
// GET /chat/files/{sesion}.
// "Nada debe depender solo del estado JS de la página." -> los archivos anclados que el backend ya no tiene se quitan.
// Los controles existentes (botón 🗂 y su ventana) quedan exactamente como en main.
import { node } from "./api.js";

const esArchivo = (a) => !a.startsWith("handoff:") && !a.startsWith("enlace:");

export async function pedirArchivos(ctx, c) {
  const r = await ctx.api(`/chat/files/${encodeURIComponent(c.sesion)}`);
  c.archivosServidor = (r.files || []).map((f) => f.nombre);
  const fantasmas = [...c.anclados].filter((a) => esArchivo(a) && !c.archivosServidor.includes(a));
  if (fantasmas.length) {
    fantasmas.forEach((a) => c.anclados.delete(a));
    c.hist.append(node("div", "🗂 Quitado del ancla (el Router no lo tiene en este chat): " + fantasmas.join(", "), "item message meta"));
    ctx.guardar();
  }
  return c.archivosServidor;
}

export function conectarArchivos(ctx) {
  const { q, chats, chat } = ctx;
  const refrescar = async (c) => {
    try { await pedirArchivos(ctx, c); }
    catch (error) { c.archivosServidor = null; ctx.tell("GAP archivos del servidor: " + error.message); }
    if (c === chat()) ctx.pintarAnclados();
  };
  ctx.refrescarArchivos = refrescar;
  chats.forEach(refrescar);
  let ultimo = null;
  new MutationObserver(() => { if (chat() !== ultimo) { ultimo = chat(); refrescar(ultimo); } }).observe(q("#chat-tabs"), { childList: true });
  // tras subir/anclar un archivo (panel-chat repinta #anclados) se vuelve a pedir la lista al backend
  let pendiente = null;
  new MutationObserver(() => { clearTimeout(pendiente); pendiente = setTimeout(() => { const c = chat(); if ([...c.anclados].some((a) => esArchivo(a) && !(c.archivosServidor || []).includes(a))) refrescar(c); }, 400); })
    .observe(q("#anclados"), { childList: true });
}
