// chat-selectores.js — interruptor ⏻ ON/OFF de los 5 selectores. Solo frontend: NO llama al Router ni envía nada.
// Solo 1 encendido a la vez: al encender uno, los demás quedan bloqueados (gris, deshabilitados) hasta apagarlo.
// Gancho para la ficha/plugin (Claude): window.RIU_SELECTORES { activo, selectores, consil, encender(id), apagar() }
// y evento 'riu:selector-activo' { activo, anterior, nombre }. El 5º selector queda reservado y oculto hasta tener nombre.
import { node } from "./api.js";

const CLAVE = "riu_selector_activo";  // sessionStorage: sobrevive a recargas en esta pestaña
const SELECTORES = [
  { id: "modelo", nombre: "Modelo", corto: "Modelo", pills: ["#ficha"] },
  { id: "qwen", nombre: "Selector Qwen", corto: "Qwen", pills: ["#sel-nuevo"] },
  { id: "consil-code", nombre: "Ask Cónsil Code", corto: "Cónsil Code", pills: ["#sel-cc"] },
  { id: "consil-frontend", nombre: "Ask Cónsil Frontend", corto: "Cónsil Frontend", pills: ["#sel-cf"] },
  { id: "selector-5", nombre: "", corto: "", pills: [], reservado: true },  // nombre y modelos: los da Antonio
];
const usable = (id) => SELECTORES.some((s) => s.id === id && (!s.reservado || s.nombre));
const leer = () => { try { const v = sessionStorage.getItem(CLAVE); return usable(v) ? v : null; } catch (e) { return null; } };
const escribir = (v) => { try { v ? sessionStorage.setItem(CLAVE, v) : sessionStorage.removeItem(CLAVE); } catch (e) { /* sin almacenamiento */ } };

window.RIU_SELECTORES = window.RIU_SELECTORES || {
  activo: null,
  selectores: SELECTORES.map((s) => ({ id: s.id, nombre: s.nombre, reservado: !!s.reservado })),
  consil: {  // modelos vacíos hasta que Antonio los dé; el micro diagrama se pinta dentro de estos contenedores
    "consil-code": { modelos: [], diagrama: "#consil-code-diagrama" },
    "consil-frontend": { modelos: [], diagrama: "#consil-frontend-diagrama" },
  },
};

export function conectarSelectores({ q }) {
  const R = window.RIU_SELECTORES, barra = q("#sel-power");
  if (!barra) return;
  const botones = {};
  const pintar = () => {
    const act = leer(), nAct = act ? SELECTORES.find((s) => s.id === act).nombre : "";
    R.activo = act;
    for (const s of SELECTORES) {
      const on = act === s.id, bloq = !!act && !on, b = botones[s.id];
      b.classList.toggle("on", on); b.disabled = bloq; b.setAttribute("aria-pressed", String(on));
      b.title = bloq ? "Bloqueado: apaga «" + nAct + "» primero" : on ? s.nombre + " encendido · toca para apagar" : "Encender " + s.nombre + " (bloquea los demás)";
      for (const sel of s.pills) {
        const p = q(sel);
        if (!p) continue;
        if (p.dataset.t0 === undefined) p.dataset.t0 = p.title || "";
        p.disabled = bloq; p.classList.toggle("bloq", bloq); p.classList.toggle("sel-activo", on);
        p.title = bloq ? "Bloqueado: «" + nAct + "» está encendido" : p.dataset.t0;
        const sh = bloq && p.dataset.sheet ? q("#" + p.dataset.sheet) : null;
        if (sh) sh.hidden = true;
      }
    }
  };
  const cambiar = (nuevo) => {
    const anterior = leer();
    escribir(nuevo); pintar();
    const nombre = nuevo ? SELECTORES.find((s) => s.id === nuevo).nombre : null;
    window.dispatchEvent(new CustomEvent("riu:selector-activo", { detail: { activo: nuevo, anterior, nombre } }));
  };
  R.encender = (id) => { const a = leer(); if (!usable(id) || (a && a !== id)) return false; if (a !== id) cambiar(id); return true; };
  R.apagar = () => { if (leer()) cambiar(null); return true; };
  barra.replaceChildren();
  for (const s of SELECTORES) {
    const b = node("button", "", "sel-on");
    b.type = "button"; b.dataset.selector = s.id; b.hidden = !usable(s.id);
    b.append(node("span", "⏻", "sel-on-ico"), node("span", s.corto, "sel-on-txt"));
    b.addEventListener("click", () => cambiar(leer() === s.id ? null : s.id));
    barra.append(b); botones[s.id] = b;
  }
  pintar();
}
