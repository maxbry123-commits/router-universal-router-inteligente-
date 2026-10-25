// ventana-room.js — ROOM CONFERENCIAS: salas compartidas entre el Director, modelos y agentes (estado en el servidor: acción «salas»).
import { accion } from "./api.js";
import { el, btn, campo, falla, ventana } from "./ventanas-control.js";
let salaAbierta = null, temporizador = null;
async function pintarRoom(cuerpo, hoja) {
  const est = el("div", "cv-est");
  const llamar = async (cuerpoReq) => {
    try { const r = await accion("salas", cuerpoReq); est.textContent = r.persistente === false ? "⚠️ Las salas no se guardarán tras reiniciar (almacenamiento HF no disponible)" : ""; return r; }
    catch (x) { falla(est, x); return null; }
  };
  const lista = async () => {
    clearInterval(temporizador); salaAbierta = null;
    const r = await llamar({ accion: "listar" }); if (!r) return;
    const nombre = campo("nombre de la sala"), modelo = el("select"); modelo.setAttribute("aria-label", "Acceso del modelo");
    [["", "El modelo no participa"], ["lectura", "El modelo: lectura"], ["escritura", "El modelo: lectura y escritura"]].forEach(([v, t]) => modelo.append(new Option(t, v)));
    const crear = btn("＋ Nueva sala", "action", async () => { const p = modelo.value ? { modelo: modelo.value } : {}; const x = await llamar({ accion: "crear", nombre: nombre.value, participantes: p }); if (x) lista(); });
    crear.id = "cv-sala-crear";
    const filas = (r.salas || []).map((s) => { const f = el("div", "cv-fila"); const n = el("div", "cv-n"); n.append(el("span", "", s.nombre), el("small", "", Object.keys(s.participantes).join(", ") + " · " + s.mensajes + " mensajes")); f.append(n, btn("Abrir", "secondary", () => sala(s.id))); return f; });
    const form = el("div", "cv-form"); form.append(nombre, modelo, crear);
    cuerpo.replaceChildren(el("div", "cv-sec", "Salas compartidas"), ...(filas.length ? filas : [el("div", "muted", "Sin salas todavía")]), form, est);
  };
  const sala = async (id) => {
    salaAbierta = id;
    const r = await llamar({ accion: "leer", id }); if (!r) return;
    const s = r.sala;
    const msgs = el("div", "list"); s.mensajes.forEach((m) => { const d = el("div", "cv-msg", m.texto); d.prepend(el("small", "", m.de + ": ")); msgs.append(d); });
    const ctx = el("textarea"); ctx.rows = 3; ctx.value = s.contexto || ""; ctx.placeholder = "contexto de la sala (lo ve quien tenga acceso)"; ctx.setAttribute("aria-label", "Contexto");
    const txt = campo("mensaje"); txt.onkeydown = (ev) => { if (ev.key === "Enter") { ev.preventDefault(); enviar.click(); } };
    const turno = btn("Turno de los agentes", "secondary", async () => { turno.disabled = true; turno.textContent = "Hablando…"; const x = await llamar({ accion: "turno", id }); turno.disabled = false; if (x) { await sala(id); if ((x.saltadas || []).length) est.textContent = "Sin responder: " + x.saltadas.map((q) => q.participante + " (" + q.motivo + ")").join(", "); else if (!(x.hablaron || []).length) est.textContent = "Nadie habló: invita con escritura un agente o un modelo (p. ej. qwen3.7-plus); «modelo» es el modelo del chat y solo usa la sala con su herramienta."; } });  // el aviso va después de repintar: leer la sala limpia el estado
    turno.title = "Cada agente o modelo de la sala lee la conversación y responde en este mismo chat (respeta los interruptores IA y Agentes)";
    const enviar = btn("Enviar", "action", async () => { if (!txt.value.trim()) return; const x = await llamar({ accion: "enviar", id, texto: txt.value }); if (x) { txt.value = ""; sala(id); } });
    const parts = Object.entries(s.participantes).map(([n, nv]) => { const f = el("div", "cv-fila"); f.append(el("div", "cv-n", n));
      const sel = el("select"); ["lectura", "escritura", "admin"].forEach((v) => sel.append(new Option(v, v))); sel.value = nv; sel.disabled = n === "director"; sel.onchange = async () => { await llamar({ accion: "permiso", id, participante: n, nivel: sel.value }); sala(id); };
      f.append(sel); if (n !== "director") f.append(btn("Quitar", "secondary", async () => { await llamar({ accion: "permiso", id, participante: n, nivel: null }); sala(id); })); return f; });
    const np = campo("nuevo participante"), nn = el("select"), dl = el("datalist"); dl.id = "cv-part-lista"; np.setAttribute("list", dl.id);
    accion("tools_estado", { rapido: true }).then((e) => dl.replaceChildren(...[...(e.agentes || []).map((a) => a.nombre), ...(e.recursos || []).map((r) => r.id)].map((v) => new Option(v, v)))).catch(() => {});  // agentes y modelos que pueden hablar en el turno
    ["lectura", "escritura", "admin"].forEach((v) => nn.append(new Option(v, v)));
    const inv = el("div", "cv-form"); inv.append(np, dl, nn, btn("Invitar", "secondary", async () => { if (np.value.trim()) { await llamar({ accion: "permiso", id, participante: np.value, nivel: nn.value }); sala(id); } }));
    cuerpo.replaceChildren(btn("← Salas", "secondary", lista), el("div", "cv-sec", s.nombre), el("div", "cv-sec", "Mensajes"), msgs, (() => { const f = el("div", "cv-form"); f.append(txt, enviar, turno); return f; })(),
      el("div", "cv-sec", "Contexto"), ctx, btn("Guardar contexto", "secondary", async () => { if (await llamar({ accion: "contexto", id, texto: ctx.value })) est.textContent = "Contexto guardado"; }),
      el("div", "cv-sec", "Acceso"), ...parts, inv,
      btn("Borrar sala", "secondary", async () => { if (confirm("¿Borrar la sala " + s.nombre + "?") && await llamar({ accion: "borrar", id })) lista(); }), est);
    clearInterval(temporizador); temporizador = setInterval(() => { if (hoja.hidden || salaAbierta !== id || document.activeElement === txt || document.activeElement === ctx) return; sala(id); }, 8000);  // mensajes nuevos sin recargar; no pisa lo que se escribe
  };
  cuerpo.replaceChildren(el("div", "muted", "Cargando…"));
  await lista();
}
const montar = () => ventana("room", "ROOM CONFERENCIAS", pintarRoom);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
