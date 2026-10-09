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
const DIAGRAMAS = {  // micro diagramas transversales horizontales (texto exacto de Antonio); Ask consil Nvidia groq: pendiente
  "team-qwen": { sel: "#team-qwen-diagrama", texto: "SELECTOR 14 → 1 MODELO → EJECUTAR → SALIDA" },
  "ask-consil-code-qwen-team": { sel: "#consil-code-diagrama", texto: "[DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max] → Qwen 3.8 Max EJECUTA → GLM 5.2 REVISA → Qwen 3.8 Max REVISA → SALIDA" },
  "ask-consil-fromtend-qwen-team": { sel: "#consil-frontend-diagrama", texto: "[DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max] → DeepSeek V4 Pro EJECUTA → GLM 5.2 REVISA → Qwen 3.8 Max REVISA → SALIDA" },
};
const INFO = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>';
const pintarDiagrama = (caja, texto) => {  // pasos en línea, desplazable en horizontal; el texto queda exacto (" → " entre pasos)
  caja.replaceChildren(); caja.title = texto; caja.classList.add("lleno");
  texto.split(" → ").forEach((paso, i) => {
    if (i) { const f = document.createElement("span"); f.className = "dg-flecha"; f.textContent = " → "; caja.append(f); }
    const p = document.createElement("span"); p.className = "dg-paso"; p.textContent = paso; caja.append(p);
  });
};
const svg = (p) => '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
const ICO_F = {  // iconos de línea para las hojas con el mismo diseño que Team qwen
  "Ask consil": '<circle cx="8" cy="8" r="3"/><circle cx="16" cy="8" r="3"/><path d="M2 20c0-3 3-5 6-5s6 2 6 5M14 15c3 0 8 1 8 5"/>',
  Motores: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  pendiente: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
};
const grupoFicha = (id) => id.startsWith("ask-consil") ? "Ask consil" : id.startsWith("motor-") ? "Motores" : id.startsWith("hf-") ? "HF" : id.startsWith("groq-") ? "GROQ" : id.startsWith("nv-") ? "NVIDIA" : "Fichas";
const limpia = (t) => t.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim();
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const decorarFichas = (lista) => {  // Nvidia groq team: mismas filas que Team qwen (icono, título, check azul); mismos handlers e ids
  const filas = [...lista.children].filter((e) => e.matches("button.fila"));
  if (!filas.length) return;
  const mods = window.RIU_CONFIG?.modelos || [], grupos = new Map();
  for (const r of filas) {
    const nom = r.querySelector(".fila-nom"), ck = r.querySelector(".fila-ck"), desc = nom.querySelector(".fila-desc");
    const titulo = (nom.firstChild || nom).textContent, m = mods.find((x) => limpia(x.etiqueta) === titulo) || { id: "" }, g = grupoFicha(m.id);
    const sel = r.classList.contains("on");
    r.className = "mod-fila" + (sel ? " sel" : ""); r.setAttribute("aria-pressed", String(sel)); r.dataset.ficha = m.id;
    const ico = el("span", "mod-ico"); ico.innerHTML = svg(ICO_F[g] || ICO_F.chip);
    const txt = el("span", "mod-txt"); txt.append(el("b", "", titulo)); if (desc) txt.append(el("small", "", desc.textContent));
    ck.className = "mod-ck"; r.replaceChildren(ico, txt, ck);
    if (!grupos.has(g)) grupos.set(g, []); grupos.get(g).push(r);
  }
  const out = [];
  for (const [g, rs] of grupos) { const caja = el("div", "mod-grupo"); caja.append(...rs); out.push(el("h4", "mod-grupo-t", g), caja); }
  lista.replaceChildren(...out);
};
const decorarPendiente = (lista) => {  // Ask consil sin modelos: misma fila/estilo que Team qwen
  const v = lista && lista.querySelector(":scope > .consil-vacio");
  if (!v) return;
  const caja = el("div", "mod-grupo"), f = el("div", "mod-fila mod-pendiente"), ico = el("span", "mod-ico"), txt = el("span", "mod-txt");
  ico.innerHTML = svg(ICO_F.pendiente); txt.append(el("b", "", v.textContent)); f.append(ico, txt, el("span", "mod-ck")); caja.append(f);
  lista.replaceChildren(el("h4", "mod-grupo-t", "Modelos"), caja);
};
const tira_id = (id) => "dg-" + id;
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
  diagramas: Object.fromEntries(Object.entries(DIAGRAMAS).map(([k, v]) => [k, v.texto])),
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
    const d = DIAGRAMAS[s.id];
    if (d) {  // botón "i": muestra/oculta el micro diagrama de este selector como recordatorio
      const info = document.createElement("button");
      info.type = "button"; info.className = "sel-info"; info.innerHTML = INFO;
      info.title = "Ver diagrama de " + s.nombre; info.setAttribute("aria-controls", tira_id(s.id)); info.setAttribute("aria-label", info.title); info.setAttribute("aria-expanded", "false");
      const tira = document.createElement("div"); tira.className = "consil-diagrama sel-diagrama"; tira.hidden = true; tira.id = tira_id(s.id);
      pintarDiagrama(tira, d.texto);
      const caja = q(d.sel); if (caja) pintarDiagrama(caja, d.texto);
      info.addEventListener("click", () => { tira.hidden = !tira.hidden; info.setAttribute("aria-expanded", String(!tira.hidden)); info.classList.toggle("abierto", !tira.hidden); });
      fila.append(info, b, tira);
    } else fila.append(b);
    botones[s.id] = b;
  }
  const ngt = q("#sel-ngt"), ficha = q("#ficha");  // Nvidia groq team: el panel muestra la ficha elegida en su tooltip
  const sync = () => { if (!ngt.classList.contains("bloq")) ngt.title = ficha.title; };
  new MutationObserver(sync).observe(ficha, { attributes: true, attributeFilter: ["title"] }); sync();
  const lf = q("#sh-ficha-lista");
  if (lf) { new MutationObserver(() => decorarFichas(lf)).observe(lf, { childList: true }); decorarFichas(lf); }
  for (const k of ["nvidia", "code", "frontend"]) decorarPendiente(q("#sh-consil-" + k + "-lista"));
  pintar();
}
