// chat-riu.js — componentes RUI (rare-ui, chat router/01-PLAN) llevados a JS simple, en archivo propio:
//  09 code-block: los bloques ``` de las respuestas se ven como codigo con boton copiar
//  08 scroll-progress: barra de avance de lectura + boton "bajar al final" cuando subes en una salida larga
// Solo frontend y con datos reales del chat: no inventa mensajes ni respuestas.
const ICO_COPIAR = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>';
const ICO_BAJAR = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5.5 12.5L12 19l6.5-6.5"/></svg>';
const FENCE = /```([\w+-]*)\n?([\s\S]*?)```/g;
function bloquesDeCodigo(span) {
  if (span.querySelector(".riu-code")) return;
  const texto = span.textContent;
  if (!texto.includes("```") || !new RegExp(FENCE.source).test(texto)) return;
  const frag = document.createDocumentFragment(); let ult = 0;
  for (const m of texto.matchAll(FENCE)) {
    if (m.index > ult) frag.append(document.createTextNode(texto.slice(ult, m.index)));
    const pre = document.createElement("pre"); pre.className = "riu-code";
    if (m[1]) pre.dataset.lang = m[1];
    const code = document.createElement("code"); code.textContent = m[2].replace(/\n$/, "");
    const b = document.createElement("button"); b.type = "button"; b.className = "riu-code-copiar";
    b.title = "Copiar código"; b.setAttribute("aria-label", "Copiar código"); b.innerHTML = ICO_COPIAR;
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      try { navigator.clipboard.writeText(code.textContent); b.classList.add("ok"); setTimeout(() => b.classList.remove("ok"), 1200); } catch (err) {}
    });
    pre.append(b, code); frag.append(pre); ult = m.index + m[0].length;
  }
  if (ult < texto.length) frag.append(document.createTextNode(texto.slice(ult)));
  span.replaceChildren(frag);
}
export function conectarRiu({ q }) {
  const hist = q("#histories"); if (!hist || hist.dataset.riu) return;
  hist.dataset.riu = "1";
  const barra = document.createElement("div"); barra.className = "riu-progreso"; barra.setAttribute("aria-hidden", "true");
  const bajar = document.createElement("button"); bajar.type = "button"; bajar.className = "riu-bajar"; bajar.hidden = true;
  bajar.title = "Bajar al final"; bajar.setAttribute("aria-label", "Bajar al final"); bajar.innerHTML = ICO_BAJAR;
  hist.prepend(barra); hist.append(bajar);
  const activa = () => [...hist.querySelectorAll(".chat-history")].find((h) => !h.hidden && h.offsetParent !== null);
  const medir = () => {
    const h = activa(); if (!h) { barra.style.width = "0"; if (!bajar.hidden) bajar.hidden = true; return; }
    const max = h.scrollHeight - h.clientHeight;
    barra.style.width = max > 4 ? Math.round((h.scrollTop / max) * 100) + "%" : "0";
    { const v = !(max - h.scrollTop > 160); if (bajar.hidden !== v) bajar.hidden = v; }
  };
  bajar.addEventListener("click", () => { const h = activa(); if (h) h.scrollTo({ top: h.scrollHeight, behavior: "smooth" }); });
  hist.addEventListener("scroll", medir, { capture: true, passive: true });
  let pend = 0;
  const revisar = () => { pend = 0; hist.querySelectorAll(".message:not(.user) .txt").forEach(bloquesDeCodigo); medir(); };
  new MutationObserver(() => { if (!pend) pend = requestAnimationFrame(revisar); })
    .observe(hist, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["hidden"] });
  revisar();
}
