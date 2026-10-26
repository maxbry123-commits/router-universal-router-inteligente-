// chat-medios.js — [[imagen:URL]] / [[video:URL]] / [[audio:URL]] que devuelve la ficha -> el medio dentro de la burbuja (solo https o audio data:)
// Módulo aparte: no toca el composer ni los handlers del chat; solo lee las burbujas del bot ya pintadas.
const MEDIO = /\[\[(imagen|video|audio):((?:https:\/\/|data:audio\/)[^\]\s]+)\]\]/g, HAY_MEDIO = /\[\[(imagen|video|audio):/;
function medios() {
  document.querySelectorAll(".chat-history .message:not(.user):not(.pending) .txt:not([data-medios])").forEach((t) => {
    t.dataset.medios = "1"; if (!HAY_MEDIO.test(t.textContent)) return;
    const lista = [...t.textContent.matchAll(MEDIO)]; t.textContent = t.textContent.replace(MEDIO, "").trim();
    lista.forEach(([, tipo, url]) => {
      const m = document.createElement(tipo === "imagen" ? "img" : tipo); m.src = url; m.className = "riu-medio";
      if (tipo === "imagen") { m.alt = "Imagen generada"; m.loading = "lazy"; } else m.controls = true;
      const a = document.createElement("a"); a.href = url; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Abrir " + tipo; a.className = "riu-medio-enlace";
      t.after(m); m.after(a);
    });
  });
}
new MutationObserver(medios).observe(document.body, { childList: true, subtree: true });
medios();
