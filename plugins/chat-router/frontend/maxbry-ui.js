// maxbry-ui.js — Maxbry UI (skill fromted-yaiwes-frontend-factory): reorganiza el composer del chat sin tocar sus handlers.
// Los mismos nodos (ids, listeners, badges) se reubican: fila principal [＋][📎][🎤] … [Enviar], chips [Auto][Pensar][IA] y bandeja «Agregar al chat».
// Iconos de línea del skill (sprite), editor que crece solo (y se amplía con ⤢), avisos tipo toast y estado del Router con punto de señal.
const SVG = (n, c) => '<svg class="mx-ico ' + (c || "") + '" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-' + n + '"/></svg>';
const SPRITE = '<svg xmlns="http://www.w3.org/2000/svg" id="mx-sprite" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">' + [
  ["plus", '<path d="M12 5v14M5 12h14"/>'], ["spark", '<path d="m12 2 2.1 7.9L22 12l-7.9 2.1L12 22l-2.1-7.9L2 12l7.9-2.1Z"/>'],
  ["send", '<path d="m3 20 18-8L3 4l2.5 7L14 12l-8.5 1Z"/>'], ["attach", '<path d="m9 13 5.5-5.5a3 3 0 0 1 4.2 4.2l-8 8a5 5 0 0 1-7.1-7.1l8.4-8.4"/>'],
  ["shield", '<path d="M12 2 20 5v6c0 5-3 8-8 11-5-3-8-6-8-11V5Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>'], ["message", '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8A8.5 8.5 0 0 1 12.5 20a8.3 8.3 0 0 1-3.8-.9L3 21l1.9-5.7A8.3 8.3 0 0 1 4 11.5a8.5 8.5 0 0 1 17 0Z"/>'],
  ["check", '<path d="m5 12 4 4L19 6"/>'], ["doc", '<path d="M5 2h10l5 5v15H5Z"/><path d="M15 2v5h5M8 12h9M8 16h9"/>'], ["down", '<path d="m6 9 6 6 6-6"/>'],
  ["think", '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>'],
  ["expand", '<path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/>'], ["x", '<path d="M5 5 19 19M19 5 5 19"/>'], ["power", '<path d="M12 2v10M6 5a9 9 0 1 0 12 0"/>'], ["settings", '<circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>'],
].map(([id, d]) => '<symbol id="i-' + id + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + d + "</symbol>").join("") + "</svg>";
const TEXTO = { "btn-archivos": "Archivos", "btn-ancla": "Anclar", "btn-sandbox": "Sandbox", "btn-copiar-input": "Copiar", "btn-conexiones": "Conexiones", "btn-room": "ROOM", "btn-pendientes": "Pendientes", "btn-power": "Servidor" };
const FIJOS = new Set(["btn-adjunto", "btn-microfono", "btn-detener", "btn-tools", "btn-agentes", "btn-prompt", "mx-mas", "mx-grande"]);  // se quedan en la fila principal
const ICONOS = { "btn-conexiones": "shield", "btn-room": "message", "btn-pendientes": "check", "btn-power": "power" };  // botones propios: iconos de línea en vez de emojis
const el = (t, c) => { const e = document.createElement(t); if (c) e.className = c; return e; };

function sprite() { if (!document.getElementById("mx-sprite")) document.body.insertAdjacentHTML("afterbegin", SPRITE); }

