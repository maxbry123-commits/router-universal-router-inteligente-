// composer-filas.js — la caja de escritura en filas ordenadas sin esconder nada:
//  fila 1 (solo si hay): anclados en una línea · fila 2: herramientas (iconos) en una tira deslizable · fila 3: IA / Agentes / System prompt + Enviar.
// Mueve los MISMOS nodos (listeners intactos). Enviar (.action) y los chips siguen siendo hijos directos de la barra: el código que hace
// bar.insertBefore(x, bar.querySelector(".action")) sigue funcionando. Botón ⤢ en el historial: salida a pantalla casi completa.
const CHIPS = new Set(["btn-tools", "btn-agentes", "btn-prompt"]);
const QUEDAN = (e) => e.classList.contains("action") || e.classList.contains("cb-herr") || e.classList.contains("cb-chips") || e.id === "anclados" || CHIPS.has(e.id) || e.tagName === "INPUT";
const KEY = "riu_herr_abiertas";
const abiertas = () => { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } };
function ordenar(bar) {
  let tira = bar.querySelector(":scope > .cb-herr"), chips = bar.querySelector(":scope > .cb-chips");
  if (!tira) { tira = document.createElement("div"); tira.className = "cb-herr"; tira.id = "cb-herr"; tira.setAttribute("role", "toolbar"); tira.setAttribute("aria-label", "Herramientas del chat"); bar.insertBefore(tira, bar.firstChild); }
  if (!chips) {  // fila de estado: IA / Agentes / System prompt siempre a la vista + botón para abrir las herramientas (móvil)
    chips = document.createElement("div"); chips.className = "cb-chips"; bar.insertBefore(chips, tira.nextSibling);
    const mas = document.createElement("button"); mas.type = "button"; mas.className = "cb-mas secondary"; mas.id = "cb-mas"; mas.setAttribute("aria-controls", "cb-herr");
    const pinta = (on) => { const f = bar.closest("#composer"); if (f) f.classList.toggle("cb-abierto", on); mas.setAttribute("aria-expanded", String(on)); mas.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + (on ? "m6 15 6-6 6 6" : "m6 9 6 6 6-6") + '"/></svg><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.4 2.4-2.6-.6-.6-2.6z"/></svg>'; mas.title = on ? "Ocultar las herramientas (más espacio para la salida)" : "Mostrar las herramientas"; mas.setAttribute("aria-label", mas.title); };
    mas.onclick = () => { const on = !(bar.closest("#composer") || document.body).classList.contains("cb-abierto"); pinta(on); try { localStorage.setItem(KEY, on ? "1" : ""); } catch (e) {} };
    chips.append(mas); pinta(abiertas());
  }
  [...bar.children].forEach((e) => { if (CHIPS.has(e.id)) chips.insertBefore(e, chips.querySelector(".cb-mas")); else if (!QUEDAN(e) && e !== chips) tira.append(e); });
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
