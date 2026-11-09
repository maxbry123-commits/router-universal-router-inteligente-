// mode_selector.js - Boton selector de modos para el chat. ES module, sin dependencias.
// Contrato con el backend: cada mensaje lleva  mode_request = { mode_id, source }
//   - boton activo:  { mode_id: "m02_objetivo", source: "button" }
//   - automatico:    { mode_id: "auto",         source: "auto"   }
// El backend (mode_router.py) es la autoridad: el front solo propone, nunca decide.

const STYLE_ID = "mode-selector-style";
const CSS = `
.ms-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:999px;border:1px solid #555;background:#2a2a2a;color:#eee;font:14px system-ui;cursor:pointer;min-height:40px}
.ms-btn[data-locked="true"]{border-color:#7aa2ff;background:#1d2a4a}
.ms-sheet-bg{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9998;display:none}
.ms-sheet{position:fixed;left:0;right:0;bottom:0;max-height:75vh;overflow:auto;background:#1e1e1e;color:#eee;border-radius:16px 16px 0 0;padding:8px 8px calc(16px + env(safe-area-inset-bottom,0px));z-index:9999;display:none;font:15px system-ui}
.ms-item{display:flex;gap:12px;align-items:flex-start;width:100%;text-align:left;background:none;border:0;color:inherit;padding:12px;border-radius:10px;cursor:pointer;min-height:48px}
.ms-item:hover,.ms-item[aria-checked="true"]{background:#2d2d2d}
.ms-item small{display:block;opacity:.7;margin-top:2px;font-size:12px}
.ms-tag{font-size:11px;opacity:.8;border:1px solid #666;border-radius:6px;padding:0 6px;margin-left:6px}
.ms-hint{font:12px system-ui;color:#9ab;padding:4px 8px}
`;

function el(tag, attrs = {}, text) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (text !== undefined) n.textContent = text;   // textContent: nunca innerHTML
  return n;
}

export async function initModeSelector(opts) {
  const { mountEl, registryUrl, conversationId = "default", composerEl = null,
          thinkingToggleEl = null, onChange = () => {} } = opts;
  if (!mountEl) throw new Error("mode_selector: falta mountEl");

  if (!document.getElementById(STYLE_ID)) {
    const s = el("style", { id: STYLE_ID }); s.textContent = CSS; document.head.appendChild(s);
  }

  const res = await fetch(registryUrl, { cache: "no-store" });
  if (!res.ok) throw new Error(`mode_selector: no pude cargar el registro (${res.status})`);
  const reg = await res.json();
  const modes = reg.modes.slice().sort((a, b) => a.order - b.order);
  const byId = Object.fromEntries(modes.map(m => [m.id, m]));
  const bySlash = Object.fromEntries(modes.map(m => [m.slash.toLowerCase(), m]));
  const autoSlash = (reg.selector.auto_slash || "/auto").toLowerCase();
  const KEY = `chat.mode_lock.${conversationId}`;

  const safeGet = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
  const safeSet = (v) => { try { localStorage.setItem(KEY, v); } catch { /* sin storage: solo memoria */ } };

  let lock = safeGet();
  if (lock !== "auto" && !byId[lock]) lock = "auto";   // id invalido guardado => auto (nunca un modo fantasma)

  // ---- UI
  const btn = el("button", { class: "ms-btn", type: "button", "aria-haspopup": "menu" });
  const hint = el("div", { class: "ms-hint", role: "status" });
  const bg = el("div", { class: "ms-sheet-bg" });
  const sheet = el("div", { class: "ms-sheet", role: "menu" });
  mountEl.append(btn, hint);
  document.body.append(bg, sheet);

  function items() {
    sheet.replaceChildren();
    const rows = [{ id: "auto", icon: "✨", label: "Auto", summary: "El router elige un modo seguro (nunca uno autonomo)." }, ...modes];
    for (const m of rows) {
      const it = el("button", { class: "ms-item", type: "button", role: "menuitemradio", "aria-checked": String(m.id === lock) });
      const icon = el("span", {}, m.icon);
      const box = el("span");
      const title = el("span", {}, m.label);
      if (m.autonomous_loop) title.append(el("span", { class: "ms-tag" }, "autonomo"));
      box.append(title, el("small", {}, (m.slash ? m.slash + " · " : "") + m.summary));
      it.append(icon, box);
      it.addEventListener("click", () => { setLock(m.id); close(); });
      sheet.append(it);
    }
  }
  function open() { items(); bg.style.display = "block"; sheet.style.display = "block"; }
  function close() { bg.style.display = "none"; sheet.style.display = "none"; }
  btn.addEventListener("click", open);
  bg.addEventListener("click", close);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });

  function render() {
    const m = byId[lock];
    btn.textContent = m ? `${m.icon} ${m.label}` : "✨ Auto";
    btn.dataset.locked = String(Boolean(m));
    btn.setAttribute("aria-label", `Modo: ${m ? m.label : "Auto"}`);
    if (thinkingToggleEl) {   // politica mode_wins: en modos autonomos el interruptor de thinking no manda
      const blocked = Boolean(m && m.autonomous_loop);
      thinkingToggleEl.disabled = blocked;
      thinkingToggleEl.title = blocked ? "Controlado por el modo activo" : "";
    }
  }

  function setLock(id) {
    if (id !== "auto" && !byId[id]) throw new Error(`mode_selector: modo desconocido ${id}`);
    lock = id; safeSet(id); render(); onChange(getModeRequest());
    window.dispatchEvent(new CustomEvent("mode:change", { detail: getModeRequest() }));
  }

  function getModeRequest() {
    return lock === "auto" ? { mode_id: "auto", source: "auto" } : { mode_id: lock, source: "button" };
  }

  // Vista previa de slash (solo informativa; el backend es quien resuelve)
  if (composerEl) {
    composerEl.addEventListener("input", () => {
      const t = (composerEl.value ?? composerEl.textContent ?? "").trimStart();
      const m = t.match(/^(\/[\w-]+)/);
      const cmd = m ? m[1].toLowerCase() : null;
      if (cmd === autoSlash) hint.textContent = "Se enviara en modo Auto";
      else if (cmd && bySlash[cmd]) hint.textContent = `Se enviara en modo ${bySlash[cmd].label} (slash)`;
      else hint.textContent = "";
    });
  }

  // Envuelve tu funcion de envio existente: agrega mode_request SIN tocar el resto del payload
  function wrapSend(sendFn) {
    return (payload, ...rest) => sendFn({ ...payload, mode_request: getModeRequest() }, ...rest);
  }

  render();
  return { getModeRequest, setLock, wrapSend, getLock: () => lock, destroy() { btn.remove(); hint.remove(); bg.remove(); sheet.remove(); } };
}
