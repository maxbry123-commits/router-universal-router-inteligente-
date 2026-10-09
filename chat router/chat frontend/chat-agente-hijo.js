// PUNTO 5 — Agente anclado → nueva sección de chat.
// "Seleccionas agente." -> hoja 🤖 agente con los agentes reales de GET /chat/agents.
// "Se crea una conversación hija." -> POST /chat/children/{sesion} y una pestaña hija nueva (sesion <padre>:ag:<agente>:<n>).
// "Se carga su ficha + DSL/DAG/schema." -> el Router guarda ficha + DAG riu.dag/v1; se leen con GET /chat/child/{hija}.
// "Recibe el INPUT_BLOCK VERBATIM." -> el texto se envía sin recortar y se compara su sha256 con el que guardó el Router.
// "Ejecuta con su memoria persistente independiente." -> el turno va por puente_chat con la sesion hija (scope propio).
// "Puede devolver resultado al chat padre." -> botón ↩ en el chat hijo: sube el resultado como archivo del padre y lo ancla.
import { node } from "./api.js";
import { b64utf8 } from "./chat-aislado.js";

export const sha256 = async (t) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)))]
  .map((x) => x.toString(16).padStart(2, "0")).join("");

export function dagHijo(agente, objetivo, instrucciones) {
  return { schema: "riu.dag/v1", id: objetivo, nodes: [{ id: "n1", agent: agente, route: { group: "default" },
    instructions: instrucciones || "Ejecuta el INPUT_BLOCK literal con tu ficha.", needs: [] }] };
}

// abre la pestaña de un hijo ya creado en el Router y pinta su ficha + DAG + verificación del INPUT_BLOCK
export async function abrirHijo(ctx, padre, hija, etiqueta, inputEnviado) {
  if (ctx.chats.length >= ctx.MAX_CHAT) throw new Error("Máximo " + ctx.MAX_CHAT + " chats abiertos: cierra uno o recarga");
  const c = ctx.nuevoChat({ sesion: hija, ficha: padre.ficha, padre: padre.sesion, etiqueta, anclados: [] });
  c.historialCargado = inputEnviado !== undefined;
  const d = await ctx.api(`/chat/child/${encodeURIComponent(hija)}`);
  const f = d.ficha || {};
  let ver = "";
  if (inputEnviado !== undefined) {
    const local = await sha256(inputEnviado);
    ver = local === d.input_block_sha256 && d.input_block === inputEnviado ? "✓ INPUT_BLOCK idéntico al enviado (sha256 " + local.slice(0, 16) + "…)" : "✗ INPUT_BLOCK DISTINTO al enviado";
  }
  if (inputEnviado === undefined) await ctx.cargarHistorial(c);
  c.hist.prepend(node("div", `🤖 CHAT HIJO ${hija}\npadre: ${d.padre} · memoria propia\nFICHA: ${f.id} · ${f.name || ""} · ${f.role || ""}\nPROMPT: ${f.system_prompt || ""}\n` +
    `DSL/DAG: ${(d.dag || {}).schema} id ${(d.dag || {}).id} · nodos ${((d.dag || {}).nodes || []).map((n) => n.id + "→" + n.agent).join(", ")}\n` +
    `INPUT_BLOCK (${d.input_block_bytes} bytes):\n${d.input_block}\n${ver}`, "item message meta"));
  return { c, d, ok: ver.startsWith("✓") };
}

export async function ejecutarEnHijo(ctx, c, texto) {
  if (String(c.ficha || "").startsWith("hf-")) throw new Error("El chat hijo no enciende GPU de pago (hf-*): elige un modelo API en la píldora del chat padre");
  c.hist.append(ctx.burbuja(texto, "user"));
  const pending = node("div", "Pensando…", "item message pending");
  c.hist.append(pending);
  c.ocupado = true; ctx.pintarTabs();
  try {
    const r = await window.RIU_HARNESS({ model: c.ficha, message: texto, max_tokens: 1024, sesion: c.sesion, anclados: [] });
    if (r.job_id) { window.__riuJob = r.job_id; const ap = ctx.q("#apagar-respaldo"); if (ap) ap.hidden = false; }  // por si acaso: botón de apagar visible
    c.hist.append(ctx.burbuja(r.reply || "Sin respuesta"));
    return r;
  } catch (error) {
    c.hist.append(node("div", "GAP: " + error.message, "item message error"));
    throw error;
  } finally { pending.remove(); c.ocupado = false; ctx.pintarTabs(); c.hist.scrollTop = c.hist.scrollHeight; }
}

