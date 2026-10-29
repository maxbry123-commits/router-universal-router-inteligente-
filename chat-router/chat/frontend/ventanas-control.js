// ventanas-control.js — base de las ventanas del composer (Conexiones, ROOM CONFERENCIAS, Servidor): botón con icono de línea + hoja.
// El navegador solo muestra y pide: permisos, secretos y salas viven en el servidor (mvp/control.py).
export const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
export const btn = (txt, cls, fn) => { const b = el("button", cls || "secondary", txt); b.type = "button"; if (fn) b.onclick = fn; return b; };
export const campo = (ph, tipo) => { const i = el("input"); i.placeholder = ph; i.type = tipo || "text"; i.autocomplete = "off"; i.setAttribute("aria-label", ph); return i; };
export const falla = (est, x) => { est.textContent = "⚠️ " + x.message; };
export const vivo = (e) => { e.setAttribute("role", "status"); e.setAttribute("aria-live", "polite"); return e; };  // región viva: los lectores de pantalla leen el aviso
export const SIN_BACKEND = "SIN_BACKEND";  // el servidor (o su plugin) no existe o no responde: la interfaz lo dice y no finge
const FOCO = 'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])';
const ICONOS = {  // iconos de línea (skill Maxbry): sin emojis en la barra
  conexiones: '<path d="M12 2 20 5v6c0 5-3 8-8 11-5-3-8-6-8-11V5Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>',
  room: '<path d="M21 11.5a8.4 8.4 0 0 1-9 8.5 8.3 8.3 0 0 1-3.8-.9L3 21l1.9-5.7A8.4 8.4 0 0 1 12 3a8.4 8.4 0 0 1 9 8.5z"/><path d="M8 11h.01M12 11h.01M16 11h.01"/>',
  power: '<path d="M12 3v9"/><path d="M6.3 6.3a8 8 0 1 0 11.4 0"/>',
  loop: '<path d="M4 12a8 8 0 0 1 13.5-5.5L20 4"/><path d="M20 4v5h-5"/><path d="M20 12a8 8 0 0 1-13.5 5.5L4 20"/><path d="M4 20v-5h5"/>',
  mcp: '<path d="M4 8h5M15 8h5M4 16h5M15 16h5"/><circle cx="12" cy="8" r="2"/><circle cx="12" cy="16" r="2"/>',
  watchdog: '<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>',
  cola: '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
  tareas: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M8 14h4"/>',
  comandos: '<path d="M8 8l-3 4 3 4M13 16h6"/>',
  sesion: '<circle cx="12" cy="8" r="3"/><path d="M5 19c1.5-3 3.8-4.5 7-4.5S17.5 16 19 19"/>',
  reglas: '<path d="M8 7h11M8 12h11M8 17h7M5 7h.01M5 12h.01M5 17h.01"/>',
};
export function ventana(id, titulo, alAbrir) {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-" + id)) return;
  const b = btn("", "secondary"); b.id = "btn-" + id; b.title = titulo; b.setAttribute("aria-label", titulo); b.setAttribute("aria-haspopup", "dialog");
  b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONOS[id] + "</svg>";
  const s = el("div", "sheet"); s.id = "ventana-" + id; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-modal", "true"); s.setAttribute("aria-label", titulo);
  const c = el("div", "va-caja cv-caja"), h = el("div", "row va-head"), x = btn("✕", "secondary sh-cerrar", () => { s.hidden = true; b.focus(); }), cuerpo = el("div", "list");
  x.setAttribute("aria-label", "Cerrar " + titulo);
  s.onclick = (ev) => { if (ev.target === s) s.hidden = true; };
  document.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && !s.hidden) { s.hidden = true; b.focus(); } });  // aunque el foco se haya perdido al repintar
  document.addEventListener("keydown", (ev) => {  // el foco se queda dentro de la ventana mientras está abierta
    if (ev.key !== "Tab" || s.hidden) return;
    const dentro = [...s.querySelectorAll(FOCO)].filter((n) => n.getClientRects().length);
    if (!dentro.length) { ev.preventDefault(); return; }
    const primero = dentro[0], ultimo = dentro[dentro.length - 1];
    if (!s.contains(document.activeElement)) { ev.preventDefault(); primero.focus(); }
    else if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
    else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
  });
  h.append(el("strong", "", titulo), x); c.append(h, cuerpo); s.append(c); document.body.append(s);
  b.onclick = () => { s.hidden = false; x.focus(); alAbrir(cuerpo, s); };
  bar.insertBefore(b, bar.querySelector(".action") || null);
}
