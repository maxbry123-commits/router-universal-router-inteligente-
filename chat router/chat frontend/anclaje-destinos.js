// anclaje-destinos.js — en la ventana de Anclaje: "Anclar a" Chat / Constitución / Workflows / Agentes remotos / Proyecto / Sandbox.
// Es LA MISMA ventana para todos: al elegir el objetivo, todo lo de la ventana (enlaces, anclado ahora, instrucciones fijas, proyectos,
// handoffs, Mi handoff y archivos) se aplica a ese objetivo. Los archivos son compartidos. Sin elegir nada, es el chat de siempre.
import { OBJETIVOS, crearObjetivo, listaWF, listaProyectos, crearProyecto, slugProy, proyId } from "./objetivos-ancla.js";
import { el, boton, cargarCss } from "./ventanas-comun.js";
export function montarDestinos({ root, q, tell }) {
  const caja = q("#ventana-ancla .va-caja"); if (!caja || caja.dataset.destinos) return; caja.dataset.destinos = "1";
  cargarCss("ventanas-comun");
  const fila = el("div", "vn-sec vn-destinos"), head = caja.querySelector(".va-head"), titulo = head && head.querySelector("strong"), base = titulo ? titulo.textContent : "Anclaje";
  if (head) head.after(fila); else caja.prepend(fila);
  let tipo = "chat", obj = null;
  function fijar(t, id, refrescar) {
    if (t === "proyecto" && !id) { let l = listaProyectos(); if (!l.length) { crearProyecto("Proyecto 1"); l = listaProyectos(); } if (l.length) id = l[0].nombre; }  // misma regla que cambiar(): sin id, el primero existente o uno nuevo
    const nuevo = t === "chat" ? null : crearObjetivo(t, id);
    if (t !== "chat" && !nuevo) return false;
    tipo = t; obj = nuevo; window.RIU_OBJETIVO_ANCLA = obj ? () => obj : undefined;
    // seleccionar/abrir un Proyecto NO vincula el chat: el vinculo es SOLO via el boton [Añadir chat actual] (mas abajo)
    if (titulo) titulo.textContent = base + (obj ? " · " + obj.nombre : "");
    window.dispatchEvent(new CustomEvent("riu:objetivo"));
    if (refrescar !== false && window.RIU_ANCLA_REFRESCAR) window.RIU_ANCLA_REFRESCAR();
    pintar(); return true;
  }
  function cambiar(t) {
    if (t === "workflows") { const l = listaWF(); if (!l.length) { tell("Crea un workflow primero en la fila workflow Loops code Yaiwes"); return; } fijar(t, l[0].id); return; }
    if (t === "proyecto") { let l = listaProyectos(); if (!l.length) { crearProyecto("Proyecto 1"); l = listaProyectos(); } fijar(t, l[0].nombre); return; }
    fijar(t);
  }
  function pintar() {
    fila.replaceChildren(el("div", "vn-t", "Anclar a · misma ventana, cambia el objetivo"));
    const bs = el("div", "vn-fila");
    OBJETIVOS.forEach(([id, nom]) => { const on = id === tipo, b = boton(nom, "toggle" + (on ? " on" : ""), () => cambiar(id)); b.setAttribute("aria-pressed", String(on)); bs.append(b); });
    fila.append(bs);
    if (tipo === "workflows" && obj) {
      const s = el("select", "vn-in"); s.setAttribute("aria-label", "Workflow");
      listaWF().forEach((w) => { const o = el("option", "", w.nombre); o.value = w.id; s.append(o); }); s.value = obj.id;
      s.addEventListener("change", () => fijar("workflows", s.value)); fila.append(s);
    }
    if (tipo === "proyecto" && obj) {
      const s = el("select", "vn-in"); s.setAttribute("aria-label", "Carpeta de proyecto");
      listaProyectos().forEach((p) => { const o = el("option", "", p.nombre); o.value = p.nombre; s.append(o); }); s.value = obj.id;
      s.addEventListener("change", () => fijar("proyecto", s.value));
      const nom = el("input", "vn-in"); nom.placeholder = "Nueva carpeta de proyecto…"; nom.maxLength = 60; nom.setAttribute("aria-label", "Nueva carpeta de proyecto");
      const nuevo = boton("＋ Carpeta", "mini", () => { const n = crearProyecto(nom.value); if (!n) { tell("Escribe un nombre"); return; } tell("Carpeta creada: " + n); fijar("proyecto", n); });
      const f2 = el("div", "vn-fila"); f2.append(nom, nuevo); fila.append(s, f2);
      try {
        const c = window.RIU_CHAT && window.RIU_CHAT.chat(), pid = proyId(obj.id);  // project_id real (p-<uid>) si existe; slug solo en proyectos viejos
        if (c && window.RIU_ACCION) {
          const vinc = c.project_id === pid;
          const b = boton(vinc ? "Quitar chat actual" : "Añadir chat actual", "mini", async () => {
            const c2 = window.RIU_CHAT && window.RIU_CHAT.chat(); if (!c2) return;
            try {
              if (c2.project_id === pid) {
                await window.RIU_ACCION("proyecto", { op: "unlink_chat", project_id: pid, sesion: c2.sesion });
                c2.project_id = null; tell("Chat quitado del proyecto «" + obj.id + "»");
              } else {
                if (c2.project_id) await window.RIU_ACCION("proyecto", { op: "unlink_chat", project_id: c2.project_id, sesion: c2.sesion });
                await window.RIU_ACCION("proyecto", { op: "link_chat", project_id: pid, sesion: c2.sesion });
                c2.project_id = pid; tell("Chat añadido al proyecto «" + obj.id + "»");
              }
              if (window.RIU_CHAT && window.RIU_CHAT.pintar) window.RIU_CHAT.pintar();
              pintar();
            } catch (e) { tell("No se pudo: " + (e && e.message ? e.message : e)); }
          });
          fila.append(b);
        }
      } catch (e) {}
    }
    if (obj) {
      const b = boton(obj.encendido ? "Encendido · viaja con cada mensaje" : "Apagado · encender para que viaje con cada mensaje", "toggle" + (obj.encendido ? " on" : ""), () => { obj.encendido = !obj.encendido; tell(obj.nombre + (obj.encendido ? " encendido" : " apagado")); pintar(); });
      b.setAttribute("aria-pressed", String(obj.encendido)); fila.append(b);
    } else fila.append(el("div", "vn-estado", "Chat: lo anclado viaja con cada mensaje del chat activo."));
  }
  pintar();
  window.RIU_ANCLA_ABRIR = (t, id) => {  // lo usan las ventanas de workflow / constitución: abre ESTA ventana con ese objetivo
    if (!fijar(t, id, false)) return;
    const s = q("#ventana-ancla"), b = q("#btn-ancla");
    if (s && s.hidden && b) b.click(); else if (window.RIU_ANCLA_REFRESCAR) window.RIU_ANCLA_REFRESCAR();
  };
  const sh = q("#ventana-ancla");
  if (sh) new MutationObserver(() => { if (sh.hidden && tipo !== "chat") fijar("chat", undefined, false); }).observe(sh, { attributes: true, attributeFilter: ["hidden"] });
}