export async function devolverAlPadre(ctx, c) {
  const padre = ctx.chats.find((x) => x.sesion === c.padre);
  const d = await ctx.api(`/chat/child/${encodeURIComponent(c.sesion)}`);
  const ult = [...((d.history || {}).messages || [])].reverse().find((m) => m.role === "assistant");
  if (!ult) throw new Error("El chat hijo aún no tiene resultado en el Router");
  const nombre = "resultado-" + d.agente + "-" + d.n + ".md";
  const texto = `RESULTADO del agente ${d.agente} (chat hijo ${c.sesion})\nINPUT_BLOCK sha256 ${d.input_block_sha256}\n\n${ult.content}`;
  const r = await window.RIU_ACCION("subir", { sesion: c.padre, nombre, tipo: "text/markdown", datos_b64: b64utf8(texto) });
  if (r.error) throw new Error(r.error);
  if (padre) {
    padre.anclados.add(r.nombre || nombre);
    padre.hist.append(ctx.burbuja("↩ " + texto));
    padre.hist.append(node("div", "📎 Anclado al chat padre como " + (r.nombre || nombre) + " (archivo del Router)", "item message meta"));
    ctx.guardar();
  }
  return nombre;
}

export function conectarAgenteHijo(ctx) {
  const { q, api, tell, chat } = ctx;
  let agentes = [];
  const lista = q("#ag-lista"), fichaEl = q("#ag-ficha"), hijosEl = q("#ag-hijos");
  const pintarFicha = () => { const a = agentes.find((x) => x.id === lista.value); fichaEl.textContent = a ? `${a.id} · ${a.role}\n${a.system_prompt}` : ""; };
  lista.addEventListener("change", pintarFicha);
  const pintarHijos = async () => {
    hijosEl.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await api(`/chat/children/${encodeURIComponent(chat().sesion)}`);
      hijosEl.replaceChildren();
      (r.children || []).forEach((h) => {
        const abierto = ctx.chats.some((x) => x.sesion === h.sesion_hija);
        hijosEl.append(Object.assign(node("button", "", "fila"), { type: "button", disabled: abierto, onclick: async () => {
          try { await abrirHijo(ctx, chat(), h.sesion_hija, "↳ " + h.agente); q("#sh-agente").hidden = true; } catch (e) { tell(e.message); }
        } }));
        hijosEl.lastChild.append(node("span", "↳ " + h.agente + " #" + h.n + " · " + h.sesion_hija + (abierto ? " (abierto)" : ""), "fila-nom"));
      });
      if (!(r.children || []).length) hijosEl.append(node("div", "Este chat no tiene chats hijos", "muted"));
    } catch (e) { hijosEl.replaceChildren(node("div", "GAP " + e.message, "muted")); }
  };
  q("#agente-hijo").addEventListener("click", async () => {
    if (!q("#ag-input").value) q("#ag-input").value = q("#message").value;
    if (!agentes.length) {
      try { agentes = (await api("/chat/agents")).agents || []; } catch (e) { tell(e.message); }
      lista.replaceChildren(...agentes.map((a) => Object.assign(node("option", a.name + " — " + a.role), { value: a.id })));
      pintarFicha();
    }
    pintarHijos();
  });
  q("#ag-abrir").addEventListener("click", async (ev) => {
    const boton = ev.currentTarget, padre = chat(), agente = lista.value, input = q("#ag-input").value;
    if (padre.padre) { tell("Abre el agente desde el chat padre, no desde un chat hijo"); return; }
    if (!agente || !input.trim()) { tell("Elige un agente y escribe el INPUT_BLOCK"); return; }
    if (String(padre.ficha || "").startsWith("hf-")) { tell("El chat hijo no enciende GPU de pago (hf-*): elige un modelo API en la píldora"); return; }
    boton.disabled = true;
    try {
      const dag = dagHijo(agente, "hijo-" + Date.now());
      const r = await api(`/chat/children/${encodeURIComponent(padre.sesion)}`, { method: "POST", body: { agente, dag, input_block: input } });
      q("#sh-agente").hidden = true;
      q("#ag-input").value = "";
      const { c } = await abrirHijo(ctx, padre, r.sesion_hija, "↳ " + agente, input);
      await ejecutarEnHijo(ctx, c, input);
    } catch (e) { tell("GAP agente: " + e.message); }
    finally { boton.disabled = false; }
  });
  // ↩ devolver: solo visible en un chat hijo
  const dev = Object.assign(node("button", "↩", "secondary"), { type: "button", id: "btn-devolver", title: "Devolver el último resultado de este chat hijo al chat padre" });
  q("#btn-detener").after(dev);
  const vis = () => { dev.hidden = !chat().padre; };
  new MutationObserver(vis).observe(q("#chat-tabs"), { childList: true });
  vis();
  dev.addEventListener("click", async () => {
    dev.disabled = true;
    try { tell("Devuelto al chat padre: " + await devolverAlPadre(ctx, chat())); } catch (e) { tell("GAP devolver: " + e.message); }
    finally { dev.disabled = false; }
  });
}
