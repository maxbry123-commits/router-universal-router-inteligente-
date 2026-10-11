// chat-ventanas.js — comportamiento comun de las ventanas (hojas) del chat. Archivo propio.
// 1) tocar fuera de la ventana la cierra  2) Escape la cierra  3) deslizar hacia abajo desde la cabecera la cierra (celular)
// 4) ANCLAJE EN UNA SOLA VENTANA: la pastilla "ancla" y el boton ⚓ del input abren la MISMA ventana, que junta todo
//    (enlaces, anclado ahora, instrucciones fijas, proyectos, handoffs, Mi handoff y archivos) con un titulo por seccion.
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
      y0 = (e.target.closest(".va-head") && caja.scrollTop <= 0) ? y : null;  // solo desde la cabecera y con la ventana arriba: deslizar el contenido no mueve la ventana
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
  const va = q("#ventana-ancla .va-caja"), sh = q("#sh-ancla .va-caja"), pill = q("#ancla"), btn = q("#btn-ancla");
  if (!va || !sh || !pill || !btn || va.dataset.unido) return;
  va.dataset.unido = "1";
  const titulo = (txt) => { const t = document.createElement("div"); t.className = "anc-sec"; t.textContent = txt; return t; };
  const antesDe = (el, txt) => { if (el && el.parentNode === va) va.insertBefore(titulo(txt), el); else if (el) el.before(titulo(txt)); };
  const fila = (sel) => { const e = q(sel); return e ? (e.closest("#ventana-ancla .va-caja > *") || e) : null; };
  antesDe(fila("#anc-pegar"), "Enlaces y raíces");
  antesDe(fila("#anc-resumen"), "Anclado ahora");
  antesDe(fila("#anc-instr"), "Instrucciones fijas");
  antesDe(fila("#anc-proy-nombre"), "Proyectos de este chat");
  const archivos = fila("#anc-subir");
  const tHand = titulo("Handoffs del proyecto y Mi handoff");
  const bloque = [...sh.children].filter((n) => !n.classList.contains("va-head"));
  if (archivos) { va.insertBefore(tHand, archivos); bloque.forEach((n) => va.insertBefore(n, archivos)); antesDe(archivos, "Archivos"); }
  else { va.append(tHand, ...bloque); }
  const tit = va.querySelector(".va-head strong"); if (tit) tit.textContent = "Anclaje";
  let ocupado = false;
  const mostrar = () => { q("#sh-ancla").hidden = true; q("#ventana-ancla").hidden = false; };
  pill.addEventListener("click", () => { if (ocupado) return; ocupado = true; btn.click(); ocupado = false; mostrar(); });  // carga tambien archivos
  btn.addEventListener("click", () => {
    if (ocupado || q("#ventana-ancla").hidden) return;
    ocupado = true; pill.click(); ocupado = false; mostrar();  // carga tambien handoffs y Mi handoff
  });
  va.querySelectorAll("button.mini").forEach((b) => {
    if (b.textContent.trim() === "Handoffs…") b.addEventListener("click", () => setTimeout(() => tHand.scrollIntoView({ behavior: "smooth", block: "start" }), 60));
  });
}
