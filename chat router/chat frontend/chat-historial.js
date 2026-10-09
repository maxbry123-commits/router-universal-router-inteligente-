// PUNTO 2 — Historial persistente.
// "Guardarlo en backend/SQLite/memoria, no solo en el navegador." -> cada turno ya lo guarda puente_chat en la memoria
// SQLite del Router (scope chat-ui:chat:<sesion>), que se sincroniza al bucket HF.
// "Al recargar, reconstruir la conversación desde almacenamiento." -> al montar el chat se pide
// GET /chat/history/{sesion} para cada chat abierto y se pinta antes de cualquier mensaje nuevo.
import { node } from "./api.js";

export async function cargarHistorial(ctx, c) {
  if (c.historialCargado) return;
  c.historialCargado = true;
  const frag = document.createDocumentFragment();
  try {
    const h = await ctx.api(`/chat/history/${encodeURIComponent(c.sesion)}?limit=200`);
    const msgs = h.messages || [];
    msgs.forEach((m) => frag.append(ctx.burbuja(m.content, m.role === "user" ? "user" : "")));
    if (msgs.length) frag.append(node("div", `🗄 Historial reconstruido desde el almacenamiento del Router: ${h.turns} turno(s) · sesión ${c.sesion}`, "item message meta"));
  } catch (error) {
    frag.append(node("div", "GAP historial del servidor: " + error.message + " (se conserva lo de esta pantalla)", "item message error"));
  }
  c.hist.prepend(frag);  // antes de lo que se haya escrito mientras cargaba
  c.hist.scrollTop = c.hist.scrollHeight;
}

export function conectarHistorial(ctx) {
  ctx.cargarHistorial = (c) => cargarHistorial(ctx, c);
  ctx.chats.forEach((c) => cargarHistorial(ctx, c));
}
