import { node } from "./api.js";
import * as A from "./chat-ancla.js";
// enviar-mensaje.js — envío del mensaje: cada chat corre su tarea con su sesión, ficha, anclas, modos y herramientas
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export function montarEnviar(ctx) {
  const { q, chat, abajo, burbuja, ajustarAlturaEditor, pintarTabs, getModeUI, releerAnclas, chatTools, FAST_SEL, getModo, previo, api, tell } = ctx;
  q("#composer").addEventListener("submit", async event => {
    chat().hist.__sigue = true;  // al enviar vuelves al final
    event.preventDefault();
    const c = chat();
    const input = q("#message");
    const rawText = input.value;
    const message = rawText.trim();
    if (!message) return;
    if (c.ocupado) { tell("Este chat ya tiene una tarea en curso"); return; }  // una tarea por chat; los demas chats siguen en paralelo
    if (message === "/ayuda") { tell("Elige modelo en la píldora, enciende anclas/archivos y envía. /ayuda no ejecuta modelos."); return; }
    const selAct = window.RIU_SELECTORES?.activo;  // solo "Nvidia groq team" tiene modelos reales en el Router hoy
    const fichaQwen = selAct === "team-qwen" && c.selectorQwen ? "qw-" + c.selectorQwen.modelo_id_slug : null;  // Team qwen: su ficha, mismo camino que Nvidia
    const fichaGroq = selAct === "groq" ? ((window.RIU_GROQ || {}).modelo || "") : null;  // selector Groq: el modelo elegido en su hoja (groq/<id>)
    if (fichaGroq === "") { c.hist.append(node("div", "Groq: " + ((window.RIU_GROQ || {}).aviso || "elige primero un modelo en la hoja Groq ⌄") + ". No se envió a otro modelo.", "item message meta")); abajo(c); return; }
    const fichaMvp = selAct === "team-5-mvp";  // Team 5 MVP: ruta propia -> fichas_qwen ficha_qwen=5 (1 modelo elegido, historial completo y tools)
    if (fichaMvp && !c.selectorQwen) {
      c.hist.append(node("div", "Team 5 MVP: elige primero un modelo en la hoja Team 5 MVP ⌄ (el mismo catalogo de la Ficha 1 / Team qwen). No se envio a otro modelo.", "item message meta"));
      abajo(c);
      return;
    }
    const CONSIL_LISTO = /^(ask-consil-code-qwen-team|ask-consil-fromtend-qwen-team|ask-consil-nvidia-groq)$/;  // Ask Consil cableados al Router; nvidia-groq va como CONSULTA a la ficha ask-consil-factory
    if (selAct && selAct !== "nvidia-groq-team" && selAct !== "groq" && !fichaQwen && !CONSIL_LISTO.test(selAct) && !fichaMvp) {
      const nomSel = (window.RIU_SELECTORES.selectores.find((x) => x.id === selAct) || {}).nombre || selAct;
      const det = selAct === "team-qwen" ? (c.selectorQwen ? " · " + c.selectorQwen.label : " · sin modelo elegido") : "";
      c.hist.append(node("div", nomSel + det + ": sin IA conectada en el Router (no hay proveedor ni clave para estos modelos). No se envió a otro modelo. Enciende Nvidia groq team o apaga el selector.", "item message meta"));
      abajo(c);
      return;
    }
    const ub = burbuja(rawText, "user");
    c.hist.append(ub);
    A.registrar(c.sesion, "user", rawText);
    input.value = ""; ajustarAlturaEditor();
    c.ocupado = true; pintarTabs();
    const pending = node("div", "Enviando…", "item message pending");  // Enviando hasta que el Router confirma proceso_id; luego riu-progreso pone Pensando/tools
    c.hist.append(pending);
    const alProgreso = (e) => {
      if (!pending.isConnected) { window.removeEventListener('riu-progreso', alProgreso); return; }  // listener fuera solo si la burbuja desaparecio (o en finally)
      const d = e.detail;
      if (!d || d.sesion !== c.sesion) return;  // evento de otro chat: ignorar, no quitarse
      const v = window.RIU_PENDIENTE && window.RIU_PENDIENTE(c.sesion);  // progreso aislado: solo mi sesion y, si hay PID guardado, solo mi proceso
      if (v && v.pid && d.proceso_id && d.proceso_id !== v.pid) return;
      if (d.parcial) { const ya = pending.classList.contains('parcial') ? pending.textContent : ''; if (ya && d.parcial.startsWith(ya)) { if (d.parcial.length > ya.length) pending.append(d.parcial.slice(ya.length)); } else pending.textContent = d.parcial; pending.classList.add('parcial'); try { abajo(c); } catch (x) {} return; }  // render incremental: solo se anade el trozo nuevo  // texto parcial en stream dentro de la burbuja; la final la reemplaza (pending.remove)
      if (pending.classList.contains('parcial')) return;  // ya hay texto parcial: no volver a 'Pensando…'
      pending.textContent = d.texto !== undefined ? d.texto : d;
    };
    window.addEventListener('riu-progreso', alProgreso);
    try { abajo(c); } catch (e) {}
    const agent = (q("#agent") || {}).value || "";
    const provider = (q("#provider") || {}).value || "";
    const model = (q("#model") || {}).value || "";
    const max_tokens = undefined; // sin tope artificial del frontend; el proveedor informa finish_reason
    try {
      const selAct = window.RIU_SELECTORES?.activo;  // selectores Qwen -> plugin fichas_qwen (fichas 1, 2, 3 y 5 = Team 5 MVP)
      const fq = selAct === "team-qwen" ? "1" : selAct === "ask-consil-code-qwen-team" ? "2" : selAct === "ask-consil-fromtend-qwen-team" ? "3" : null;
      const soloLiteralQwen = fq === "2" || fq === "3";  // ficha 2/3: input verbatim del Director (sin envolver ni trim)
      const mvp = selAct === "team-5-mvp" ? { plugin: "fichas_qwen", ficha_qwen: "5", modelo: c.selectorQwen ? (c.selectorQwen.model_id || c.selectorQwen.label) : "", instrucciones_fijas: c.instrucciones || "" } : null;  // Team 5 MVP: fichas_qwen ficha_qwen=5, sin N4, sin fallback
      const mensajeQwen = soloLiteralQwen ? rawText : (mvp ? rawText : A.envolver(rawText, c.instrucciones)); // no eliminar espacios del input real
      const fijasQwen = (soloLiteralQwen || mvp) ? (c.instrucciones || "") : "";
      const _conModo = getModeUI() ? getModeUI().wrapSend((b) => b) : ((b) => b);  // >>> MODOS <<< punto B: agrega mode_request al payload sin tocar el resto
      const anclados = releerAnclas(c);
      const controlTools = { tools: !!chatTools.tools, agente_tool: !!chatTools.agente_tool, llm_tool: !!chatTools.llm_tool };
      const body = _conModo({ ...controlTools, message: mensajeQwen, ficha: fichaQwen || fichaGroq || (selAct === "ask-consil-nvidia-groq" ? "ask-consil-factory" : c.ficha), provider, model, mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens: mvp ? 0 : max_tokens, fast_reply: !!c.fastReply && FAST_SEL(), motor: !!c.motor, project_id: c.project_id || null, thinking: getModo() === "think", ...(fijasQwen ? { instrucciones_fijas: fijasQwen } : {}), ...(fq ? { plugin: "fichas_qwen", ficha_qwen: fq, modelo: fq === "1" && c.selectorQwen ? (c.selectorQwen.model_id || c.selectorQwen.label) : "", task_type: "chat" } : {}), ...(mvp || {}) });  // MVP: input literal + instrucciones_fijas aparte, max_tokens lo decide la ficha; ficha 2/3 verbatim + instrucciones_fijas
      // con harnessUrl el mensaje va al harness DeepSeek (y este a la memoria por su plugin); si no, al Router como hoy
      c.detenerFlag = false;
      const raceDetener = new Promise((_, rej) => { c.detenerFn = () => rej(new Error("PROCESO_DETENIDO")); });  // Detener ya vale desde aqui: tambien mientras se restaura el historial o se arma el contexto
      const ctxPrev = (fq || mvp) ? previo(c, rawText) : undefined;
      body.contexto_previo = ctxPrev;  // historial completo de esta sesion; el input actual viaja una sola vez
      const _multiSel = fq === "1" && c.paralelo ? (c.selectorQwenMulti || []).slice(0, 6) : [];  // >>> MODOS <<< T6: fan-out paralelo
      const _fanout = async () => {  // una llamada por modelo elegido; cada burbuja lleva su nombre
        const rs = await Promise.allSettled(_multiSel.map((m, i) => window.RIU_HARNESS({
          model: 'qw-' + (m.modelo_id_slug || 'modelo'), message: mensajeQwen, max_tokens: mvp ? 0 : max_tokens, fast_reply: !!c.fastReply && FAST_SEL(), motor: !!c.motor, project_id: c.project_id || null,
          contexto_previo: ctxPrev, anclados, sesion: c.sesion + '-' + (m.modelo_id_slug || i), instrucciones_fijas: fijasQwen || undefined,
          ...controlTools, thinking_mode: getModo() === 'think' ? 'on' : 'off',
          mode_request: getModeUI() ? getModeUI().getModeRequest() : undefined, tool_approval: getModeUI() && getModeUI().getApproval ? getModeUI().getApproval() : undefined,
          qwen: { plugin: "fichas_qwen", ficha_qwen: "1", modelo: m.model_id || m.label || m.modelo_id_slug || "", task_type: "chat" }, avisar: () => {} })));
        const partes = rs.map((r, i) => {
          const nom = _multiSel[i].label || _multiSel[i].modelo_id_slug || ('modelo ' + (i + 1));
          return r.status === 'fulfilled' ? ('── ' + nom + ' ──\n' + (r.value.reply || 'Sin respuesta')) : ('── ' + nom + ' ──\nGAP: ' + (r.reason && r.reason.message || r.reason));
        });
        return { reply: partes.join('\n\n'), tools: [], ms: 0, finish_reason: rs.some((r) => r.status === 'fulfilled' && r.value.finish_reason === 'length') ? 'length' : null };
      };
      const answer = window.RIU_CONFIG?.harnessUrl
        ? (_multiSel.length > 1
            ? await Promise.race([_fanout(), raceDetener])  // >>> MODOS <<< T6: misma tarea a cada modelo; un proceso por modelo en el backend
            : await Promise.race([window.RIU_HARNESS({ model: fichaQwen || fichaGroq || (selAct === "ask-consil-nvidia-groq" ? "ask-consil-factory" : c.ficha), message: mensajeQwen, max_tokens: mvp ? 0 : max_tokens, fast_reply: !!c.fastReply && FAST_SEL(), motor: !!c.motor, project_id: c.project_id || null, contexto_previo: ctxPrev, anclados, sesion: c.sesion, instrucciones_fijas: fijasQwen || undefined, ...controlTools, thinking_mode: (fq || mvp) ? (getModo() === 'think' ? 'on' : 'off') : undefined, mode_request: getModeUI() ? getModeUI().getModeRequest() : undefined,  // >>> MODOS <<<
        qwen: fq ? { plugin: "fichas_qwen", ficha_qwen: fq, modelo: fq === "1" && c.selectorQwen ? (c.selectorQwen.model_id || c.selectorQwen.label) : "", task_type: "chat" } : (mvp || null), avisar: (t) => c.hist.append(node('div', t, 'item message')) }), raceDetener]))
        : await Promise.race([api("/chat/send", { method: "POST", body }), raceDetener]);  // >>> MODOS <<< body ya lleva mode_request
      c.detenerFn = null;
      if (c.detenerFlag) throw new Error("PROCESO_DETENIDO");  // detenido mientras la respuesta llegaba: no pintar respuesta tardia
      pending.remove();
      if (answer.modelo_solicitado) c.hist.append(node("div", "Modelo solicitado: " + answer.modelo_solicitado + " · API: " + (answer.modelo_respuesta || "sin identificar"), "item message meta"));
      if (answer.aviso) c.hist.append(node("div", "Aviso: " + answer.aviso, "item message meta"));  // p. ej. modo Objetivo: un turno (sin bucle autónomo en el MVP)
      c.hist.append(burbuja(answer.reply || "Sin respuesta"));
      A.registrar(c.sesion, "bot", answer.reply || "Sin respuesta");
      if (answer.finish_reason === "length") { const aviso = node("div", "La respuesta se cortó por el límite de salida del proveedor. ", "item message meta"), seguir = node("button", "Continuar", "mx-continuar"); seguir.type = "button"; seguir.onclick = () => { seguir.disabled = true; const m = q("#message"); m.value = "Continúa exactamente donde se cortó la respuesta anterior, sin repetir texto."; q("#composer").requestSubmit(); }; aviso.append(seguir); c.hist.append(aviso); }  // un clic y sigue desde el corte
      if (answer.execution_path === "FAST_QA") c.hist.append(node("div", "⚡ respuesta rápida · " + answer.ms + " ms", "item meta"));
      else if (answer.execution_path === "FAST_CONSULT") c.hist.append(node("div", "⚡ cónsil rápido · " + answer.ms + " ms", "item meta"));
      else if (c.fastReply && FAST_SEL() && answer.execution_path === "HEAVY") c.hist.append(node("div", "Respuesta rápida omitida: la tarea requiere flujo completo", "item meta"));
      if (answer.tools && answer.tools.length) { const meta = node("div", "Herramientas usadas: ", "item message meta"); answer.tools.forEach((t, i) => { const ok = typeof t === "string" || t.ok; const s = document.createElement("span"); s.textContent = (typeof t === "string" ? t : t.nombre) + (ok ? "" : " (fallo)"); if (!ok) s.className = "tool-fail"; if (i) meta.append(", "); meta.append(s); }); c.hist.append(meta); }
      if (answer.job_id) { window.__riuJob = answer.job_id; const ar = q('#apagar-respaldo'); if (ar) ar.hidden = false; }
      abajo(c);
    } catch (error) {
      pending.remove();
      const detalleError = error && error.name === "AbortError" ? "Tiempo de espera agotado" : error.message;
      A.registrar(c.sesion, "err", (c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message))) ? "proceso detenido por el usuario" : "GAP: " + detalleError);
      c.hist.append(node("div", (c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message))) ? "proceso detenido por el usuario" : `GAP: ${detalleError}`, "item message" + (c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message)) ? " meta" : " error")));
      abajo(c);
      if (!(c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message))) && !input.value) { input.value = message; input.dispatchEvent(new Event("input", { bubbles: true })); }  // si falla, el mensaje vuelve a la caja
    } finally {
      window.removeEventListener('riu-progreso', alProgreso);  // listener fuera al terminar/error/cancelar
      c.detenerFn = null; c.ocupado = false; pintarTabs();
      if (window.matchMedia("(pointer: fine)").matches) input.focus();
    }
  });
}
