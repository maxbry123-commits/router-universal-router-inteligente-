// controles-ventana.js — 🔑 Conexiones (servicio + varias credenciales + ON/OFF) y 🗣 ROOM CONFERENCIAS (salas compartidas).
// El navegador solo muestra y pide: permisos, secretos y salas viven en el servidor (mvp/control.py). El secreto viaja una vez y nunca vuelve.
import { accion } from "./api.js";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const btn = (txt, cls, fn) => { const b = el("button", cls || "secondary", txt); b.type = "button"; if (fn) b.onclick = fn; return b; };
const campo = (ph, tipo) => { const i = el("input"); i.placeholder = ph; i.type = tipo || "text"; i.autocomplete = "off"; i.setAttribute("aria-label", ph); return i; };
const CSS = `.cv-caja{overflow:auto;max-height:88vh}.cv-fila{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:6px 8px;border-radius:8px;background:rgba(127,127,127,.08);margin:3px 0}
.cv-fila .cv-n{flex:1 1 140px;min-width:0;overflow:hidden;text-overflow:ellipsis}.cv-fila small{opacity:.65;display:block}
.cv-form{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.cv-form input,.cv-form select,.cv-form textarea{flex:1 1 140px;min-width:0;box-sizing:border-box}
.cv-est{font-size:12px;opacity:.85;white-space:pre-wrap;min-height:1em}.cv-msg{padding:4px 8px;margin:2px 0;border-radius:8px;background:rgba(127,127,127,.08);white-space:pre-wrap;overflow-wrap:anywhere}
.cv-msg small{opacity:.65}.cv-sec{margin:10px 0 4px;font-weight:600}`;

function ventana(id, icono, titulo, alAbrir) {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-" + id)) return;
  if (!document.querySelector("#cv-css")) { const st = el("style"); st.id = "cv-css"; st.textContent = CSS; document.head.append(st); }
  const b = btn(icono, "secondary"); b.id = "btn-" + id; b.title = titulo; b.setAttribute("aria-label", titulo);
  const s = el("div", "sheet"); s.id = "ventana-" + id; s.hidden = true;
  const c = el("div", "va-caja cv-caja"), h = el("div", "row va-head"), x = btn("✕", "secondary", () => { s.hidden = true; }), cuerpo = el("div", "list");
  s.onclick = (ev) => { if (ev.target === s) s.hidden = true; };
  h.append(el("strong", "", icono + " " + titulo), x); c.append(h, cuerpo); s.append(c); document.body.append(s);
  b.onclick = () => { s.hidden = false; alAbrir(cuerpo, s); };
  bar.insertBefore(b, bar.querySelector(".action") || null);
}
const falla = (est, x) => { est.textContent = "⚠️ " + x.message; };

