// ventana-conexiones.js — Conexiones: servicio + varias credenciales + ON/OFF. El secreto viaja una vez al servidor y nunca vuelve.
import { accion } from "./api.js";
import { el, btn, campo, falla, ventana } from "./ventanas-control.js";
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
      const n = el("div", "cv-n"); n.append(el("span", "", c.etiqueta), el("small", "", c.id === "defecto" ? "credencial principal del banco" : "id " + c.id + (c.herramientas && c.herramientas.length ? " · " + c.herramientas.length + " herramientas (se encienden en IA)" : "")));
      const t = btn(c.on ? "ON" : "OFF", "toggle" + (c.on ? " on" : ""), () => cargar({ accion: "activar", servicio: actual.servicio, id: c.id, on: !c.on }));
      t.setAttribute("aria-pressed", String(c.on)); t.title = c.on ? "Conexión activa: apagarla impide nuevas ejecuciones" : "Conexión apagada";
      f.append(n, t);
      if (c.id !== "defecto") { const q = btn("Quitar", "secondary"); q.setAttribute("aria-label", "Quitar " + c.etiqueta); q.onclick = () => { if (q.dataset.ok) return cargar({ accion: "quitar", servicio: actual.servicio, id: c.id }); q.dataset.ok = "1"; q.textContent = "¿Quitar? Confirmar"; setTimeout(() => { delete q.dataset.ok; q.textContent = "Quitar"; }, 5000); }; f.append(q); }
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
const montar = () => ventana("conexiones", "Conexiones", pintarConexiones);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
