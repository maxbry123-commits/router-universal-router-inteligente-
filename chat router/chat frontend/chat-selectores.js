// chat-selectores.js — panel "Selectores" (entre el chat y Control): 5 selectores, cada uno con su botón ON/OFF.
// Solo frontend: NO llama al Router ni envía nada. Solo 1 encendido a la vez: al encender uno, los demás quedan
// bloqueados (gris, deshabilitados) hasta apagarlo. Gancho para la ficha/plugin (Claude):
// window.RIU_SELECTORES { activo, selectores, consil, encender(id), apagar() } + evento 'riu:selector-activo' { activo, anterior, nombre }.
const CLAVE = "riu_selector_activo";  // sessionStorage: sobrevive a recargas en esta pestaña
const SELECTORES = [  // nombres exactos de Antonio
  { id: "nvidia-groq-team", nombre: "Nvidia groq team", pills: ["#sel-ngt", "#ficha"] },
  { id: "ask-consil-nvidia-groq", nombre: "Ask consil Nvidia groq", pills: ["#sel-cn"] },
  { id: "team-qwen", nombre: "Team qwen", pills: ["#sel-nuevo"] },  // los 14 modelos QwenCloud
  { id: "ask-consil-code-qwen-team", nombre: "Ask cónsil code qwen team", pills: ["#sel-cc"] },
  { id: "ask-consil-fromtend-qwen-team", nombre: "Ask consil fromtend qwen team", pills: ["#sel-cf"] },
];
const POWER = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0"/></svg>';
const DIAGRAMAS = {  // micro diagramas transversales horizontales; Ask consil Nvidia groq sigue pendiente de definición explícita
  "team-qwen": { sel: "#team-qwen-diagrama", texto: "SELECTOR 14 → 1 MODELO → EJECUTAR → SALIDA" },
  "ask-consil-code-qwen-team": { sel: "#consil-code-diagrama", texto: "[DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max] → Qwen 3.8 Max EJECUTA → GLM 5.2 REVISA → Qwen 3.8 Max REVISA → SALIDA" },
  "ask-consil-fromtend-qwen-team": { sel: "#consil-frontend-diagrama", texto: "[DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max] → DeepSeek V4 Pro EJECUTA → GLM 5.2 REVISA → Qwen 3.8 Max REVISA → SALIDA" },
};
const CONSIL_MODELOS = {
  "ask-consil-code-qwen-team": [
    ["DeepSeek V4 Pro", "Analiza arquitectura · paralelo"],
    ["GLM 5.2", "Analiza · paralelo · revisa/refactoriza"],
    ["Qwen 3.7 Max", "Analiza arquitectura · paralelo"],
    ["Qwen 3.8 Max", "Ejecuta código · revisión final"],
  ],
  "ask-consil-fromtend-qwen-team": [
    ["DeepSeek V4 Pro", "Analiza · paralelo · ejecuta frontend"],
    ["GLM 5.2", "Analiza · paralelo · revisa/refactoriza"],
    ["Qwen 3.7 Max", "Analiza · paralelo"],
    ["Qwen 3.8 Max", "Revisión final"],
  ],
};
const INFO = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>';
const pintarDiagrama = (caja, texto) => {  // pasos en línea, desplazable en horizontal; el texto queda exacto (" → " entre pasos)
  caja.replaceChildren(); caja.title = texto; caja.classList.add("lleno");
  const pista = () => caja.classList.toggle("mas", caja.scrollLeft + caja.clientWidth < caja.scrollWidth - 2);  // pista visual: hay más a la derecha
  if (!caja.dataset.pista) { caja.dataset.pista = "1"; caja.addEventListener("scroll", pista, { passive: true }); new ResizeObserver(pista).observe(caja); }
  texto.split(" → ").forEach((paso, i) => {
    if (i) { const f = document.createElement("span"); f.className = "dg-flecha"; f.textContent = " → "; caja.append(f); }
    const p = document.createElement("span"); p.className = "dg-paso"; p.textContent = paso; caja.append(p);
  });
};
const svg = (p) => '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
const ICO_F = {  // iconos de línea para las hojas con el mismo diseño que Team qwen
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
  flecha: '<path d="M4 12h15M13 6l6 6-6 6"/>',
  lupa: '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  pendiente: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
};
const icoFicha = (id) => id.startsWith("ask-consil") ? "pensar" : id === "motor-descarga" ? "flecha" : id.startsWith("motor-") ? "lupa" : "chip";  // equivalente de línea del emoji original
const limpia = (t) => t.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim();
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const decorarFichas = (lista) => {  // Nvidia groq team: las MISMAS fichas reales de RIU_CONFIG, mismo orden; no inventa proveedores
  const filas = [...lista.children].filter((e) => e.matches("button.fila"));
  if (!filas.length) return;
  const mods = window.RIU_CONFIG?.modelos || [], caja = el("div", "mod-grupo");
  for (const r of filas) {
    const nom = r.querySelector(".fila-nom"), ck = r.querySelector(".fila-ck"), desc = nom.querySelector(".fila-desc");
    const titulo = (nom.firstChild || nom).textContent, m = mods.find((x) => limpia(x.etiqueta) === titulo) || { id: "" };
    const sel = r.classList.contains("on");
    r.className = "mod-fila" + (sel ? " sel" : ""); r.setAttribute("aria-pressed", String(sel)); r.dataset.ficha = m.id;
    const ico = el("span", "mod-ico"); ico.innerHTML = svg(ICO_F[icoFicha(m.id)]);
    const txt = el("span", "mod-txt"); txt.append(el("b", "", titulo)); if (desc) txt.append(el("small", "", desc.textContent));
    ck.className = "mod-ck"; r.replaceChildren(ico, txt, ck);
    caja.append(r);
  }
  lista.replaceChildren(caja);
};
const decorarPendiente = (lista) => {  // Ask consil Nvidia groq: todavía no se inventan modelos ni flujo
  const v = lista && lista.querySelector(":scope > .consil-vacio");
  if (!v) return;
  const caja = el("div", "mod-grupo"), f = el("div", "mod-fila mod-pendiente"), ico = el("span", "mod-ico"), txt = el("span", "mod-txt");
  ico.innerHTML = svg(ICO_F.pendiente); txt.append(el("b", "", v.textContent)); f.append(ico, txt, el("span", "mod-ck")); caja.append(f);
  lista.replaceChildren(caja);
};
const decorarConsil = (lista, modelos) => {  // vista informativa; no ejecuta nada ni finge backend
  if (!lista || !modelos?.length) return;
  const caja = el("div", "mod-grupo");
  for (const [nombre, rol] of modelos) {
    const f = el("div", "mod-fila"), ico = el("span", "mod-ico"), txt = el("span", "mod-txt");
    ico.innerHTML = svg(ICO_F.pensar);
    txt.append(el("b", "", nombre), el("small", "", rol));
    f.append(ico, txt, el("span", "mod-ck"));
    caja.append(f);
  }
  lista.replaceChildren(caja);
};
const tira_id = (id) => "dg-" + id;
const usable = (id) => SELECTORES.some((s) => s.id === id);
const leer = () => { try { const v = sessionStorage.getItem(CLAVE); return usable(v) ? v : null; } catch (e) { return null; } };
const escribir = (v) => { try { v ? sessionStorage.setItem(CLAVE, v) : sessionStorage.removeItem(CLAVE); } catch (e) { /* sin almacenamiento */ } };

