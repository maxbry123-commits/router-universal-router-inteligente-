// chat-ventanas.js — comportamiento comun de las ventanas (hojas) del chat. Archivo propio.
// 1) tocar fuera de la ventana la cierra  2) Escape la cierra  3) deslizar hacia abajo desde la cabecera la cierra (celular)
// 4) UN SOLO ANCLAJE: el boton ⚓ del input abre una ventana con archivos, enlaces, handoffs del proyecto y Mi handoff.
//    Se quita la pastilla "ancla" repetida y el campo de enlace duplicado (los enlaces se pegan arriba, en la misma ventana).
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
      y0 = (e.target.closest(".va-head") || y - caja.getBoundingClientRect().top < 40) ? y : null;
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
  unirAnclaje(q);
}
function unirAnclaje(q) {
  const va = q("#ventana-ancla .va-caja"), sh = q("#sh-ancla .va-caja"), pill = q("#ancla"), btn = q("#btn-ancla");
  if (!va || !sh || !pill || !btn || va.dataset.unido) return;
  va.dataset.unido = "1";
  const t = document.createElement("div"); t.className = "mod-grupo-t"; t.textContent = "Handoffs del proyecto y Mi handoff";
  va.append(t);
  [...sh.children].forEach((n) => { if (!n.classList.contains("va-head")) va.append(n); });
  const enl = q("#ancla-enlace"); if (enl && enl.closest(".row")) enl.closest(".row").hidden = true;
  va.querySelectorAll("button.mini").forEach((b) => { if (b.textContent.trim() === "Handoffs…") b.hidden = true; });
  const tit = va.querySelector(".va-head strong"); if (tit) tit.textContent = "Anclar";
  pill.hidden = true;
  btn.addEventListener("click", () => {
    if (q("#ventana-ancla").hidden) return;
    pill.click();  // carga handoffs y Mi handoff en la misma ventana
    q("#sh-ancla").hidden = true; q("#ventana-ancla").hidden = false;
  });
}
