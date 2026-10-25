// La salida es el hueco que queda encima de la caja de escritura.
// No se multiplica ni se empuja la página: eso dejaba el texto del modelo fuera de la pantalla.
function soltar() {
  document.documentElement.classList.remove("salida-x4");
  document.documentElement.style.removeProperty("--salida-alto");
}
function alFinal() {
  const h = document.querySelector("#histories .chat-history:not([hidden])");
  if (h) h.scrollTop = h.scrollHeight;
}
function vigilar() {
  const h = document.querySelector("#histories .chat-history");
  if (!h) return;
  new MutationObserver(() => requestAnimationFrame(alFinal)).observe(h, { childList: true });
}
function iniciar() {
  soltar();
  vigilar();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
else iniciar();
