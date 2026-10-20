// apariencia-extra.js — secciones 8, 9 y 10 de la ventana Apariencia: orden del menú (V07 "organización táctil"), bloqueo con PIN (RUI 10)
// e inventario de los 22 componentes RUI (V07 "Rare UI"). Archivo propio; lo llama panel-apariencia.js.
import { montarAccesoConfig } from "./acceso-clave.js";
import { pinActivo, pinDisponible, fijarPin, verificarPin, quitarPin, crearOtp, bloquear } from "./bloqueo-pin.js";
const VISTAS = [["chat", "Chat"], ["archivos", "Archivos"], ["seguimiento", "Seguimiento"], ["canvas", "Canvas"], ["connectors", "Conectores"], ["templates", "Plantillas"], ["engineering", "Ingeniería"], ["apariencia", "Apariencia"]];
const GRIP = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/><circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/></svg>';
const RUI = [
  ["01", "Folder", "Carpeta que se abre en «Archivos en memoria» cuando está vacío"], ["02", "Bounce sidebar", "Rebote al elegir una vista del menú"],
  ["03", "Hook sidebar", "Riel punteado del que cuelga el indicador del menú"], ["04", "Family drawer", "Las ventanas suben con rebote y se cierran deslizando"],
  ["05", "Proximity sidebar", "El menú se acerca al cursor (escritorio)"], ["06", "Duration picker", "Duración del aviso (sección 6)"],
  ["07", "Fluid orb", "Punto que late mientras llega la respuesta"], ["08", "Scroll progress", "Barra de lectura y botón «bajar al final»"],
  ["09", "Code block", "Bloques de código con botón copiar"], ["10", "OTP input", "PIN de 4 dígitos para bloquear el chat (sección 9)"],
  ["11", "Gravity letters", "Bienvenida del chat vacío con accesos rápidos"], ["12", "GitHub activity", "Actividad de 28 días en la ventana «Más»"],
  ["13", "Emoji reaction", "Reacciones en cada respuesta"], ["14", "Notification bell", "Campana con el historial de avisos"],
  ["15", "Step player", "Botón «Recorrer» en los diagramas de los selectores"], ["16", "Grid reveal", "Los iconos de esta ventana aparecen en cascada"],
  ["17", "Gooey nav", "Indicador que se desliza entre las vistas del menú"], ["18", "Delete button", "Cerrar un chat con confirmación"],
  ["19", "Animated counter", "Contador de anclados en el botón del ancla"], ["20", "Matrix orb", "Orbe de estado de la conexión"],
  ["21", "Task list", "Cola del motor como lista de tareas con tilde"], ["22", "Voice note", "Micrófono de dictado que late mientras escucha"],
];
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

