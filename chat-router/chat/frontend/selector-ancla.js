// selector-ancla.js — selector de ancla: handoffs con botón de encender + pegar enlace/handoff propio
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
import { leer, escribir } from "./almacen.js";
const K_HOFF="riu_handoff_borrador_v1";
export function montarSelectorAncla(ctx) {
  const { q, filaEncender, chat, burbuja, abajo, fila, cerrarHojas, chatA, pintarAnclados, guardar, tell } = ctx;
  // ---- selector de ancla: handoffs con boton de encender + pegar enlace/handoff propio ----
  const ANCLAS = [
    ["chat-router", "plugins/chat-router/", "handoff del proyecto workflow Loops code Yaiwes"],
    ["skill", "SKILL.md", "handoff del skill maestro Maxbry UI FROMTED"],
    ["preview", "Preview Vercel", "handoff del panel-chat de prueba"],
  ];
  const pintarAnclas = () => {
    const lista = q("#sh-ancla-lista");
    lista.replaceChildren();
    for (const [k, t, d] of ANCLAS) {
      lista.append(filaEncender(t, d, "handoff:" + k, async (enc) => {
        if (!enc || window.RIU_OBJETIVO_ANCLA) return;
        try {  // muestra en el chat lo que quedo anclado
          const r = await window.RIU_ACCION("handoff", { fuente: k, sesion: chat().sesion });
          const c = chat();
          c.hist.append(burbuja("ANCLADO " + k + ":\n" + JSON.stringify(r.handoff || r, null, 1)));
          abajo(c);
        } catch (err) { tell(err.message); }
      }));
    }
    lista.append(fila("Auditor de code del repo", "ubica los archivos de code del proyecto", false, async (ev) => {
      ev.currentTarget.disabled = true;
      try {
        const r = await window.RIU_ACCION("auditor_code", { sesion: chat().sesion });
        cerrarHojas();
        const c = chat();
        c.hist.append(burbuja("AUDITOR CODE — " + r.total + " archivos:\n" + (r.carpetas || []).join("\n")));
        abajo(c);
      } catch (err) { tell(err.message); }
    }));
  };
  // mi handoff: texto propio guardado en memoria, editable; va interno con cada mensaje
  const cargarMiHandoff = async () => {
    const key=chatA().sesion, saved=leer(K_HOFF,{})[key]||"";
    try {
      const r=await window.RIU_ACCION("handoff_texto",{sesion:key});
      q("#mi-handoff").value=r.texto||saved;
      if(r.texto){const l=leer(K_HOFF,{});l[key]=r.texto;escribir(K_HOFF,l);}
      q("#mh-estado").textContent=r.encendido?"encendido":"apagado";
    }catch(err){
      q("#mi-handoff").value=saved;
      q("#mh-estado").textContent="sin confirmar";
    }
  };
  q("#mh-guardar").addEventListener("click", async () => {
    try {
      const texto=q("#mi-handoff").value,key=chatA().sesion,all=leer(K_HOFF,{});
      all[key]=texto;if(!escribir(K_HOFF,all))throw Error("No se guardó el borrador");
      const r=await window.RIU_ACCION("handoff_texto",{sesion:key,texto});
      q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
      if (r.encendido) {
        const c = chat();
        c.hist.append(burbuja("MI HANDOFF anclado:\n" + texto));
        abajo(c);
      }
      tell("yaiwes.md " + (r.encendido ? "guardado y encendido" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#mh-apagar").addEventListener("click", async () => {
    try {
      const key=chatA().sesion,all=leer(K_HOFF,{});
      all[key]=q("#mi-handoff").value;
      if(!escribir(K_HOFF,all))throw Error("No se pudo conservar el handoff");
      await window.RIU_ACCION("handoff_texto",{sesion:key,texto:""});
      q("#mh-estado").textContent="apagado";
      tell("yaiwes.md apagado");
    } catch (err) { tell(err.message); }
  });
  q("#ancla-enlace-on").addEventListener("click", () => {
    const v = (q("#ancla-enlace").value || "").trim();
    if (!v) { tell("Pega primero un enlace o handoff"); return; }
    chatA().anclados.add("enlace:" + v);
    q("#ancla-enlace").value = "";
    pintarAnclados(); guardar();
    tell("Enlace anclado al chat");
  });

  return { pintarAnclas, cargarMiHandoff };
}