function montar(comp) {
  const msg = comp.querySelector("#message"), bar = comp.querySelector(".composer-bar");
  if (!msg || !bar || comp.dataset.mx) return; comp.dataset.mx = "1"; sprite();
  const raiz = (document.querySelector("#sh-mas") || {}).parentElement || document.body;
  // ＋ y bandeja «Agregar al chat» (patrón de las referencias Grok/Claude: tarjetas con icono + título)
  const mas = el("button", "secondary"); mas.type = "button"; mas.id = "mx-mas"; mas.title = "Agregar al chat"; mas.setAttribute("aria-label", "Agregar al chat"); mas.setAttribute("aria-haspopup", "dialog"); mas.innerHTML = SVG("plus");
  const hoja = el("div", "sheet"); hoja.id = "mx-hoja"; hoja.hidden = true; hoja.setAttribute("role", "dialog"); hoja.setAttribute("aria-label", "Agregar al chat");
  const caja = el("div", "va-caja"), cab = el("div", "row va-head"), x = el("button", "secondary sh-cerrar"), bandeja = el("div", "mx-bandeja"), ajustes = el("button", "mx-fila-ajustes");
  bandeja.id = "mx-bandeja"; x.type = "button"; x.textContent = "✕"; x.setAttribute("aria-label", "Cerrar");
  ajustes.type = "button"; ajustes.innerHTML = SVG("settings") + "<span><strong>Herramientas y permisos</strong><small>Encender o apagar cada herramienta</small></span>" + SVG("down", "mx-der");
  ajustes.onclick = () => { hoja.hidden = true; const t = document.querySelector("#btn-tools"); if (t) t.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true })); };
  const strong = el("strong"); strong.textContent = "Agregar al chat"; cab.append(strong, x); caja.append(cab, bandeja, ajustes); hoja.append(caja); raiz.append(hoja);
  const cerrar = () => { hoja.hidden = true; };
  x.onclick = cerrar; hoja.addEventListener("click", (e) => { if (e.target === hoja) cerrar(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(); });
  mas.onclick = () => { hoja.hidden = false; };
  bandeja.addEventListener("click", () => setTimeout(cerrar, 0));  // el botón elegido ya actuó (abre su ventana o el selector de archivos)
  bar.insertBefore(mas, bar.firstChild);
  // chips: Auto (selector de modos), Pensar (abre el selector de pensamiento) e IA/agentes
  const chips = el("div", "mx-chips"); chips.setAttribute("role", "group"); chips.setAttribute("aria-label", "Modo, pensamiento e IA"); comp.insertBefore(chips, bar);
  const pensar = el("button", "mx-chip"); pensar.type = "button"; pensar.id = "mx-pensar"; pensar.title = "Cómo piensa el modelo: rápido, equilibrado o pensar";
  const modo = () => document.querySelector("#modo");
  pensar.onclick = () => { const m = modo(); if (m) m.click(); };
  const pintarPensar = () => { const m = modo(), t = m ? m.textContent.replace(/[⌄˅v]\s*$/, "").trim() : "equilibrado"; pensar.innerHTML = SVG("think") + "<span>" + (t || "equilibrado").replace(/^./, (c) => c.toUpperCase()) + "</span>"; pensar.setAttribute("aria-pressed", String(/pensar/i.test(t))); };
  pintarPensar();
  // editor: crece con el texto, se amplía con ⤢
  const grande = el("button", "mx-grande"); grande.type = "button"; grande.id = "mx-grande"; grande.title = "Ampliar el editor"; grande.setAttribute("aria-label", "Ampliar el editor"); grande.setAttribute("aria-pressed", "false"); grande.innerHTML = SVG("expand");
  comp.insertBefore(grande, msg);
  const ajustar = () => { msg.style.height = "auto"; const max = Math.round(window.innerHeight * (comp.classList.contains("mx-grande") ? 0.7 : 0.38)); msg.style.height = Math.min(msg.scrollHeight + 2, max) + "px"; };
  grande.onclick = () => { const on = comp.classList.toggle("mx-grande"); grande.setAttribute("aria-pressed", String(on)); ajustar(); if (on) msg.focus(); };
  msg.addEventListener("input", ajustar); new ResizeObserver(() => { if (!msg.value) msg.style.height = ""; }).observe(comp);
  window.addEventListener("resize", ajustar); comp.addEventListener("submit", () => setTimeout(() => { msg.style.height = ""; }, 50));
  const colocar = () => {  // mueve cada botón nuevo (aparecen por módulos que cargan tarde) a su sitio, sin clonar
    const modos = document.querySelector("#mode-selector-mount"); if (modos && modos.parentElement !== chips) chips.append(modos);
    if (pensar.parentElement !== chips) chips.append(pensar);
    ["#btn-tools", "#btn-agentes"].forEach((id) => { const b = document.querySelector(id); if (b && b.parentElement !== chips) chips.append(b); });
    bar.querySelectorAll(":scope > button.secondary").forEach((b) => {
      if (FIJOS.has(b.id) || b.classList.contains("sh-cerrar")) return;
      b.dataset.mx = TEXTO[b.id] || (b.title || b.getAttribute("aria-label") || "").split(/[·:(]/)[0].trim().slice(0, 16);
      if (ICONOS[b.id] && !b.querySelector("svg")) b.innerHTML = SVG(ICONOS[b.id]);
      bandeja.append(b);
    });
    const a = bar.querySelector(".anclados"); if (a && a.parentElement === bar && bar.firstChild !== a) bar.insertBefore(a, bar.firstChild);
    const adj = bar.querySelector("#btn-adjunto"), mic = bar.querySelector("#btn-microfono");
    if (adj && mas.nextElementSibling !== adj) mas.after(adj);
    if (mic && adj && adj.nextElementSibling !== mic) adj.after(mic);
    pintarPensar();
  };
  colocar(); new MutationObserver(colocar).observe(bar, { childList: true }); const m = modo(); if (m) new MutationObserver(pintarPensar).observe(m, { childList: true, characterData: true, subtree: true });
  // Detener solo mientras el chat trabaja (mismo estado real que el indicador de pensamiento)
  setInterval(() => { const d = bar.querySelector("#btn-detener"); if (!d) return; let o = false; try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); o = !!(c && c.ocupado); } catch (e) {} d.hidden = !o; }, 300);
}

