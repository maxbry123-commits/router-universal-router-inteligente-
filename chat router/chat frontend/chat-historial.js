// PUNTO 2 — Historial persistente.
// "Guardarlo en backend/SQLite/memoria, no solo en el navegador." -> cada turno ya lo guarda puente_chat en la memoria
// SQLite del Router (scope chat-ui:chat:<sesion>), que se sincroniza al bucket HF.
// "Al recargar, reconstruir la conversación desde almacenamiento." -> al montar el chat se pide
// GET /chat/history/{sesion} para cada chat abierto y se pinta antes de cualquier mensaje nuevo.
// También se reconstruye desde GET /chat/files/{sesion} lo que no es turno del chat (revisión A-3/B-1):
//   orquestador-obj-*.json -> orden + tarjeta de resultados (por ts_inicio), resultado-*.md -> burbuja ↩,
//   historial-*.txt -> aviso "Historial autorizado". Todo en orden de ts, como se vio antes de recargar.
import { node } from "./api.js";
import { textoTarjeta } from "./chat-orquestador.js";

const meta = (texto) => node("div", texto, "item message meta");
const hasta = (msgs, ts) => msgs.filter((m) => (m.ts || 0) <= ts + 1);

async function entradasDeArchivos(ctx, c) {
  const files = (await ctx.api(`/chat/files/${encodeURIComponent(c.sesion)}`)).files || [];
  const lista = await Promise.all(files.map(async (f) => {
    let m;
    if (/^orquestador-obj-.*\.json$/.test(f.nombre)) {
      const st = await ctx.api(`/chat/files/${encodeURIComponent(c.sesion)}/${f.file_id}`);
      if (!st || !st.objective_id || !Array.isArray(st.agentes)) return null;
      const orden = typeof st.input === "string" ? st.input : `(orden de ${st.objective_id}: ${st.input_bytes} bytes · sha256 ${st.input_block_sha256})`;
      return { ts: (Date.parse(st.ts_inicio) / 1000) || f.ts, tipo: "orq",
        n: [ctx.burbuja(orden, "user"), ctx.burbuja(textoTarjeta(st)), meta("🗂 State JSON y bitácora guardados en el Router: " + f.nombre)] };
    }
    if ((m = /^resultado-(.+)-(\d+)\.md$/.exec(f.nombre))) {
      const hija = `${c.sesion}:ag:${m[1]}:${m[2]}`;
      const d = await ctx.api(`/chat/child/${encodeURIComponent(hija)}`);
      const ult = hasta((d.history || {}).messages || [], f.ts).reverse().find((x) => x.role === "assistant");
      if (!ult) return null;
      const texto = `RESULTADO del agente ${d.agente} (chat hijo ${hija})\nINPUT_BLOCK sha256 ${d.input_block_sha256}\n\n${ult.content}`;
      return { ts: f.ts, tipo: "res", n: [ctx.burbuja("↩ " + texto), meta("📎 Anclado al chat padre como " + f.nombre + " (archivo del Router)")] };
    }
    if ((m = /^historial-(.+)\.txt$/.exec(f.nombre))) {
      const h = await ctx.api(`/chat/history/${encodeURIComponent(m[1])}?limit=200`);
      const turnos = hasta(h.messages || [], f.ts).filter((x) => x.role === "user").length;
      return { ts: f.ts, tipo: "aut", n: [meta(`📋 Historial de ${m[1]} autorizado: ${turnos} turnos anclados a este chat`)] };
    }
    return null;
  }).map((p) => p.catch(() => null)));
  return lista.filter(Boolean);
}

export async function cargarHistorial(ctx, c) {
  if (c.historialCargado) return;
  c.historialCargado = true;
  const frag = document.createDocumentFragment();
  try {
    const [h, extra] = await Promise.all([
      ctx.api(`/chat/history/${encodeURIComponent(c.sesion)}?limit=200`),
      entradasDeArchivos(ctx, c).catch((e) => { frag.append(node("div", "GAP archivos del historial: " + e.message, "item message error")); return []; }),
    ]);
    const msgs = h.messages || [];
    const todo = msgs.map((m, i) => ({ ts: m.ts || 0, i, n: [ctx.burbuja(m.content, m.role === "user" ? "user" : "")] }))
      .concat(extra.map((e, j) => ({ ...e, i: msgs.length + j })));
    todo.sort((a, b) => a.ts - b.ts || a.i - b.i).forEach((e) => frag.append(...e.n));
    if (todo.length) {
      const cuenta = (t) => extra.filter((e) => e.tipo === t).length;
      frag.append(meta(`🗄 Historial reconstruido desde el almacenamiento del Router: ${h.turns} turno(s), ${cuenta("orq")} orden(es) del orquestador, ${cuenta("res")} resultado(s) ↩, ${cuenta("aut")} historial(es) autorizado(s) · sesión ${c.sesion}`));
    }
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