// ---------- 🔑 Conexiones ----------
let servicioActivo = "github";
async function pintarConexiones(cuerpo) {
  const est = el("div", "cv-est");
  const cargar = async (cuerpoReq) => {
    try {
      const r = await accion("conexiones", cuerpoReq || {});
      if (r.aviso) est.textContent = "⚠️ " + r.aviso;
      else est.textContent = r.persistente === false ? "⚠️ Los cambios no se guardarán tras reiniciar (almacenamiento HF no disponible)" : "";
      dibujar(r.servicios || []);
    } catch (x) { falla(est, x); }
  };
  const dibujar = (servicios) => {
    const sel = el("select"); sel.setAttribute("aria-label", "Servicio");
    servicios.forEach((s) => sel.append(new Option(s.nombre, s.servicio)));
    if (!servicios.some((s) => s.servicio === servicioActivo)) servicioActivo = (servicios[0] || {}).servicio;
    sel.value = servicioActivo; sel.onchange = () => { servicioActivo = sel.value; dibujar(servicios); };
    const actual = servicios.find((s) => s.servicio === servicioActivo) || { conexiones: [] };
    const lista = el("div", "list");
    actual.conexiones.forEach((c) => {
      const f = el("div", "cv-fila"); f.dataset.conexion = c.id;
      const n = el("div", "cv-n"); n.append(el("span", "", c.etiqueta), el("small", "", c.id === "defecto" ? "credencial principal del banco" : "id " + c.id + (c.herramientas && c.herramientas.length ? " · " + c.herramientas.length + " herramientas (se encienden en 🧰)" : "")));
      const t = btn(c.on ? "ON" : "OFF", "toggle" + (c.on ? " on" : ""), () => cargar({ accion: "activar", servicio: actual.servicio, id: c.id, on: !c.on }));
      t.setAttribute("aria-pressed", String(c.on)); t.title = c.on ? "Conexión activa: apagarla impide nuevas ejecuciones" : "Conexión apagada";
      f.append(n, t);
      if (actual.servicio === "mcp") f.append(btn("Actualizar", "secondary", () => cargar({ accion: "descubrir", id: c.id })));
      lista.append(f);
    });
    if (!actual.conexiones.length) lista.append(el("div", "muted", "Sin conexiones: añade la primera con ＋"));
    const et = campo("nombre de la conexión"), sec = campo("clave / token (solo viaja al servidor)", "password"), url = campo("URL del servidor MCP (https://…)");
    url.hidden = actual.servicio !== "mcp";
    if (actual.servicio === "mcp") sec.placeholder = "token Bearer (opcional)";
    const mas = btn("＋ Añadir", "action", async () => {
      const cuerpoReq = { accion: "agregar", servicio: actual.servicio, etiqueta: et.value || undefined, secreto: sec.value || undefined, url: url.value || undefined };
      sec.value = ""; await cargar(cuerpoReq); et.value = ""; url.value = "";
    });
    mas.id = "cv-anadir";
    const form = el("div", "cv-form"); form.append(et, sec, url, mas);
    cuerpo.replaceChildren(el("div", "cv-sec", "Servicio"), sel, lista, form, est);
  };
  cuerpo.replaceChildren(el("div", "muted", "Cargando…"));
  await cargar();
}

// ---------- 🗣 ROOM CONFERENCIAS ----------
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
    const enviar = btn("Enviar", "action", async () => { if (!txt.value.trim()) return; const x = await llamar({ accion: "enviar", id, texto: txt.value }); if (x) { txt.value = ""; sala(id); } });
    const parts = Object.entries(s.participantes).map(([n, nv]) => { const f = el("div", "cv-fila"); f.append(el("div", "cv-n", n));
      const sel = el("select"); ["lectura", "escritura", "admin"].forEach((v) => sel.append(new Option(v, v))); sel.value = nv; sel.disabled = n === "director"; sel.onchange = async () => { await llamar({ accion: "permiso", id, participante: n, nivel: sel.value }); sala(id); };
      f.append(sel); if (n !== "director") f.append(btn("Quitar", "secondary", async () => { await llamar({ accion: "permiso", id, participante: n, nivel: null }); sala(id); })); return f; });
    const np = campo("nuevo participante"), nn = el("select"); ["lectura", "escritura", "admin"].forEach((v) => nn.append(new Option(v, v)));
    const inv = el("div", "cv-form"); inv.append(np, nn, btn("Invitar", "secondary", async () => { if (np.value.trim()) { await llamar({ accion: "permiso", id, participante: np.value, nivel: nn.value }); sala(id); } }));
    cuerpo.replaceChildren(btn("← Salas", "secondary", lista), el("div", "cv-sec", "🗣 " + s.nombre), el("div", "cv-sec", "Mensajes"), msgs, (() => { const f = el("div", "cv-form"); f.append(txt, enviar); return f; })(),
      el("div", "cv-sec", "Contexto"), ctx, btn("Guardar contexto", "secondary", async () => { if (await llamar({ accion: "contexto", id, texto: ctx.value })) est.textContent = "Contexto guardado"; }),
      el("div", "cv-sec", "Acceso"), ...parts, inv,
      btn("Borrar sala", "secondary", async () => { if (confirm("¿Borrar la sala " + s.nombre + "?") && await llamar({ accion: "borrar", id })) lista(); }), est);
    clearInterval(temporizador); temporizador = setInterval(() => { if (hoja.hidden || salaAbierta !== id || document.activeElement === txt || document.activeElement === ctx) return; sala(id); }, 8000);  // mensajes nuevos sin recargar; no pisa lo que se escribe
  };
  cuerpo.replaceChildren(el("div", "muted", "Cargando…"));
  await lista();
}

const revisar = () => { try { ventana("conexiones", "🔑", "Conexiones", pintarConexiones); ventana("room", "🗣", "ROOM CONFERENCIAS", pintarRoom); } catch (e) { console.warn("controles-ventana", e); } };
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