window.RIU_SELECTORES = window.RIU_SELECTORES || {
  activo: null,
  selectores: SELECTORES.map((s) => ({ id: s.id, nombre: s.nombre })),
  consil: {
    "ask-consil-nvidia-groq": { modelos: [], diagrama: "#consil-nvidia-diagrama", estado: "PENDIENTE_DEFINICION" },
    "ask-consil-code-qwen-team": { modelos: CONSIL_MODELOS["ask-consil-code-qwen-team"].map((m) => m[0]), diagrama: "#consil-code-diagrama", estado: "UI_DEFINIDA_BACKEND_PENDIENTE" },
    "ask-consil-fromtend-qwen-team": { modelos: CONSIL_MODELOS["ask-consil-fromtend-qwen-team"].map((m) => m[0]), diagrama: "#consil-frontend-diagrama", estado: "UI_DEFINIDA_BACKEND_PENDIENTE" },
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
    } else { const hueco = el("span", "sel-info sel-info-hueco"); hueco.setAttribute("aria-hidden", "true"); fila.append(hueco, b); }  // mismo ancho que la "i": las 5 filas alinean
    botones[s.id] = b;
  }
  const ngt = q("#sel-ngt"), ficha = q("#ficha");  // Nvidia groq team: el panel muestra la ficha elegida en su tooltip
  const sync = () => { if (!ngt.classList.contains("bloq")) ngt.title = ficha.title; };
  new MutationObserver(sync).observe(ficha, { attributes: true, attributeFilter: ["title"] }); sync();
  const lf = q("#sh-ficha-lista");
  if (lf) { new MutationObserver(() => decorarFichas(lf)).observe(lf, { childList: true }); decorarFichas(lf); }
  decorarPendiente(q("#sh-consil-nvidia-lista"));
  decorarConsil(q("#sh-consil-code-lista"), CONSIL_MODELOS["ask-consil-code-qwen-team"]);
  decorarConsil(q("#sh-consil-frontend-lista"), CONSIL_MODELOS["ask-consil-fromtend-qwen-team"]);
  pintar();
}
