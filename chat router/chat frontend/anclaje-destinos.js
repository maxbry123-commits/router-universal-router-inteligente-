// anclaje-destinos.js — en la ventana de Anclaje: "Anclar a" Chat / Constitución / Workflows / Agentes remotos / Proyecto / Sandbox.
// Es LA MISMA ventana para todos: al elegir el objetivo, todo lo de la ventana (enlaces, anclado ahora, instrucciones fijas, proyectos,
// handoffs, Mi handoff y archivos) se aplica a ese objetivo. Los archivos son compartidos. Sin elegir nada, es el chat de siempre.
import { OBJETIVOS, crearObjetivo, listaWF, listaProyectos, crearProyecto, slugProy, proyId, buscarProyecto } from "./objetivos-ancla.js";
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
    // encendido/apagado de CADA ancla, siempre visible en la hoja (la Constitución arranca apagada; solo viaja si está encendida)
    const est = el("div", "vn-fila vn-encendidos"); est.append(el("div", "vn-t", "Encendido de cada ancla"));
    const tog = (t, id, etq) => { const o = crearObjetivo(t, id); if (!o) return; const on = !!o.encendido, b = boton(etq + ": " + (on ? "ON" : "OFF"), "toggle" + (on ? " on" : ""), () => { o.encendido = !o.encendido; tell(etq + (o.encendido ? ": ON · viaja con cada mensaje" : ": OFF · no se envía")); pintar(); }); b.dataset.ancla = t + (id ? ":" + id : ""); b.setAttribute("aria-pressed", String(on)); est.append(b); };
    est.append(el("span", "vn-estado", "● Chat · siempre"));
    tog("constitucion", undefined, "Constitución"); listaWF().forEach((w) => tog("workflows", w.id, "Workflow " + w.nombre)); tog("agentes", undefined, "Agentes remotos"); listaProyectos().forEach((p) => tog("proyecto", p.nombre, "Proyecto " + p.nombre)); tog("sandbox", undefined, "Sandbox");
    fila.append(est);
    if (tipo === "workflows" && obj) {
      const s = el("select", "vn-in"); s.setAttribute("aria-label", "Workflow");
      listaWF().forEach((w) => { const o = el("option", "", w.nombre); o.value = w.id; s.append(o); }); s.value = obj.id;
      s.addEventListener("change", () => fijar("workflows", s.value)); fila.append(s);
    }
    if (tipo === "proyecto" && obj) {
      const s = el("select", "vn-in"); s.setAttribute("aria-label", "Carpeta de proyecto");
      listaProyectos().forEach((p) => { const o = el("option", "", p.nombre); o.value = p.project_id; s.append(o); }); s.value = obj.project_id;  // cada proyecto se ancla por su propio ID
      const on = el("option", "", "＋ Nuevo proyecto"); on.value = "__nuevo__"; s.append(on);
      s.addEventListener("change", () => {
        if (s.value !== "__nuevo__") { fijar("proyecto", s.value); return; }
        const n = (window.prompt("Nombre del nuevo proyecto") || "").trim(); s.value = obj.project_id;
        if (!n) return;
        const ya = listaProyectos().some((p) => p.nombre.toLowerCase() === n.toLowerCase()), nom2 = crearProyecto(n), p = buscarProyecto(nom2);
        if (!p) { tell("No se pudo crear"); return; }
        tell((ya ? "Ya existía: " : "Proyecto creado: ") + p.nombre); fijar("proyecto", p.project_id);
      });
      const nom = el("input", "vn-in"); nom.placeholder = "Nueva carpeta de proyecto…"; nom.maxLength = 60; nom.setAttribute("aria-label", "Nueva carpeta de proyecto");
      const nuevo = boton("＋ Carpeta", "mini", () => { const n = crearProyecto(nom.value); if (!n) { tell("Escribe un nombre"); return; } tell("Carpeta creada: " + n); fijar("proyecto", n); });
      const f2 = el("div", "vn-fila"); f2.append(nom, nuevo); fila.append(s, f2);
      try {
        const c = window.RIU_CHAT && window.RIU_CHAT.chat(), pid = obj.project_id || proyId(obj.id);  // project_id persistido del objetivo (crearObjetivo lo transporta); slug solo en proyectos viejos
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
    if (obj) fila.append(el("div", "vn-estado", obj.nombre + ": " + (obj.encendido ? "ON · viaja con cada mensaje" : "OFF · no se envía") + " (se cambia arriba)"));  // un solo botón por ancla: el de «Encendido de cada ancla»
    else fila.append(el("div", "vn-estado", "Chat: lo anclado viaja con cada mensaje del chat activo."));
  }
  pintar(); unBotonMiHandoff(q, tell); chipAncla(q);
  window.addEventListener("riu:almacen", () => { if (!root.isConnected) return; chipAncla(q); });
  window.RIU_ANCLA_ABRIR = (t, id) => {  // lo usan las ventanas de workflow / constitución: abre ESTA ventana con ese objetivo
    if (!fijar(t, id, false)) return;
    const s = q("#ventana-ancla"), b = q("#btn-ancla");
    if (s && s.hidden && b) b.click(); else if (window.RIU_ANCLA_REFRESCAR) window.RIU_ANCLA_REFRESCAR();
  };
  const sh = q("#ventana-ancla");
  if (sh) new MutationObserver(() => { if (sh.hidden && tipo !== "chat") fijar("chat", undefined, false); }).observe(sh, { attributes: true, attributeFilter: ["hidden"] });
}
function chipAncla(q) {  // el chip «ancla» del chat (pastilla y botón ⚓ del input, el visible en móvil) muestra si la Constitución está ON u OFF
  const on = !!crearObjetivo("constitucion").encendido, ba = q("#btn-ancla") || document.getElementById("btn-ancla");
  if (ba) { let m = ba.querySelector(".riu-const-chip"); if (!m) { m = document.createElement("span"); m.className = "riu-const-chip"; m.style.cssText = "position:absolute;top:-6px;left:-6px;font-size:11px;line-height:1;pointer-events:none"; ba.style.position = ba.style.position || "relative"; ba.append(m); }
    m.textContent = on ? "📜" : ""; ba.dataset.const = on ? "on" : "off"; ba.title = "Anclaje · Constitución " + (on ? "ON" : "OFF"); }
  const pill = q("#ancla") || document.getElementById("ancla"); if (!pill) return;  // en móvil la pastilla se mueve fuera del panel (#mv-ctl)
  pill.textContent = "ancla · 📜 " + (on ? "ON" : "OFF") + " ⌄"; pill.classList.toggle("on", on); pill.title = "Constitución " + (on ? "ON: viaja con cada mensaje" : "OFF: no se envía");
}
function unBotonMiHandoff(q, tell) {  // Mi handoff: un solo botón ON/OFF en lugar de «Encender/Guardar» + «Apagar» (los originales quedan ocultos y siguen funcionando)
  const g = q("#mh-guardar"), a = q("#mh-apagar"), est = q("#mh-estado"), enl = q("#ancla-enlace-on");
  if (enl) enl.textContent = "Anclar";
  if (!g || !a || !est || g.dataset.uno) return; g.dataset.uno = "1"; [g, a, est].forEach((x) => { x.style.display = "none"; });
  const t = document.createElement("button"); t.type = "button"; t.id = "mh-toggle"; g.before(t);
  const pinta = () => { const on = est.textContent.trim() === "encendido"; t.textContent = "Mi handoff: " + (on ? "ON" : "OFF"); t.className = "toggle" + (on ? " on" : ""); t.setAttribute("aria-pressed", String(on)); };
  t.addEventListener("click", () => { if (est.textContent.trim() === "encendido") a.click(); else { const m = q("#mi-handoff"); if (!m || !m.value.trim()) { tell("Escribe tu handoff primero"); return; } g.click(); } });
  new MutationObserver(pinta).observe(est, { childList: true, characterData: true, subtree: true }); pinta();
}
