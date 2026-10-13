// chat-riu.js — componentes RUI (rare-ui, chat router/01-PLAN) llevados a JS simple, en archivo propio:
//  09 code-block: los bloques ``` de las respuestas se ven como codigo con boton copiar
//  08 scroll-progress: barra de avance de lectura + botones subir/bajar en salidas largas
// Solo frontend y con datos reales del chat: no inventa mensajes ni respuestas.
const ICO_COPIAR = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>';
const ICO_BAJAR = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5.5 12.5L12 19l6.5-6.5"/></svg>';
const ICO_SUBIR = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5.5 11.5L12 5l6.5 6.5"/></svg>';
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
  const subir = document.createElement("button"); subir.type = "button"; subir.className = "riu-subir"; subir.hidden = true;
  subir.title = "Subir al inicio"; subir.setAttribute("aria-label", "Subir al inicio"); subir.innerHTML = ICO_SUBIR;
  const bajar = document.createElement("button"); bajar.type = "button"; bajar.className = "riu-bajar"; bajar.hidden = true;
  bajar.title = "Bajar al final"; bajar.setAttribute("aria-label", "Bajar al final"); bajar.innerHTML = ICO_BAJAR;
  hist.prepend(barra); hist.append(subir, bajar);
  const activa = () => [...hist.querySelectorAll(".chat-history")].find((h) => !h.hidden && h.offsetParent !== null);

  // GAP 3: cada historial decide si sigue la salida. Solo una accion REAL del usuario cambia esta bandera.
  // Los scrollTop que haga otro modulo al llegar progreso/respuesta no pueden volver a activar el seguimiento.
  const estado = new WeakMap();
  const st = (h) => {
    if (!estado.has(h)) estado.set(h, { seguir: true, top: h.scrollTop || 0, usuario: false });
    return estado.get(h);
  };
  const marcarUsuario = (e) => {
    const h = e.target.closest && e.target.closest(".chat-history");
    if (!h) return;
    const s = st(h); s.usuario = true; s.top = h.scrollTop;
    setTimeout(() => { s.usuario = false; }, 180);
  };
  hist.addEventListener("touchstart", marcarUsuario, { capture: true, passive: true });
  hist.addEventListener("pointerdown", marcarUsuario, { capture: true, passive: true });
  hist.addEventListener("wheel", marcarUsuario, { capture: true, passive: true });

  const medir = () => {
    const h = activa();
    if (!h) { barra.style.width = "0"; subir.hidden = bajar.hidden = true; return; }
    const max = h.scrollHeight - h.clientHeight;
    barra.style.width = max > 4 ? Math.round((h.scrollTop / max) * 100) + "%" : "0";
    subir.hidden = h.scrollTop < 120;
    bajar.hidden = !(max - h.scrollTop > 160);
  };

  hist.addEventListener("scroll", (e) => {
    const h = e.target.closest && e.target.closest(".chat-history");
    if (!h) { medir(); return; }
    const s = st(h);
    if (s.usuario) {
      const max = Math.max(0, h.scrollHeight - h.clientHeight);
      s.top = h.scrollTop;
      s.seguir = max - h.scrollTop <= 80;
    }
    medir();
  }, { capture: true, passive: true });

  subir.addEventListener("click", () => {
    const h = activa(); if (!h) return;
    const s = st(h); s.seguir = false; s.top = 0;
    h.scrollTo({ top: 0, behavior: "smooth" });
  });
  bajar.addEventListener("click", () => {
    const h = activa(); if (!h) return;
    const s = st(h); s.seguir = true;
    h.scrollTo({ top: h.scrollHeight, behavior: "smooth" });
    s.top = h.scrollHeight;
  });

  let pend = 0;
  const revisar = () => {
    pend = 0;
    hist.querySelectorAll(".message:not(.user) .txt").forEach(bloquesDeCodigo);
    const h = activa();
    if (h) {
      const s = st(h);
      if (s.seguir) {
        h.scrollTop = h.scrollHeight;
        s.top = h.scrollTop;
      } else {
        // Restaura la lectura donde el usuario la dejó aunque panel-chat intente bajar al recibir progreso.
        h.scrollTop = Math.min(s.top, Math.max(0, h.scrollHeight - h.clientHeight));
      }
    }
    medir();
  };
  new MutationObserver(() => { if (!pend) pend = requestAnimationFrame(revisar); })
    .observe(hist, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["hidden"] });
  revisar();

  // Gancho para otras piezas del chat: permite consultar/forzar el seguimiento sin tocar el DOM interno.
  window.RIU_SCROLL = {
    seguir() { const h = activa(); return h ? st(h).seguir : true; },
    arriba() { subir.click(); },
    abajo() { bajar.click(); },
  };
}