function avisos() {  // #notice como toast: se retira solo (errores, más tiempo) y no tapa el chat
  const n = document.querySelector("#notice"); if (!n || n.dataset.mx) return; n.dataset.mx = "1"; let t = 0;
  new MutationObserver(() => { clearTimeout(t); if (!n.textContent) return; t = setTimeout(() => { n.textContent = ""; n.classList.remove("err"); }, /GAP|error|fall|HTTP|no se|bloquead/i.test(n.textContent) ? 9000 : 5000); }).observe(n, { childList: true, characterData: true, subtree: true });
  n.addEventListener("click", () => { n.textContent = ""; });
}

function estado() {  // punto de señal (skill .signal) en el estado del Router
  const s = document.querySelector("#movil-status"); if (!s || s.dataset.mx) return; s.dataset.mx = "1";
  const pintar = () => { s.dataset.estado = /error|no disponible|detenido/i.test(s.textContent) ? "err" : s.textContent.trim() ? "ok" : ""; };
  s.style.cursor = "pointer"; s.title = "Encender, apagar o reiniciar el Router"; s.onclick = () => { const p = document.querySelector("#btn-power"); if (p) p.click(); };  // el estado abre el panel del servidor
  pintar(); new MutationObserver(pintar).observe(s, { childList: true, characterData: true, subtree: true });
}

const MEDIO = /\[\[(imagen|video|audio):((?:https:\/\/|data:audio\/)[^\]\s]+)\]\]/g, HAY_MEDIO = /\[\[(imagen|video|audio):/;
function medios() {  // [[imagen:URL]] / [[video:URL]] / [[audio:URL]] que devuelve la ficha -> el medio dentro de la burbuja (solo https o audio data:)
  document.querySelectorAll(".chat-history .message:not(.user):not(.pending) .txt:not([data-mx])").forEach((t) => {
    t.dataset.mx = "1"; if (!HAY_MEDIO.test(t.textContent)) return;
    const lista = [...t.textContent.matchAll(MEDIO)]; t.textContent = t.textContent.replace(MEDIO, "").trim();
    lista.forEach(([, tipo, url]) => {
      const m = document.createElement(tipo === "imagen" ? "img" : tipo); m.src = url; m.className = "mx-medio";
      if (tipo === "imagen") { m.alt = "Imagen generada"; m.loading = "lazy"; } else m.controls = true;
      const a = document.createElement("a"); a.href = url; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Abrir " + tipo; a.className = "mx-medio-enlace";
      t.after(m); m.after(a);
    });
  });
}

const revisar = () => { try { const c = document.querySelector("#composer"); if (c) montar(c); avisos(); estado(); medios(); const e = document.querySelector(".riu-estado"); if (e && !e.dataset.mx) { e.dataset.mx = "1"; e.style.cursor = "pointer"; e.onclick = () => { const p = document.querySelector("#btn-power"); if (p) p.click(); }; } } catch (e) { console.warn("maxbry-ui", e); } };
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
