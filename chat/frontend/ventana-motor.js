import { node } from "./api.js";
// ventana-motor.js — ventana del motor: descarga/extracción/copiar/mover entre repos
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export function montarMotor(ctx) {
  const { chat, abajo, q, chatA, pintarAnclados, guardar, cerrarHojas, burbuja, tell } = ctx;
  // ---- ventana del motor: descarga/extraccion/copiar/mover entre repos ----
  const extraerUrls = (t) => { const s = new Set(); (String(t || "").match(/https?:\/\/[^\s"'<>)\]]+/g) || []).forEach((u) => s.add(u.replace(/[.,;:!?]+$/g, ""))); return [...s]; };
  const motorConfirma = (t) => { chat().hist.append(node("div", t, "item message meta")); abajo(chat()); };
  const mm = q("#motor-mover"), mc = q("#motor-copiar");
  mm.addEventListener("change", () => { if (mm.checked) mc.checked = false; else if (!mc.checked) mm.checked = true; });
  mc.addEventListener("change", () => { if (mc.checked) mm.checked = false; else if (!mm.checked) mc.checked = true; });
  const motorEjecutar = async (origen, destino, op) => {
    if (!origen || !destino) { tell("Falta el enlace de origen o de destino"); return null; }
    try {
      const r = await window.RIU_ACCION("mover_raiz", { op, origen, destino, sesion: chat().sesion });
      if (r.error) { motorConfirma("motor: GAP " + r.error + " — " + (r.detalle || "")); return r; }
      motorConfirma(r.op + " ✓ " + r.archivos + " archivo(s) · " + r.estado + " · " + r.registro + (r.fallos && r.fallos.length ? " · fallos: " + r.fallos.join(", ") : ""));
      return r;
    } catch (e) { motorConfirma("motor: GAP " + e.message); return null; }
  };
  q("#motor-ejecutar").addEventListener("click", async () => {
    await motorEjecutar(q("#motor-origen").value.trim(), q("#motor-destino").value.trim(), mm.checked ? "mover" : "copiar");
  });
  q("#motor-archivo-btn").addEventListener("click", () => q("#motor-archivo").click());
  q("#motor-archivo").addEventListener("change", async (e) => {
    const f = e.target.files[0]; e.target.value = "";
    if (!f) return;
    const txt = await f.text();
    const urls = extraerUrls(txt);
    const viejo = q("#motor-urls").value.trim();
    q("#motor-urls").value = (viejo ? viejo + "\n" : "") + urls.join("\n");
    motorConfirma("archivo " + f.name + ": " + urls.length + " URL(s) visibles extraídas");
  });
  q("#motor-activar").addEventListener("click", async () => {
    const urls = extraerUrls(q("#motor-urls").value);
    const dest = q("#motor-destino2").value.trim() || q("#motor-destino").value.trim();
    if (!urls.length || !dest) { tell("Pega las URLs y el enlace destino"); return; }
    q("#motor-cola").textContent = "cola: " + urls.length + " descarga(s)";
    for (let i = 0; i < urls.length; i++) {
      q("#motor-cola").textContent = "cola: " + (i + 1) + "/" + urls.length + " → " + urls[i].slice(0, 60);
      await motorEjecutar(urls[i], dest, "copiar");
    }
    q("#motor-cola").textContent = "cola terminada: " + urls.length + "/" + urls.length;
  });
  q("#motor-auditar").addEventListener("click", async () => {
    const lista = q("#motor-hist");
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await window.RIU_ACCION("descargas", { op: "lista", sesion: chat().sesion });
      lista.replaceChildren();
      const items = (r.lista || []).slice().reverse();
      if (!items.length) { lista.append(node("div", "Sin descargas en la bitácora", "muted")); return; }
      items.forEach((d) => {
        const b = node("button", "", "fila");
        b.type = "button";
        b.append(node("span", (d.estado === "procesando" ? "… " : d.estado === "completado" ? "✓ " : "! ") + d.op + " " + (d.archivos || 0) + " archivos · " + d.id, "fila-nom"));
        b.addEventListener("click", async () => {
          const v = await window.RIU_ACCION("descargas", { op: "ver", id: d.id, sesion: chat().sesion });
          q("#motor-detalle").textContent = JSON.stringify(v, null, 1).slice(0, 4000);
        });
        lista.append(b);
      });
    } catch (e) { lista.replaceChildren(node("div", "GAP " + e.message, "muted")); }
  });
  const cargarArchivos = async (destino = "#va-lista") => {
    const lista = q(destino);
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await window.RIU_ACCION("archivos", { sesion: chat().sesion, ...window.RIU_DESTINO_ARCHIVOS() });  // lista del objetivo actual (chat/constitucion/proyecto seleccionado), no siempre del chat
      lista.replaceChildren();
      for (const nombre of r.archivos || []) {
        const fil = node("div", "", "va-item");
        const t = node("button", "", "toggle" + (chatA().anclados.has(nombre) ? " on" : ""));
        t.type = "button"; t.title = "Encender = anclar al chat, apagar = quitar";
        t.addEventListener("click", () => {
          const enc = !chatA().anclados.has(nombre);
          enc ? chatA().anclados.add(nombre) : chatA().anclados.delete(nombre);
          t.classList.toggle("on", enc);
          pintarAnclados(); guardar();
        });
        const nom = node("span", nombre, "fila-nom");
        const xr = node("button", "X-Ray", "mini");
        xr.type = "button"; xr.title = "Auditoría forense del archivo";
        xr.addEventListener("click", async () => {
          xr.disabled = true;
          try {
            const r2 = await window.RIU_ACCION("xray", { nombre, sesion: chat().sesion });
            cerrarHojas();
            const c = chat();
            c.hist.append(burbuja("X-RAY " + (r2.nombre || nombre) + "\n" + (r2.estructura || "") +
              "\nURLs: " + (r2.urls || []).join(", ") + "\nMAPA:\n" + (r2.mapa_mental || "") +
              "\nFLUJO: " + (r2.microflujo || "") + "\n" + (r2.resumen_goals || "")));
            abajo(c);
          } catch (err) { tell(err.message); }
        });
        fil.append(nom, t, xr);
        lista.append(fil);
      }
      if (!(r.archivos || []).length) lista.append(node("div", "No hay archivos subidos en este chat", "muted"));
    } catch (err) { lista.replaceChildren(node("div", err.message, "item message error")); }
  };

  return { cargarArchivos };
}
