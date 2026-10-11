// selector-workflows.js — fila "workflow Loops code Yaiwes" en el panel Selectores: selección + botón ON/OFF, con el mismo formato que las otras filas.
// La selección abre la ventana de workflows (varios a la vez); el botón enciende el workflow elegido o apaga todos. Las otras filas no se tocan.
import { leer, escribir, KEYS } from "./almacen.js";
import { dameWF } from "./contexto.js";
import { el } from "./ventanas-comun.js";
const POWER = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0"/></svg>';
export function montarSelectorWorkflows({ root, q, tell }) {
  const sec = q("#selectores"); if (!sec || sec.querySelector("#sel-workflows")) return;
  const lista = el("div", "sel-lista"), fila = el("div", "sel-fila"); fila.dataset.selector = "workflow-loops-code-yaiwes";
  const pill = el("button", "pill sel-pill", "workflow Loops code Yaiwes ⌄"); pill.type = "button"; pill.id = "sel-workflows"; pill.setAttribute("aria-haspopup", "dialog"); pill.title = "Elegir y configurar workflows";
  const hueco = el("span", "sel-info sel-info-hueco"); hueco.setAttribute("aria-hidden", "true");
  const on = el("button", "sel-on"); on.type = "button"; on.setAttribute("aria-label", "ON/OFF workflow Loops code Yaiwes"); on.innerHTML = POWER + "<span>OFF</span>";
  const abrir = () => { const p = q("#pill-workflows"); if (p) p.click(); };
  pill.addEventListener("click", abrir);
  on.addEventListener("click", () => {
    const x = leer(KEYS.workflows, { lista: [], sel: null });
    if (!Array.isArray(x.lista) || !x.lista.length) { tell("Crea un workflow primero"); abrir(); return; }
    const hayOn = x.lista.some((w) => w.encendido);
    if (hayOn) x.lista.forEach((w) => { w.encendido = false; });
    else { const w = x.lista.find((y) => y.id === x.sel) || x.lista[0]; w.encendido = true; tell("Workflow encendido: " + w.nombre); }
    escribir(KEYS.workflows, x); if (hayOn) tell("Workflows apagados");
  });
  fila.append(pill, hueco, on); lista.append(fila); sec.append(lista);
  const sync = () => {
    const n = dameWF().filter((w) => w.encendido).length;
    on.classList.toggle("on", n > 0); on.setAttribute("aria-pressed", String(n > 0)); on.lastChild.textContent = n > 1 ? "ON · " + n : n ? "ON" : "OFF";
    on.title = n ? "Workflows encendidos: " + n + " · toca para apagar" : "Encender el workflow elegido"; fila.classList.toggle("activa", n > 0);
  };
  const onAlm = () => { if (!root.isConnected) { window.removeEventListener("riu:almacen", onAlm); return; } sync(); };
  window.addEventListener("riu:almacen", onAlm); sync();
}
