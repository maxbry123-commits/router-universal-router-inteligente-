// composer-filas.js — la caja de escritura en filas ordenadas sin esconder nada:
//  fila 1 (solo si hay): anclados en una línea · fila 2: herramientas (iconos) en una tira deslizable · fila 3: IA / Agentes / System prompt + Enviar.
// Mueve los MISMOS nodos (listeners intactos). Enviar (.action) y los chips siguen siendo hijos directos de la barra: el código que hace
// bar.insertBefore(x, bar.querySelector(".action")) sigue funcionando. Botón ⤢ en el historial: salida a pantalla casi completa.
const CHIPS = new Set(["btn-tools", "btn-agentes", "btn-prompt"]);
const QUEDAN = (e) => e.classList.contains("action") || e.classList.contains("cb-herr") || e.id === "anclados" || CHIPS.has(e.id) || e.tagName === "INPUT";
function ordenar(bar) {
  let tira = bar.querySelector(":scope > .cb-herr");
  if (!tira) { tira = document.createElement("div"); tira.className = "cb-herr"; tira.setAttribute("role", "toolbar"); tira.setAttribute("aria-label", "Herramientas del chat"); bar.insertBefore(tira, bar.firstChild); }
  [...bar.children].forEach((e) => { if (!QUEDAN(e)) tira.append(e); });
}
function ampliar(hist) {
  if (!hist || hist.querySelector(".riu-ampliar")) return;
  const b = document.createElement("button"); b.type = "button"; b.className = "riu-ampliar"; b.setAttribute("aria-pressed", "false");
  b.title = "Ampliar la salida"; b.setAttribute("aria-label", "Ampliar la salida");
  b.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>';
  b.onclick = () => { const on = document.body.classList.toggle("salida-grande"); b.setAttribute("aria-pressed", String(on)); b.title = on ? "Volver al tamaño normal" : "Ampliar la salida"; b.setAttribute("aria-label", b.title); try { localStorage.setItem("riu_salida_grande", on ? "1" : ""); } catch (e) {} };
  hist.append(b);
  try { if (localStorage.getItem("riu_salida_grande")) b.click(); } catch (e) {}
}
const revisar = () => {
  const bar = document.querySelector("#composer .composer-bar");
  if (bar && !bar.dataset.filas) { bar.dataset.filas = "1"; ordenar(bar); new MutationObserver(() => ordenar(bar)).observe(bar, { childList: true }); }
  ampliar(document.querySelector("#histories"));
};
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
