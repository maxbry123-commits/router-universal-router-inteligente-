// auto-hist-hook.js — dispara recuperación automática al cargar si el chat está vacío.
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    const btn = document.getElementById("btn-recuperar-hist");
    if (!btn) return;
    const chats = document.querySelectorAll(".chat-history");
    const vacio = [...chats].every(h => !h.textContent.trim());
    if (vacio && chats.length) {
      console.log("auto-hist: chat vacío, disparando recuperación");
      btn.click();
    }
  }, 1200);
});
