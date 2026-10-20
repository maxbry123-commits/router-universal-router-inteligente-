// menu-habilidades.js — al escribir "/" en la caja del chat aparece el menú de Habilidades: acciones reales (comandos, workflows y ventanas del chat).
import { dameWF } from "./contexto.js";
import { el, cargarCss } from "./ventanas-comun.js";
export function montarHabilidades({ root, q, tell }) {
  const m = q("#message"), f = q("#composer"); if (!m || !f || f.dataset.hab) return; f.dataset.hab = "1"; cargarCss("habilidades");
  const caja = el("div", "hab-menu"); caja.hidden = true; caja.setAttribute("role", "listbox"); caja.setAttribute("aria-label", "Habilidades"); f.append(caja);
  let items = [], act = 0;
  const catalogo = () => [
    { cmd: "/ayuda", nombre: "Ayuda", desc: "Qué puede hacer el chat", ins: "/ayuda" },
    ...dameWF().map((w) => ({ cmd: "/wf " + w.nombre, nombre: "Workflow · " + w.nombre, desc: "Escribir una instrucción en su ejecución", ins: "/wf " + w.nombre + " " })),
    { cmd: "/workflow", nombre: "Workflow Loops code Yaiwes", desc: "Abrir la ventana", abre: "#pill-workflows" },
    { cmd: "/constitucion", nombre: "Constitución sentinela", desc: "Abrir la ventana", abre: "#pill-constitucion" },
    { cmd: "/claves", nombre: "Banco de claves", desc: "Abrir la ventana", abre: "#pill-claves" },
    { cmd: "/anclaje", nombre: "Anclaje", desc: "Enlaces, archivos y handoffs", abre: "#btn-ancla" },
    { cmd: "/archivos", nombre: "Archivos", desc: "La carpeta compartida", abre: "#btn-archivos" },
    { cmd: "/sandbox", nombre: "Sandbox", desc: "Instrucciones de código", abre: "#btn-sandbox" },
  ];
  const cerrar = () => { caja.hidden = true; items = []; };
  const elegir = (it) => {
    if (it.abre) { m.value = ""; m.dispatchEvent(new Event("input", { bubbles: true })); cerrar(); const b = q(it.abre); if (b) b.click(); else tell("Esa ventana no está disponible"); return; }
    m.value = it.ins; m.dispatchEvent(new Event("input", { bubbles: true })); m.focus(); cerrar();
  };
  const pintar = () => {
    caja.replaceChildren(el("div", "hab-t", "Habilidades"));
    items.forEach((it, i) => {
      const b = el("button", "hab-it" + (i === act ? " act" : "")); b.type = "button"; b.setAttribute("role", "option"); b.setAttribute("aria-selected", String(i === act));
      b.append(el("strong", "", it.cmd), el("span", "", it.nombre + " · " + it.desc));
      b.addEventListener("mousedown", (e) => e.preventDefault()); b.addEventListener("click", () => elegir(it)); caja.append(b);
    });
  };
  const actualizar = () => {
    const v = m.value; if (!/^\/[^\n]*$/.test(v)) { cerrar(); return; }
    const t = v.slice(1).toLowerCase();
    items = catalogo().filter((it) => it.cmd.slice(1).toLowerCase().startsWith(t) || it.nombre.toLowerCase().includes(t)).slice(0, 8);
    if (!items.length) { cerrar(); return; }
    act = Math.min(act, items.length - 1); caja.hidden = false; pintar();
  };
  m.addEventListener("input", actualizar);
  m.addEventListener("blur", () => setTimeout(cerrar, 150));
  m.addEventListener("keydown", (e) => {
    if (caja.hidden || !items.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); act = (act + 1) % items.length; pintar(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); act = (act - 1 + items.length) % items.length; pintar(); }
    else if (e.key === "Tab" || (e.key === "Enter" && !e.shiftKey && /^\/\S*$/.test(m.value))) { e.preventDefault(); e.stopImmediatePropagation(); elegir(items[act]); }
    else if (e.key === "Escape") cerrar();
  }, true);
}
