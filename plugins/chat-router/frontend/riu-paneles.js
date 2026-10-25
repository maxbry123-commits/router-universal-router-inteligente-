// riu-paneles.js — cola del motor como tareas (RUI 21), actividad de 28 días (RUI 12) y carpeta vacía (RUI 01). Dividido de chat-riu2.js sin cambiar la lógica.
import { crear, leer } from "./riu-util.js";
// RUI 21 task-list: la cola del motor como lista de tareas con tilde (URLs reales de la cola)
export function colaMotor({ q }) {
  const cola = q("#motor-cola"), urls = q("#motor-urls"), sh = q("#sh-motor"); if (!cola || !urls) return;
  const lista = crear("ul", "riu-tareas"); lista.setAttribute("aria-label", "Cola de descargas"); cola.after(lista);
  const pintar = () => {
    const us = urls.value.match(/https?:\/\/[^\s"'<>)]+/g) || [];
    const txt = cola.textContent || "", m = /(\d+)\/(\d+)/.exec(txt), fin = /terminada/.test(txt);
    const hechas = !m ? 0 : fin ? Number(m[1]) : Math.max(0, Number(m[1]) - 1);
    lista.replaceChildren();
    us.slice(0, 50).forEach((u, i) => {
      const li = crear("li", i < hechas ? "hecha" : (m && !fin && i === hechas ? "en-curso" : ""));
      li.append(crear("span", "riu-tilde", i < hechas ? "✓" : ""), crear("span", "riu-tarea-t", u.replace(/^https?:\/\//, "").slice(0, 64)));
      lista.append(li);
    });
  };
  urls.addEventListener("input", pintar); urls.addEventListener("change", pintar);
  new MutationObserver(pintar).observe(cola, { childList: true, characterData: true, subtree: true });
  if (sh) new MutationObserver(() => { if (!sh.hidden) pintar(); }).observe(sh, { attributes: true, attributeFilter: ["hidden"] });
  pintar();
}

// RUI 12 github-activity: tus mensajes de los ultimos 28 dias (del historial local), en "Mas opciones"
export function actividad({ q }) {
  const sh = q("#sh-mas"), caja = sh && sh.querySelector(".va-caja"); if (!caja || caja.querySelector(".riu-actividad")) return;
  const t = crear("div", "mod-grupo-t", "Actividad (28 días)"), g = crear("div", "riu-actividad"); g.setAttribute("role", "img"); caja.append(t, g);
  const pintar = () => {
    const h = leer("riu_hist_v1", {}), dias = {};
    Object.values(h).forEach((l) => (Array.isArray(l) ? l : []).forEach((m) => { if (m && m.rol === "user" && m.ts) { const k = new Date(m.ts).toDateString(); dias[k] = (dias[k] || 0) + 1; } }));
    g.replaceChildren(); let tot = 0;
    for (let i = 27; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i); const n = dias[d.toDateString()] || 0; tot += n;
      const c = crear("i", "riu-dia n" + (n ? Math.min(4, Math.ceil(n / 3)) : 0)); c.title = d.toLocaleDateString() + ": " + n + " mensaje(s)"; g.append(c);
    }
    g.setAttribute("aria-label", tot + " mensajes tuyos en 28 días");
  };
  new MutationObserver(() => { if (!sh.hidden) pintar(); }).observe(sh, { attributes: true, attributeFilter: ["hidden"] });
}

// RUI 01 folder: carpeta que se abre cuando "Archivos en memoria" está vacía
export function carpetaVacia({ q }) {
  const lista = q("#va-lista"); if (!lista || lista.dataset.carpeta) return; lista.dataset.carpeta = "1";
  const c = crear("div", "riu-carpeta"); c.hidden = true;
  c.innerHTML = '<svg viewBox="0 0 64 56" width="64" height="56" aria-hidden="true"><path class="fondo" d="M4 12a4 4 0 0 1 4-4h14l6 6h28a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path class="tapa" d="M4 24h56v24a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/></svg><span>Aún no hay archivos en memoria</span>';
  lista.after(c);
  const act = () => { const n = lista.children.length; c.hidden = !(n === 0 || (n === 1 && /sin |vac[ií]o|no hay|ning/i.test(lista.textContent))); };
  new MutationObserver(act).observe(lista, { childList: true }); act();
}
