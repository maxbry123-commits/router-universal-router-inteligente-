// ventana-constitucion.js — ventana "Constitución sentinela": constitución propia + la oficial YAIWES (solo lectura), y las mismas anclas
// (texto, URL, archivos) que el anclaje del chat. Encendida, viaja con cada mensaje (ver contexto.js).
import { escribir, KEYS } from "./almacen.js";
import { dameCon, refsCompartidas } from "./contexto.js";
import { el, boton, crearVentana, abrirVentana, agregarPill } from "./ventanas-comun.js";
const URL_OFICIAL = "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json";
export function montarConstitucion({ root, q, tell }) {
  if (root.dataset.con) return; root.dataset.con = "1";
  const { sheet, caja } = crearVentana(root, { id: "ventana-constitucion", titulo: "Constitución sentinela", css: "ventana-constitucion" });
  const pill = agregarPill(q, "pill-constitucion", "constitución ⌄", () => { pintar(); abrirVentana(root, sheet); });
  const cuerpo = el("div", "con-cuerpo"); caja.append(cuerpo);
  const poner = (fn) => { const c = dameCon(); fn(c); escribir(KEYS.constitucion, c); };
  const marcar = () => pill.classList.toggle("on", !!dameCon().encendida);
  async function oficial() {
    let t = null; try { t = sessionStorage.getItem("riu_const_oficial"); } catch (e) {}
    if (t) return t;
    const r = await fetch(URL_OFICIAL); if (!r.ok) throw new Error("HTTP " + r.status);
    t = await r.text(); try { sessionStorage.setItem("riu_const_oficial", t); } catch (e) {} return t;
  }
  function pintar() {
    const c = dameCon(); cuerpo.replaceChildren(); marcar();
    const enc = boton(c.encendida ? "Encendida" : "Apagada · encender", "toggle" + (c.encendida ? " on" : ""), () => { poner((x) => { x.encendida = !x.encendida; }); pintar(); tell(c.encendida ? "Constitución apagada" : "Constitución encendida"); });
    enc.setAttribute("aria-pressed", String(!!c.encendida));
    cuerpo.append(enc, el("div", "vn-estado", "Encendida, su texto y sus anclas viajan con cada mensaje del chat."));
    const ta = el("textarea", "vn-ta"); ta.value = c.texto || ""; ta.placeholder = "Mi constitución sentinela: reglas que la IA debe respetar siempre…"; ta.setAttribute("aria-label", "Mi constitución");
    ta.addEventListener("input", () => poner((x) => { x.texto = ta.value.slice(0, 12000); }));  // guarda al teclear: nada se pierde si envia sin soltar el campo
    cuerpo.append(el("div", "vn-t", "Mi constitución sentinela"), ta);
    const of = boton(c.oficial ? "Incluir la oficial YAIWES: sí" : "Incluir la oficial YAIWES: no", "toggle" + (c.oficial ? " on" : ""), async () => {
      if (!c.oficial) { try { await oficial(); } catch (e) { tell("No pude leer la constitución oficial: " + e.message); return; } }
      poner((x) => { x.oficial = !x.oficial; }); pintar();
    });
    of.setAttribute("aria-pressed", String(!!c.oficial));
    const det = el("details", "con-oficial"), res = el("summary", "", "Ver la constitución oficial (solo lectura)"), pre = el("pre", "con-pre", "Cargando…");
    det.append(res, pre); let cargada = false;
    det.addEventListener("toggle", async () => { if (!det.open || cargada) return; cargada = true; try { pre.textContent = await oficial(); } catch (e) { pre.textContent = "No pude leerla (" + e.message + ")."; } });
    cuerpo.append(el("div", "vn-t", "Constitución oficial"), of, det);
    cuerpo.append(el("div", "vn-t", "Anclas de la constitución"), el("div", "vn-estado", (c.items || []).length + " anclado(s). Es la misma ventana de anclaje: enlaces, handoffs, archivos compartidos, proyectos."), boton("Abrir el anclaje de la constitución", "mini", () => { if (window.RIU_ANCLA_ABRIR) window.RIU_ANCLA_ABRIR("constitucion"); else tell("El anclaje no está disponible"); }));
    const rc = refsCompartidas("constitucion");
    cuerpo.append(el("div", "vn-t", "Claves compartidas con la constitución"), el("div", "vn-estado", rc.length ? rc.join(", ") + " (solo el nombre viaja; el valor nunca)" : "Ninguna. Se comparten desde la ventana de claves."));
  }
  const onAlm = () => { if (!root.isConnected) { window.removeEventListener("riu:almacen", onAlm); return; } marcar(); };
  window.addEventListener("riu:almacen", onAlm); marcar();
}
