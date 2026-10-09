// PUNTO 1 — Nuevo chat aislado.
// "Crear una sesión nueva real, con session_id/chat_id propio." -> panel-chat.js nuevoChat() genera el id (web-<16 hex>)
// y cada llamada al Router lleva esa sesion. Aquí: se muestra el id del chat activo.
// "No comparte historial salvo lo que tú autorices." -> única vía: el botón "Autorizar" de la hoja ⚓ ancla, que copia
// el historial del otro chat (GET /chat/history/{sesion}) como archivo de ESTE chat (acción subir) y lo ancla.
import { node } from "./api.js";

export const b64utf8 = (texto) => {
  const u = new TextEncoder().encode(String(texto));
  let s = "";
  for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192));
  return btoa(s);
};

export function conectarAislado(ctx) {
  const { root, q, api, tell, chats, chat } = ctx;
  const tabs = q("#chat-tabs");
  const etiqueta = node("div", "", "muted chat-id");
  etiqueta.style.fontSize = "11px";
  tabs.after(etiqueta);
  const pintarId = () => {
    const c = chat();
    if (!c) return;
    etiqueta.textContent = "🔒 Chat aislado · id " + c.sesion + (c.padre ? " · hijo de " + c.padre : "");
  };
  new MutationObserver(pintarId).observe(tabs, { childList: true });
  pintarId();

  // ---- autorización explícita para compartir historial entre chats ----
  const caja = q("#sh-ancla .va-caja");
  const zona = node("div", "", "list");
  zona.id = "autorizar-historial";
  caja.append(node("strong", "📋 Compartir historial (solo si lo autorizas)"), zona,
    node("div", "Por defecto cada chat está aislado. Autorizar copia el historial del otro chat como archivo de este chat y lo ancla.", "fila-desc"));
  const pintar = () => {
    zona.replaceChildren();
    const actual = chat();
    const otros = chats.filter((c) => c !== actual);
    if (!otros.length) { zona.append(node("div", "No hay otros chats abiertos", "muted")); return; }
    otros.forEach((c) => {
      const fila = node("div", "", "va-item");
      const nombre = node("span", (c.etiqueta || "💬 " + (chats.indexOf(c) + 1)) + " · " + c.sesion, "fila-nom");
      const b = node("button", "Autorizar", "mini");
      b.type = "button";
      b.title = "Copiar el historial de ese chat a este chat";
      b.addEventListener("click", async () => {
        b.disabled = true;
        try {
          const destino = chat();
          const h = await api(`/chat/history/${encodeURIComponent(c.sesion)}?limit=200`);
          const msgs = h.messages || [];
          if (!msgs.length) { tell("Ese chat no tiene historial en el servidor"); return; }
          const texto = `HISTORIAL AUTORIZADO del chat ${c.sesion} (${h.turns} turnos)\n\n` +
            msgs.map((m) => (m.role === "user" ? "[usuario] " : "[asistente] ") + m.content).join("\n\n");
          const nombreArchivo = "historial-" + c.sesion + ".txt";
          const r = await window.RIU_ACCION("subir", { sesion: destino.sesion, nombre: nombreArchivo, tipo: "text/plain", datos_b64: b64utf8(texto) });
          if (r.error) throw new Error(r.error);
          destino.anclados.add(r.nombre || nombreArchivo);
          ctx.pintarAnclados(); ctx.guardar();
          destino.hist.append(node("div", `📋 Historial de ${c.sesion} autorizado: ${h.turns} turnos anclados a este chat`, "item message meta"));
          tell("Historial autorizado y anclado");
        } catch (error) { tell("GAP historial: " + error.message); }
        finally { b.disabled = false; }
      });
      fila.append(nombre, b);
      zona.append(fila);
    });
  };
  q("#ancla").addEventListener("click", pintar);
  pintar();
  return { pintarId };
}
