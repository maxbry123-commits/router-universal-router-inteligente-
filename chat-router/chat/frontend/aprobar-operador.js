// aprobar-operador.js — quien aprueba una tarea SWE se identifica con SU operador y SU token individual (cabeceras x-operador / x-operator-token del backend).
// Se piden en un dialogo al pulsar «Aprobar y continuar», viajan SOLO como cabeceras de esa peticion y se descartan: nunca a storage, ni a consola, ni al cuerpo.
const SOLO_CABECERA = /^[\x20-\x7E]+$/;  // ASCII imprimible: otra cosa haria fallar o inyectaria en la cabecera
const el = (doc, tag, cls, txt) => { const e = doc.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const css = (doc, nombre) => { try { const id = "css-" + nombre; if (doc.getElementById(id)) return; const l = doc.createElement("link"); l.id = id; l.rel = "stylesheet"; l.href = "/chat/ui/" + nombre + ".css"; doc.head.append(l); } catch (e) {} };
let abierto = null;
export function pedirOperadorYToken(doc = document) {
  if (abierto) return abierto;
  css(doc, "ventanas-comun"); css(doc, "acceso-clave");
  abierto = new Promise((resolve) => {
    const previo = doc.activeElement;
    const fondo = el(doc, "div", "ac-fondo ap-operador"), caja = el(doc, "div", "ac-caja");
    fondo.setAttribute("role", "dialog"); fondo.setAttribute("aria-modal", "true"); fondo.setAttribute("aria-labelledby", "ap-op-titulo");
    const titulo = el(doc, "strong", "", "Aprobar y continuar"); titulo.id = "ap-op-titulo";
    const ayuda = el(doc, "p", "muted", "Identifícate con tu operador y tu token individual. Solo se envían con esta aprobación y no se guardan.");
    const op = el(doc, "input", "vn-in"), tk = el(doc, "input", "vn-in");
    op.type = "text"; op.autocomplete = "off"; op.id = "ap-op-operador"; op.placeholder = "Operador"; op.setAttribute("aria-label", "Operador"); op.setAttribute("autocapitalize", "off"); op.setAttribute("spellcheck", "false");
    tk.type = "password"; tk.autocomplete = "off"; tk.id = "ap-op-token"; tk.placeholder = "Token de operador"; tk.setAttribute("aria-label", "Token de operador");
    const error = el(doc, "div", "vn-estado"); error.setAttribute("role", "alert");
    const fin = (v) => { op.value = ""; tk.value = ""; fondo.remove(); abierto = null; try { if (previo && previo.focus) previo.focus(); } catch (e) {} resolve(v); };
    const aprobar = el(doc, "button", "mini", "Aprobar"), cancelar = el(doc, "button", "mini", "Cancelar");
    aprobar.type = "button"; cancelar.type = "button";
    aprobar.addEventListener("click", () => {
      const o = op.value.trim(), t = tk.value;
      if (!o || !t) { error.textContent = "Escribe el operador y el token."; (o ? tk : op).focus(); return; }
      if (!SOLO_CABECERA.test(o) || !SOLO_CABECERA.test(t)) { error.textContent = "El operador y el token solo admiten caracteres ASCII visibles, sin saltos de línea."; return; }
      fin({ operador: o, token: t });
    });
    cancelar.addEventListener("click", () => fin(null));
    const enter = (e) => { if (e.key === "Enter") { e.preventDefault(); aprobar.click(); } };
    op.addEventListener("keydown", enter); tk.addEventListener("keydown", enter);
    fondo.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { e.preventDefault(); cancelar.click(); return; }
      if (e.key === "Tab") {  // el foco no sale del dialogo
        const orden = [op, tk, aprobar, cancelar], i = orden.indexOf(doc.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); cancelar.focus(); } else if (!e.shiftKey && i === orden.length - 1) { e.preventDefault(); op.focus(); }
      }
    });
    const fila = el(doc, "div", "ac-acc"); fila.append(aprobar, cancelar);
    caja.append(titulo, ayuda, op, tk, fila, error); fondo.append(caja); doc.body.append(fondo); op.focus();
  });
  return abierto;
}
// explica en claro el rechazo del servidor; nunca repite lo que se escribio
export function mensajeAprobacion(e) {
  const s = e && e.status;
  if (s === 503) return "Aprobación no configurada en el servidor: falta definir RIU_SWE_APROBADORES (operador:sha256 del token de cada persona). Pídele al administrador que la configure.";
  if (s === 403 || s === 401) return "Aprobación rechazada: operador o token incorrecto. Revisa tu operador y tu token individual y vuelve a pulsar «Aprobar y continuar».";
  return null;
}
export const mensajeExito = (operador) => "Aprobación registrada" + (operador ? " por " + operador : "") + ": la tarea continúa. Aprobado desde la interfaz con operador y token individual.";
