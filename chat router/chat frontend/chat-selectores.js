// chat-selectores.js — panel "Selectores" (entre el chat y Control): 5 selectores, cada uno con su botón ON/OFF.
// Solo frontend: NO llama al Router ni envía nada. Solo 1 encendido a la vez: al encender uno, los demás quedan
// bloqueados (gris, deshabilitados) hasta apagarlo. Gancho para la ficha/plugin (Claude):
// window.RIU_SELECTORES { activo, selectores, consil, encender(id), apagar() } + evento 'riu:selector-activo' { activo, anterior, nombre }.
const CLAVE = "riu_selector_activo";  // sessionStorage: sobrevive a recargas en esta pestaña
const SELECTORES = [  // nombres exactos de Antonio
  { id: "nvidia-groq-team", nombre: "Nvidia groq team", pills: ["#sel-ngt", "#ficha"] },  // las 11 fichas
  { id: "ask-consil-nvidia-groq", nombre: "Ask consil Nvidia groq", pills: ["#sel-cn"] },
  { id: "team-qwen", nombre: "Team qwen", pills: ["#sel-nuevo"] },  // los 14 modelos Qwen
  { id: "ask-consil-code-qwen-team", nombre: "Ask cónsil code qwen team", pills: ["#sel-cc"] },
  { id: "ask-consil-fromtend-qwen-team", nombre: "Ask consil fromtend qwen team", pills: ["#sel-cf"] },
];
const POWER = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0"/></svg>';
const usable = (id) => SELECTORES.some((s) => s.id === id);
const leer = () => { try { const v = sessionStorage.getItem(CLAVE); return usable(v) ? v : null; } catch (e) { return null; } };
const escribir = (v) => { try { v ? sessionStorage.setItem(CLAVE, v) : sessionStorage.removeItem(CLAVE); } catch (e) { /* sin almacenamiento */ } };

window.RIU_SELECTORES = window.RIU_SELECTORES || {
  activo: null,
  selectores: SELECTORES.map((s) => ({ id: s.id, nombre: s.nombre })),
  consil: {  // modelos vacíos hasta que Antonio los dé; el micro diagrama transversal se pinta dentro de estos contenedores
    "ask-consil-nvidia-groq": { modelos: [], diagrama: "#consil-nvidia-diagrama" },
    "ask-consil-code-qwen-team": { modelos: [], diagrama: "#consil-code-diagrama" },
    "ask-consil-fromtend-qwen-team": { modelos: [], diagrama: "#consil-frontend-diagrama" },
  },
};

export function conectarSelectores({ q }) {
  const R = window.RIU_SELECTORES, panel = q("#sel-power");
  if (!panel) return;
  const botones = {};
  const pintar = () => {
    const act = leer(), nAct = act ? SELECTORES.find((s) => s.id === act).nombre : "";
    R.activo = act;
    for (const s of SELECTORES) {
      const on = act === s.id, bloq = !!act && !on, b = botones[s.id];
      b.classList.toggle("on", on); b.disabled = bloq; b.setAttribute("aria-pressed", String(on));
      b.lastChild.textContent = on ? "ON" : "OFF";
      b.title = bloq ? "Bloqueado: apaga «" + nAct + "» primero" : on ? s.nombre + " encendido · toca para apagar" : "Encender " + s.nombre + " (bloquea los demás)";
      b.closest(".sel-fila").classList.toggle("activa", on);
      for (const sel of s.pills) {
        const p = q(sel);
        if (!p) continue;
        if (bloq && !p.classList.contains("bloq")) { p.dataset.t0 = p.title || ""; p.title = "Bloqueado: «" + nAct + "» está encendido"; }
        if (!bloq && p.classList.contains("bloq")) p.title = p.dataset.t0 || "";
        p.disabled = bloq; p.classList.toggle("bloq", bloq);
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
  for (const s of SELECTORES) {
    const fila = panel.querySelector('[data-selector="' + s.id + '"]');
    const b = document.createElement("button");
    b.type = "button"; b.className = "sel-on"; b.dataset.selector = s.id; b.setAttribute("aria-label", "ON/OFF " + s.nombre);
    b.innerHTML = POWER + "<span>OFF</span>";
    b.addEventListener("click", () => cambiar(leer() === s.id ? null : s.id));
    fila.append(b); botones[s.id] = b;
  }
  const ngt = q("#sel-ngt"), ficha = q("#ficha");  // Nvidia groq team: el panel muestra la ficha elegida en su tooltip
  const sync = () => { if (!ngt.classList.contains("bloq")) ngt.title = ficha.title; };
  new MutationObserver(sync).observe(ficha, { attributes: true, attributeFilter: ["title"] }); sync();
  pintar();
}