const BASE_DOC = "https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/";
const DOCS = [["README del frontend", BASE_DOC + "README.md"], ["Handoff del frontend", BASE_DOC + "HANDOFF-FRONTEND.md"]];
function documentacion(root, api) {  // README y handoff al alcance del chat: enlaces y botón para anclarlos al chat activo
  const caja = root.querySelector("#ap-docs"); if (!caja) return;
  const ul = el("ul", "ap-docs");
  DOCS.forEach(([n, u]) => { const li = el("li"), a = el("a", "", n); a.href = u; a.target = "_blank"; a.rel = "noopener"; li.append(a); ul.append(li); });
  const b = el("button", "mini", "Anclar README y handoff al chat"); b.type = "button";
  b.addEventListener("click", () => {
    try {
      const k = "riu_chats_v1", arr = JSON.parse(localStorage.getItem(k) || "[]");
      if (!Array.isArray(arr) || !arr.length) { api.avisa("Abre el chat una vez para poder anclar"); return; }
      const i = Math.min(Math.max(Number(localStorage.getItem("riu_chat_activo")) || 0, 0), arr.length - 1), ya = new Set(arr[i].anclados || []);
      DOCS.forEach(([, u]) => ya.add("enlace:" + u)); arr[i].anclados = [...ya]; localStorage.setItem(k, JSON.stringify(arr)); api.avisa("README y handoff anclados al chat activo");
    } catch (e) { api.avisa("No se pudo anclar: " + e.message); }
  });
  caja.append(ul, b);
}
export function montarExtra(root, api) {
  const q = (s) => root.querySelector(s);
  const etq = Object.fromEntries(VISTAS), base = VISTAS.map((v) => v[0]);
  // ---- 8 · orden del menú ----
  const lista = q("#ap-orden");
  const orden = () => { const ya = (api.est().orden || []).filter((v) => base.includes(v)); return [...ya, ...base.filter((v) => !ya.includes(v))]; };
  const fijarOrden = (o) => { api.est().orden = o; api.guardar(); window.dispatchEvent(new Event("resize")); pintarOrden(); };
  const mover = (a, b) => { const o = orden(); if (b < 0 || b >= o.length || a === b) return; const [x] = o.splice(a, 1); o.splice(b, 0, x); fijarOrden(o); };
  const arrastrar = (g, li) => g.addEventListener("pointerdown", (e) => {
    e.preventDefault(); g.setPointerCapture(e.pointerId);
    const filas = [...lista.children], desde = filas.indexOf(li), y0 = e.clientY;
    const mid = filas.map((f) => { const r = f.getBoundingClientRect(); return r.top + r.height / 2; });
    let hasta = desde; li.classList.add("arrastrando");
    const mueve = (ev) => { const dy = ev.clientY - y0; li.style.transform = "translateY(" + dy + "px)"; const yc = mid[desde] + dy; hasta = mid.reduce((m, v, i) => (Math.abs(v - yc) < Math.abs(mid[m] - yc) ? i : m), 0); };
    const suelta = () => { g.removeEventListener("pointermove", mueve); g.removeEventListener("pointerup", suelta); g.removeEventListener("pointercancel", suelta); li.style.transform = ""; li.classList.remove("arrastrando"); if (hasta !== desde) mover(desde, hasta); };
    g.addEventListener("pointermove", mueve); g.addEventListener("pointerup", suelta); g.addEventListener("pointercancel", suelta);
  });
  const pintarOrden = () => {
    if (!lista) return; lista.replaceChildren();
    orden().forEach((id, i, arr) => {
      const li = el("li", "ap-orden-fila"), g = el("button", "ap-grip"); g.type = "button"; g.innerHTML = GRIP; g.title = "Mantén pulsado y arrastra para mover"; g.setAttribute("aria-label", "Arrastrar " + etq[id]);
      const up = el("button", "mini", "▲"), dn = el("button", "mini", "▼"); up.type = dn.type = "button"; up.setAttribute("aria-label", "Subir " + etq[id]); dn.setAttribute("aria-label", "Bajar " + etq[id]);
      up.disabled = i === 0; dn.disabled = i === arr.length - 1;
      up.addEventListener("click", () => mover(i, i - 1)); dn.addEventListener("click", () => mover(i, i + 1));
      li.append(g, el("span", "", etq[id]), up, dn); lista.append(li); arrastrar(g, li);
    });
  };
  const reset = q("#ap-orden-reset"); if (reset) reset.addEventListener("click", () => { delete api.est().orden; api.guardar(); window.dispatchEvent(new Event("resize")); pintarOrden(); api.avisa("Orden del menú restablecido"); });
  // ---- 9 · bloqueo con PIN ----
  const caja = q("#ap-pin");
  const pintarPin = () => {
    if (!caja) return; caja.replaceChildren();
    if (!pinDisponible()) { caja.append(el("p", "muted", "Este navegador no permite el bloqueo con PIN (hace falta una conexión segura).")); return; }
    const msg = el("p", "muted"); msg.setAttribute("role", "status");
    if (!pinActivo()) {
      const b = el("button", "mini", "Activar PIN"); b.type = "button";
      b.addEventListener("click", () => {
        caja.replaceChildren(el("p", "", "Elige un PIN de 4 dígitos"));
        let primero = null;
        const otp = crearOtp(4, async (pin) => {
          if (!primero) { primero = pin; otp.limpiar(); caja.firstChild.textContent = "Repítelo para confirmar"; return; }
          if (pin !== primero) { primero = null; otp.sacudir(); otp.limpiar(); caja.firstChild.textContent = "No coinciden. Elige un PIN de 4 dígitos"; return; }
          try { await fijarPin(pin); api.avisa("PIN activado"); } catch (e) { api.avisa(e.message); }
          pintarPin();
        });
        const cancel = el("button", "mini", "Cancelar"); cancel.type = "button"; cancel.addEventListener("click", pintarPin);
        caja.append(otp, cancel); otp.enfocar();
      });
      caja.append(b); return;
    }
    const ya = el("p", "", "El PIN está activo: el chat se bloquea al abrirlo.");
    const ahora = el("button", "mini", "Bloquear ahora"); ahora.type = "button"; ahora.addEventListener("click", bloquear);
    const quitar = el("button", "mini rojo", "Quitar PIN"); quitar.type = "button";
    quitar.addEventListener("click", () => {
      caja.replaceChildren(el("p", "", "Escribe tu PIN para quitarlo"));
      const otp = crearOtp(4, async (pin) => { const r = await verificarPin(pin); if (r.ok) { quitarPin(); api.avisa("PIN quitado"); pintarPin(); } else { otp.sacudir(); otp.limpiar(); caja.firstChild.textContent = r.espera ? "Espera " + r.espera + " s" : "PIN incorrecto"; } });
      const cancel = el("button", "mini", "Cancelar"); cancel.type = "button"; cancel.addEventListener("click", pintarPin);
      caja.append(otp, cancel); otp.enfocar();
    });
    const fila = el("div", "ap-fila"); fila.append(ahora, quitar); caja.append(ya, fila, msg);
  };
  // ---- 10 · inventario RUI ----
  const rui = q("#ap-rui");
  if (rui) RUI.forEach(([n, nom, uso]) => { const li = el("li", ""); li.append(el("b", "", n), el("strong", "", nom), el("span", "muted", uso)); rui.append(li); });
  documentacion(root, api);
  montarAccesoConfig(root, api);
  return { pintar: () => { pintarOrden(); pintarPin(); } };
}
