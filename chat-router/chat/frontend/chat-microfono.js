// chat-microfono.js — boton de microfono del input (archivo propio). Dicta por voz en #message con el
// reconocimiento de voz del navegador. NO MOCK: si el navegador no lo trae, el boton queda bloqueado y lo avisa.
// No envia nada solo: el texto queda en el input para que el Director lo revise y lo mande.
const ICONO = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>';
export function conectarMicrofono({ q, tell }) {
  const caja = q("#message"), barra = q(".composer-bar");
  if (!caja || !barra || q("#btn-microfono")) return;
  const b = document.createElement("button");
  b.type = "button"; b.id = "btn-microfono"; b.className = "secondary btn-microfono";
  b.title = "Dictar por voz"; b.setAttribute("aria-label", "Dictar por voz"); b.setAttribute("aria-pressed", "false");
  b.innerHTML = ICONO;
  barra.insertBefore(b, q("#btn-copiar-input") || barra.querySelector(".action"));
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Rec) { b.classList.add("bloq"); b.addEventListener("click", () => tell("Este navegador no trae dictado por voz. Prueba con Chrome.")); return; }
  let rec = null, base = "", activo = false;
  const parar = () => { activo = false; b.classList.remove("on"); b.setAttribute("aria-pressed", "false"); try { rec && rec.stop(); } catch (e) {} };
  b.addEventListener("click", () => {
    if (activo) { parar(); tell(""); return; }
    rec = new Rec();
    rec.lang = (navigator.language || "").toLowerCase().startsWith("es") ? navigator.language : "es-ES";
    rec.interimResults = true; rec.continuous = true;
    base = caja.value ? caja.value.replace(/\s*$/, " ") : "";
    rec.onresult = (ev) => {
      let txt = "";
      for (let i = 0; i < ev.results.length; i++) txt += ev.results[i][0].transcript;
      caja.value = base + txt; caja.dispatchEvent(new Event("input", { bubbles: true }));
    };
    rec.onerror = (ev) => { tell(ev.error === "not-allowed" ? "Permiso de micrófono negado" : "Micrófono: " + ev.error); parar(); };
    rec.onend = () => { if (activo) parar(); };
    try { rec.start(); activo = true; b.classList.add("on"); b.setAttribute("aria-pressed", "true"); tell("Escuchando… toca el micrófono otra vez para parar"); }
    catch (e) { tell(e.message); parar(); }
  });
  q("#composer")?.addEventListener("submit", parar);
}
