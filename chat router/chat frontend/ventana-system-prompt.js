// ventana-system-prompt.js — ventana aparte "System prompt": prompt simple guardable (sin validación). Va en la entrada del modelo
// con o sin Constitución; la Constitución (contrato + validación de la salida) vive en ventana-constitucion.js.
import { el, crearVentana, abrirVentana, agregarPill } from "./ventanas-comun.js";
import { dameSP, seccionSystemPrompt } from "./sentinela.js";
export function montarSystemPrompt({ root, q, tell }) {
  if (root.dataset.sp) return; root.dataset.sp = "1";
  const { sheet, caja } = crearVentana(root, { id: "ventana-system-prompt", titulo: "System prompt" });
  const activo = () => { const v = dameSP(); return v.lista.find((x) => x.id === v.activo) || null; };
  const pill = agregarPill(q, "pill-system-prompt", "system prompt ⌄", () => { pintar(); abrirVentana(root, sheet); });
  const marcar = () => { const a = activo(); pill.classList.toggle("on", !!a); pill.title = a ? "System prompt activo: " + a.nombre : "Sin system prompt"; };
  const cuerpo = el("div", "con-cuerpo"); caja.append(cuerpo);
  function pintar() { cuerpo.replaceChildren(); seccionSystemPrompt(cuerpo, tell, marcar); marcar(); }
  marcar();
}
