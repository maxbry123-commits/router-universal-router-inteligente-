// mode_selector.js - Boton selector de modos para el chat. ES module, sin dependencias.
// Contrato con el backend: cada mensaje lleva  mode_request = { mode_id, source }
//   - boton activo:  { mode_id: "m02_objetivo", source: "button" }
//   - automatico:    { mode_id: "auto",         source: "auto"   }
// El backend (mode_router.py) es la autoridad: el front solo propone, nunca decide.

const STYLE_ID = "mode-selector-style";
const CSS = `
.ms-btn{display:inline-flex;align-items:center;gap:4px;max-width:92px;height:34px;min-height:34px;padding:0 8px;border-radius:999px;border:1px solid var(--border,#555);background:var(--panel,#2a2a2a);color:var(--title,#eee);font:13px/1 system-ui;cursor:pointer;overflow:hidden}
.ms-btn .ms-lb{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.ms-btn[data-locked="true"]{border-color:var(--status-blue,#7aa2ff)}
.ms-sheet-bg{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:9998;display:none}
.ms-sheet{position:fixed;left:12px;right:12px;max-height:55vh;overflow:auto;background:var(--surface,#1e1e1e);color:var(--text,#eee);border:1px solid var(--border,#333);border-radius:16px;padding:6px;z-index:9999;display:none;font:15px system-ui;box-shadow:0 16px 40px rgba(0,0,0,.5)}
.ms-item{display:grid;grid-template-columns:28px 1fr 20px;gap:8px;align-items:center;width:100%;text-align:left;background:none;border:0;color:inherit;padding:8px 10px;border-radius:12px;cursor:pointer;min-height:48px}
.ms-item[aria-checked="true"]{background:var(--module-selected,#2d2d2d)}
.ms-item b{font-weight:650}
.ms-item small{display:block;color:var(--quiet-2,#9aa);margin-top:2px;font-size:12px;font-weight:400}
.ms-ck{color:var(--status-blue,#7aa2ff);font-weight:700}
.ms-sec{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--quiet-2,#888);padding:10px 10px 2px}
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
  const KEY_AP = `chat.tool_approval.${conversationId}`;

  const safeGet = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
  const safeSet = (v) => { try { localStorage.setItem(KEY, v); } catch { /* sin storage: solo memoria */ } };
  const safeGetKey = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
  const safeSetKey = (k, v) => { try { localStorage.setItem(k, v); } catch { /* sin storage */ } };

  let lock = safeGet();
  if (lock !== "auto" && !byId[lock]) lock = "auto";
  let approval = safeGetKey(KEY_AP) === "auto" ? "auto" : "manual";

  // ---- UI
  const btn = el("button", { class: "ms-btn", type: "button", "aria-haspopup": "menu" });
  const hint = el("div", { class: "ms-hint", role: "status" });
  const bg = el("div", { class: "ms-sheet-bg" });
  const sheet = el("div", { class: "ms-sheet", role: "menu" });
  mountEl.append(btn);
  document.body.append(bg, sheet);

  function fila(icono, titulo, detalle, marcado, alClick) {
    const it = el("button", { class: "ms-item", type: "button", role: "menuitemradio", "aria-checked": String(marcado) });
    const box = el("span");
    box.append(el("b", {}, titulo), el("small", {}, detalle));
    it.append(el("span", { "aria-hidden": "true" }, icono), box, el("span", { class: "ms-ck" }, marcado ? "✓" : ""));
    it.addEventListener("click", alClick);
    return it;
  }
  function items() {
    sheet.replaceChildren();
    sheet.append(el("div", { class: "ms-sec" }, "Modo"));
    const rows = [{ id: "auto", icon: "✨", label: "Auto", slash: autoSlash, summary: "El router elige un modo seguro." }, ...modes];
    for (const m of rows) {
      sheet.append(fila(m.icon, m.label, (m.slash ? m.slash + " · " : "") + m.summary, m.id === lock, () => { setLock(m.id); close(); }));
    }
    sheet.append(el("div", { class: "ms-sec" }, "Aprobación de tools"));
    sheet.append(fila("✋", "Manual", "Pregunta antes de usar una herramienta nueva", approval === "manual", () => { setApproval("manual"); close(); }));
    sheet.append(fila("▶", "Automática", "Actúa y se detiene si algo parece inseguro", approval === "auto", () => { setApproval("auto"); close(); }));
    sheet.append(el("div", { class: "ms-sec" }, "Habilidades"));
    sheet.append(fila("/", "Habilidades", "Escribe / para elegir una del chat", false, () => {
      close();
      if (!composerEl) return;
      composerEl.value = "/";
      composerEl.dispatchEvent(new Event("input", { bubbles: true }));
      composerEl.focus();
    }));
  }
  function open() {
    items();
    bg.style.display = "block";
    sheet.style.display = "block";
    const r = btn.getBoundingClientRect();
    const alto = Math.min(window.innerHeight * 0.55, 460);
    sheet.style.maxHeight = alto + "px";
    sheet.style.bottom = Math.max(8, Math.round(window.innerHeight - r.top + 8)) + "px";
  }
  function close() { bg.style.display = "none"; sheet.style.display = "none"; }
  btn.addEventListener("click", open);
  bg.addEventListener("click", close);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });

  function render() {
    const m = byId[lock];
    btn.replaceChildren(el("span", { "aria-hidden": "true" }, m ? m.icon : "✨"), el("span", { class: "ms-lb" }, m ? m.label : "Auto"));
    btn.dataset.locked = String(Boolean(m));
    btn.title = `Modo ${m ? m.label : "Auto"} · tools ${approval === "auto" ? "automáticas" : "manuales"}`;
    btn.setAttribute("aria-label", btn.title);
    if (thinkingToggleEl) {
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
  function setApproval(v) {
    approval = v === "auto" ? "auto" : "manual";
    safeSetKey(KEY_AP, approval);
    render();
    window.dispatchEvent(new CustomEvent("mode:approval", { detail: { tool_approval: approval } }));
  }

  function getModeRequest() {
    return lock === "auto" ? { mode_id: "auto", source: "auto" } : { mode_id: lock, source: "button" };
  }
  function getApproval() { return approval; }

  if (composerEl) {
    composerEl.addEventListener("input", () => {
      const t = (composerEl.value ?? composerEl.textContent ?? "").trimStart();
      const m = t.match(/^(\/[\w-]+)/);
      const cmd = m ? m[1].toLowerCase() : null;
      if (cmd === autoSlash) btn.title = "Se enviará en modo Auto";
      else if (cmd && bySlash[cmd]) btn.title = `Se enviará en modo ${bySlash[cmd].label}`;
    });
  }

  function wrapSend(sendFn) {
    return (payload, ...rest) => sendFn({ ...payload, mode_request: getModeRequest(), tool_approval: getApproval() }, ...rest);
  }

  render();
  return { getModeRequest, getApproval, setLock, setApproval, wrapSend, getLock: () => lock, destroy() { btn.remove(); hint.remove(); bg.remove(); sheet.remove(); } };
}
