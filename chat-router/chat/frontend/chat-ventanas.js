import { cargarCss } from "./ventanas-comun.js";
// chat-ventanas.js — comportamiento comun de las ventanas (hojas) del chat. Archivo propio.
// 1) tocar fuera de la ventana la cierra  2) Escape la cierra  3) deslizar hacia abajo desde la cabecera la cierra (celular)
// 4) ANCLAJE EN UNA SOLA VENTANA: la pastilla "ancla" y el boton ⚓ del input abren la MISMA ventana, que junta todo
//    (enlaces, anclado ahora, instrucciones fijas, proyectos, handoffs, yaiwes.md y archivos) con un titulo por seccion.
//    No se borra ni se oculta nada: solo se mueve la ventana de handoffs dentro de la de anclaje.
export function conectarVentanas({ root, q }) {
  const hojas = () => [...root.querySelectorAll(".sheet")];
  hojas().forEach((s) => s.addEventListener("click", (e) => { if (e.target === s) s.hidden = true; }));
  if (window.__riuEsc) document.removeEventListener("keydown", window.__riuEsc);
  window.__riuEsc = (e) => { if (e.key === "Escape") hojas().forEach((s) => { s.hidden = true; }); };
  document.addEventListener("keydown", window.__riuEsc);
  hojas().forEach((s) => {
    const caja = s.querySelector(".va-caja"); if (!caja) return;
    let y0 = null;
    caja.addEventListener("touchstart", (e) => {
      const y = e.touches[0].clientY;
      y0 = e.target.closest(".va-head") ? y : null;  // se arrastra desde la cabecera (siempre visible arriba); el contenido se desliza normal
    }, { passive: true });
    caja.addEventListener("touchmove", (e) => {
      if (y0 === null) return; const d = e.touches[0].clientY - y0;
      caja.style.transform = d > 0 ? "translateY(" + d + "px)" : "";
    }, { passive: true });
    caja.addEventListener("touchend", (e) => {
      if (y0 === null) return; const d = e.changedTouches[0].clientY - y0;
      caja.style.transform = ""; y0 = null; if (d > 90) s.hidden = true;
    });
  });
  if (q) unirAnclaje(q);
}
function unirAnclaje(q) {
  // Un ÚNICO sheet nativo: ambos accesos apuntan a #ventana-ancla.
  // El contenido existente de #sh-ancla se conserva con sus IDs y handlers,
  // pero se presenta como sección plegable; no se monta otra ventana.
  const va = q("#ventana-ancla .va-caja");
  const sh = q("#sh-ancla .va-caja");
  const pill = q("#ancla");
  const btn = q("#btn-ancla");
  if (!va || !sh || !pill || !btn || va.dataset.unido) return;
  va.dataset.unido = "2";
  cargarCss("anclaje-compacto");
  const titulo = (txt) => { const t = document.createElement("div"); t.className = "anc-sec"; t.textContent = txt; return t; };
  const cab = va.querySelector(".va-head strong");
  if (cab) cab.textContent = "⚓ Anclaje";
  const fila = (sel) => { const e = q(sel); return e && (e.closest("#ventana-ancla .va-caja > *") || e); };
  [["#anc-pegar","Enlaces y raíces"],["#anc-resumen","Anclado ahora"],["#anc-instr","Instrucciones fijas"],["#anc-proy-nombre","Proyectos del chat"]].forEach(([sel,label]) => {
    const node = fila(sel); if (node && node.parentNode === va) node.before(titulo(label));
  });
  const legacy = [...sh.children].filter(n => !n.classList.contains("va-head"));
  const grupo = document.createElement("details");
  grupo.id = "ancla-handoffs";
  grupo.className = "ancla-grupo";
  const cabecera = document.createElement("summary");
  cabecera.textContent = "📌 Handoff permanente · enlaces y archivos";
  grupo.append(cabecera, ...legacy);
  const archivos = q("#anc-subir")?.closest(".row");
  if (archivos && archivos.parentElement === va) archivos.before(grupo);
  else va.append(grupo);
  // Se evita el bucle pill.click() ↔ btn.click() que abría/cerraba dos hojas.
  pill.dataset.sheet = "ventana-ancla";
  pill.setAttribute("aria-controls","ventana-ancla");
  btn.setAttribute("aria-controls","ventana-ancla");
  pill.setAttribute("aria-haspopup","dialog");
  btn.setAttribute("aria-haspopup","dialog");
  q("#sh-ancla").hidden = true;
  const handoff = q("#mi-handoff");
  if (handoff) handoff.setAttribute("aria-label","Handoff permanente");
}
