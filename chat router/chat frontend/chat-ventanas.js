// chat-ventanas.js — comportamiento comun de las ventanas (hojas) del chat. Archivo propio.
// 1) tocar fuera de la ventana la cierra  2) Escape la cierra  3) deslizar hacia abajo desde la cabecera la cierra (celular)
// El sistema de anclaje queda como era: este archivo no lo toca.
export function conectarVentanas({ root }) {
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
}
