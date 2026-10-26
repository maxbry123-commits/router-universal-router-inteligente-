// selector-modelos.js — un solo selector guarda TODOS los selectores de modelo (NVIDIA, Groq, Team qwen, Team 5 MVP, Ask cónsil…) en una ventana.
// Fuera queda el indicador con el selector encendido y el modelo que responde (texto de .sel-resp-global, lo escribe chat-selectores.js).
// No cambia el cableado: los botones ON/OFF, ⓘ y las hojas de cada selector siguen siendo los mismos nodos, solo se mudan a la ventana.
const ICONO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/></svg>';
function montar() {
  const sec = document.getElementById("selectores"), composer = document.getElementById("composer");
  if (!sec || !composer || document.getElementById("sh-selectores")) return !!document.getElementById("sh-selectores");
  const hoja = document.createElement("div");
  hoja.id = "sh-selectores"; hoja.className = "sheet"; hoja.hidden = true; hoja.setAttribute("role", "dialog"); hoja.setAttribute("aria-modal", "true"); hoja.setAttribute("aria-label", "Selector de modelos");
  hoja.innerHTML = '<div class="va-caja"><div class="row va-head"><strong>Selector de modelos</strong><button type="button" class="secondary sh-cerrar" aria-label="Cerrar">✕</button></div></div>';
  hoja.querySelector(".va-caja").append(sec);
  document.body.append(hoja);
  const btn = document.createElement("button");
  btn.type = "button"; btn.id = "btn-selector-modelos"; btn.className = "pill sel-indicador"; btn.setAttribute("aria-haspopup", "dialog"); btn.setAttribute("aria-controls", "sh-selectores");
  btn.innerHTML = ICONO + '<span class="sel-ind-txt"></span><span class="sel-ind-flecha" aria-hidden="true">⌄</span>';
  composer.prepend(btn);  // dentro de la caja de escritura: queda siempre a la vista con ella
  const txt = btn.querySelector(".sel-ind-txt");
  const pintar = () => {
    const g = sec.querySelector(".sel-resp-global"), t = (g && g.textContent.trim()) || "Selector de modelos";
    const m = t.match(/^Ningún selector encendido: responde (.+?)(?: \(por defecto[^)]*\))?$/), r = t.match(/^Responde: (.+)$/);
    txt.textContent = m ? "Modelo: " + m[1] + " · por defecto" : r ? r[1] : t; btn.title = t + " — tocar para cambiar"; btn.setAttribute("aria-label", "Selector de modelos: " + t);
    btn.classList.toggle("on", !!(g && g.classList.contains("on")));
  };
  const abrir = () => { hoja.hidden = false; btn.setAttribute("aria-expanded", "true"); const f = hoja.querySelector(".sel-on, button"); if (f) f.focus(); };
  const cerrar = () => { if (hoja.hidden) return; hoja.hidden = true; btn.setAttribute("aria-expanded", "false"); btn.focus(); };
  btn.addEventListener("click", abrir);
  hoja.addEventListener("click", (e) => {
    if (e.target === hoja || e.target.closest(".sh-cerrar")) { cerrar(); return; }
    const pill = e.target.closest(".sel-pill");  // la lista de cada selector es otra ventana: se cierra esta para que no quede debajo
    if (pill && (pill.dataset.sheet || pill.id === "sel-groq")) { hoja.hidden = true; btn.setAttribute("aria-expanded", "false"); }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(); });
  window.addEventListener("riu:selector-activo", () => setTimeout(pintar, 0));
  window.addEventListener("riu:fichas", () => setTimeout(pintar, 0));
  new MutationObserver(pintar).observe(sec, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  pintar();
  window.RIU_SELECTOR_MODELOS = { abrir, cerrar, pintar };
  return true;
}
let intentos = 0;
const esperar = () => { if (montar() || ++intentos > 100) return; setTimeout(esperar, 100); };
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", esperar); else esperar();
