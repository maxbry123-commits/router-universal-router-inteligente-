// rui-media.js — RUI 16 grid-reveal y RUI 22 voice-note (Rare UI, swamimalode07/rare-ui @1d572f4, components/ui/*.tsx)
// llevados a JS simple sin React. Se conserva la geometría, los tiempos y la lógica originales; solo cambian los colores (tokens del tema).
// Créditos: componentes de Rare UI (https://github.com/swamimalode07/rare-ui), usados con atribución según su licencia.
// NO MOCK: el grid-reveal termina cuando la imagen de verdad cargó; el voice-note reproduce el audio real (sin audio = bloqueado).
import { cargarCss } from "./ventanas-comun.js";
const reduce = () => { try { return matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; } };

// ---------- RUI 16 grid-reveal ----------
const CELLS = 180, OPENING_CELLS = 4, HOLD = 0.9, WAIT_CAP = 0.72, LAST_SPLIT = 0.92, MORPH = 0.055, SAMPLE = 128, COLOR_MS = 420;
const GUTTER_FROM = 0.35, GUTTER_TO = 0.75, PHOTO_FROM = 0.93;
const clamp01 = (n) => (n > 0 ? (n < 1 ? n : 1) : 0);
const mix = (a, b, t) => a + (b - a) * t;
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const smoothstep = (a, b, x) => { const t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const selfPaced = (elapsed, duration) => HOLD * (1 - Math.exp(-elapsed / (duration > 0 ? duration : 1)));
const hash = (x, y, z) => { const n = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453; return n - Math.floor(n); };
const makeCell = (x, y, w, h, parent) => ({ x, y, w, h, r: 0, g: 0, b: 0, tone: hash(x + 3.1, y + 1.7, w * 31.7), detail: 0, splitAt: 0, parent, kids: null });
function buildTree(aspect) {
  const root = makeCell(0, 0, 1, 1, null), leaves = [root], branches = [];
  while (leaves.length < CELLS) {
    let pick = 0, widest = -1;
    for (let i = 0; i < leaves.length; i++) { const c = leaves[i], area = c.w * aspect * c.h * (1 + 0.12 * hash(c.x, c.y, 7.3)); if (area > widest) { widest = area; pick = i; } }
    const p = leaves.splice(pick, 1)[0], wide = p.w * aspect >= p.h, half = wide ? p.w / 2 : p.h / 2;
    const a = wide ? makeCell(p.x, p.y, half, p.h, p) : makeCell(p.x, p.y, p.w, half, p);
    const b = wide ? makeCell(p.x + half, p.y, half, p.h, p) : makeCell(p.x, p.y + half, p.w, half, p);
    p.kids = [a, b]; branches.push(p); leaves.push(a, b);
  }
  const opening = OPENING_CELLS - 1, rest = Math.max(1, branches.length - opening);
  branches.forEach((c, i) => { c.splitAt = i < opening ? -MORPH : (LAST_SPLIT * (i - opening + 1)) / rest; });
  return { root, branches };
}
function measureTree(root, px, size) {
  const gather = (cell) => {
    let s;
    if (cell.kids) { const a = gather(cell.kids[0]), b = gather(cell.kids[1]); s = { n: a.n + b.n, r: a.r + b.r, g: a.g + b.g, b: a.b + b.b, l: a.l + b.l, l2: a.l2 + b.l2 }; }
    else {
      s = { n: 0, r: 0, g: 0, b: 0, l: 0, l2: 0 };
      const x0 = Math.round(cell.x * size), y0 = Math.round(cell.y * size), x1 = Math.max(x0 + 1, Math.round((cell.x + cell.w) * size)), y1 = Math.max(y0 + 1, Math.round((cell.y + cell.h) * size));
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { const i = (y * size + x) * 4, r = px[i], g = px[i + 1], bb = px[i + 2], l = 0.299 * r + 0.587 * g + 0.114 * bb; s.n++; s.r += r; s.g += g; s.b += bb; s.l += l; s.l2 += l * l; }
    }
    const n = s.n || 1; cell.r = s.r / n; cell.g = s.g / n; cell.b = s.b / n; cell.detail = Math.max(0, s.l2 / n - (s.l / n) * (s.l / n)); return s;
  };
  gather(root);
}
function orderByDetail(branches, before) {
  const pending = branches.filter((c) => c.splitAt > before); if (pending.length < 2) return;
  const slots = pending.map((c) => c.splitAt).sort((a, b) => a - b), queue = pending.filter((c) => !c.parent || c.parent.splitAt <= before);
  let next = 0;
  while (queue.length && next < slots.length) {
    let pick = 0; for (let i = 1; i < queue.length; i++) if (queue[i].detail > queue[pick].detail) pick = i;
    const cell = queue.splice(pick, 1)[0]; cell.splitAt = slots[next++]; for (const k of cell.kids || []) if (k.kids) queue.push(k);
  }
}
const coverRect = (iw, ih, w, h) => { const s = Math.max(w / iw, h / ih); return { dx: (w - iw * s) / 2, dy: (h - ih * s) / 2, dw: iw * s, dh: ih * s }; };
const temaOscuro = () => { try { const c = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim() || getComputedStyle(document.body).backgroundColor; const m = c.match(/\d+/g); if (c.startsWith("#")) { const h = c.length === 4 ? c.slice(1).split("").map((x) => x + x).join("") : c.slice(1, 7); return parseInt(h.slice(0, 2), 16) * 0.299 + parseInt(h.slice(2, 4), 16) * 0.587 + parseInt(h.slice(4, 6), 16) * 0.114 < 128; } return m ? m[0] * 0.299 + m[1] * 0.587 + m[2] * 0.114 < 128 : true; } catch (e) { return true; } };
const greyOf = (tone, dark, clock) => (dark ? 30 : 228) + tone * 13 + Math.sin(clock * 1.5 + tone * 6.28) * 3;
function drawScene(s) {
  const { ctx, root, width, height, split } = s, tint = s.hasColors ? s.fade : 0, shade = (g, t) => Math.round(mix(g, t, tint)), base = greyOf(root.tone, s.dark, s.clock);
  ctx.fillStyle = `rgb(${Math.round(shade(base, root.r) * 0.92)},${Math.round(shade(base, root.g) * 0.92)},${Math.round(shade(base, root.b) * 0.92)})`; ctx.fillRect(0, 0, width, height);
  const soft = 1 - smoothstep(GUTTER_FROM, GUTTER_TO, split), gutter = s.scale * soft, rounded = soft > 0.01 && typeof ctx.roundRect === "function";
  const paint = (p) => {
    const x = Math.round(p.x), y = Math.round(p.y), w = Math.round(p.x + p.w) - x, h = Math.round(p.y + p.h) - y;
    const oL = x <= 0, oT = y <= 0, oR = x + w >= width, oB = y + h >= height, left = oL ? 0 : gutter, top = oT ? 0 : gutter;
    const iw = w - left - (oR ? 0 : gutter), ih = h - top - (oB ? 0 : gutter); if (iw <= 0 || ih <= 0) return;
    const g = greyOf(p.tone, s.dark, s.clock); ctx.fillStyle = `rgb(${shade(g, p.r)},${shade(g, p.g)},${shade(g, p.b)})`;
    if (rounded) { const rr = Math.min(iw, ih) * 0.12 * soft; ctx.beginPath(); ctx.roundRect(x + left, y + top, iw, ih, [!oL && !oT ? rr : 0, !oR && !oT ? rr : 0, !oR && !oB ? rr : 0, !oL && !oB ? rr : 0]); ctx.fill(); }
    else ctx.fillRect(x + left, y + top, iw, ih);
  };
  const walk = (cell, p) => {
    if (!cell.kids || split < cell.splitAt) { paint(p); return; }
    const t = easeOut(clamp01((split - cell.splitAt) / MORPH));
    for (const k of cell.kids) walk(k, { x: mix(p.x, k.x * width, t), y: mix(p.y, k.y * height, t), w: mix(p.w, k.w * width, t), h: mix(p.h, k.h * height, t), r: mix(p.r, k.r, t), g: mix(p.g, k.g, t), b: mix(p.b, k.b, t), tone: mix(p.tone, k.tone, t) });
  };
  walk(root, { x: 0, y: 0, w: width, h: height, r: root.r, g: root.g, b: root.b, tone: root.tone });
  if (!s.image) return;
  const photo = s.hasColors ? smoothstep(PHOTO_FROM, 1, split) * s.fade : s.fade; if (photo <= 0.002) return;
  const fit = coverRect(s.image.naturalWidth, s.image.naturalHeight, width, height);
  ctx.globalAlpha = photo; ctx.drawImage(s.image, fit.dx, fit.dy, fit.dw, fit.dh); ctx.globalAlpha = 1;
}
function readAverages(img, root, branches, at) {
  const buf = document.createElement("canvas"); buf.width = SAMPLE; buf.height = SAMPLE;
  const ctx = buf.getContext("2d", { willReadFrequently: true }); if (!ctx) return false;
  const fit = coverRect(img.naturalWidth, img.naturalHeight, SAMPLE, SAMPLE); ctx.drawImage(img, fit.dx, fit.dy, fit.dw, fit.dh);
  try { measureTree(root, ctx.getImageData(0, 0, SAMPLE, SAMPLE).data, SAMPLE); orderByDetail(branches, at); return true; } catch (e) { return false; }
}
// Muestra src con el efecto grid-reveal; al terminar deja la <img> real (nodoFinal). onError si la imagen no carga.
export function gridReveal(src, { alt = "", estimatedDuration = 6000, onDone, onError, nodoFinal } = {}) {
  cargarCss("rui-media");
  const frame = document.createElement("div"); frame.className = "rui-grid"; frame.dataset.slot = "grid-reveal"; frame.setAttribute("role", "img"); frame.setAttribute("aria-label", alt || "imagen"); frame.setAttribute("aria-busy", "true");
  const canvas = document.createElement("canvas"); canvas.setAttribute("aria-hidden", "true"); frame.append(canvas);
  const ctx = canvas.getContext("2d"); if (!ctx) return frame;
  let tree = buildTree(1); const scene = { ctx, root: tree.root, width: 0, height: 0, scale: 1, dark: temaOscuro(), clock: 0, split: 0, fade: 0, hasColors: false, image: null };
  let loadedAt = -1, cancelled = false, frameId = 0, stopped = false; const red = reduce();
  const render = (split, now) => { scene.split = split; scene.fade = loadedAt < 0 ? 0 : smoothstep(0, COLOR_MS, now - loadedAt); drawScene(scene); };
  const repaint = () => { if (!red) return render(scene.split, performance.now()); render(scene.image ? 1 : WAIT_CAP, loadedAt < 0 ? performance.now() : loadedAt + COLOR_MS); };
  const resize = () => { const dpr = Math.min(window.devicePixelRatio || 1, 2), r = frame.getBoundingClientRect(), w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr)); scene.scale = dpr; if (w === scene.width && h === scene.height) return; scene.width = w; scene.height = h; canvas.width = w; canvas.height = h; repaint(); };
  const obs = typeof ResizeObserver === "function" ? new ResizeObserver(resize) : null; obs && obs.observe(frame);
  const fin = () => { if (cancelled) return; cancelled = true; cancelAnimationFrame(frameId); obs && obs.disconnect(); frame.setAttribute("aria-busy", "false"); frame.dataset.revealed = "1"; if (nodoFinal) { frame.replaceWith(nodoFinal); } onDone && onDone(); };
  const load = (url, cors) => {
    const im = new Image(); if (cors) im.crossOrigin = "anonymous"; im.decoding = "async";
    im.onload = () => {
      if (cancelled) return; if (!im.naturalWidth || !im.naturalHeight) { onError && onError(); return; }
      // el marco toma la proporción real de la imagen (el árbol se rehace antes de la primera división visible)
      const asp = im.naturalWidth / im.naturalHeight; frame.style.aspectRatio = String(asp);
      if (scene.split < 0.05) { tree = buildTree(asp); scene.root = tree.root; }
      scene.image = im; loadedAt = performance.now(); scene.hasColors = readAverages(im, scene.root, tree.branches, scene.split);
      resize(); if (red) { repaint(); setTimeout(fin, 0); }
    };
    im.onerror = () => { if (cancelled) return; if (cors && !/^(blob|data):/.test(url)) load(url, false); else { cancelled = true; cancelAnimationFrame(frameId); obs && obs.disconnect(); frame.dataset.error = "1"; frame.setAttribute("aria-busy", "false"); onError && onError(); } };
    im.src = url;
  };
  requestAnimationFrame(resize);
  if (src) load(src, !/^(blob|data):/.test(src));
  if (red) return frame;
  let last = 0, elapsed = 0, eased = 0, split = 0, fired = false;
  const tick = (now) => {
    if (cancelled || stopped) return; frameId = requestAnimationFrame(tick);
    if (!frame.isConnected && elapsed > 1) { cancelled = true; cancelAnimationFrame(frameId); obs && obs.disconnect(); return; }
    if (!last) last = now; const dt = Math.min((now - last) / 1000, 0.05); last = now; elapsed += dt; scene.clock = elapsed;
    const ready = scene.image !== null, target = ready ? 1 : selfPaced(elapsed * 1000, estimatedDuration);
    eased += (target - eased) * (1 - Math.exp(-dt * 5.5)); const wanted = Math.min(eased, ready ? 1 : WAIT_CAP); split += (wanted - split) * (1 - Math.exp(-dt * 4));
    render(split, now);
    if (!fired && ready && eased > 0.995 && now - loadedAt > COLOR_MS) fired = true;
    if (fired && split > 0.9995) { render(1, now); stopped = true; fin(); }
  };
  frameId = requestAnimationFrame(tick);
  return frame;
}

// ---------- RUI 22 voice-note ----------
const SPEEDS = [1, 1.5, 2], CONTROL_RATIO = 0.76, ICON_RATIO = 0.72, BLUR_RATIO = 0.32, PEAK_RATIO = 0.68, PULSE_SPEED = 0.6, SPIN_UP = 0.45, PLAYING_GLOW = 0.62, START_AT = 6.2, SEEK_STEP = 5, MIN_AMPLITUDE = 0.14;
const BLOBS = [{ size: 2, alpha: 0.5, lap: 11, offset: 0.04, pulse: 0.12 }, { size: 1.5, alpha: 0.4, lap: 17, offset: 0.19, pulse: 0.14 }, { size: 2.3, alpha: 0.45, lap: 23, offset: 0.47, pulse: 0.1 }, { size: 1.2, alpha: 0.35, lap: 13, offset: 0.71, pulse: 0.16 }];
const SIZE = { height: 52, gap: 10, bar: 3, barGap: 3, pad: 14 };
const PLAY_SHAPE = [7.7, 5.8, 13, 8.9, 13, 15.1, 7.7, 18.2, 13, 8.9, 18.3, 12, 18.3, 12, 13, 15.1];
const PAUSE_SHAPE = [8.2, 6.8, 10.9, 6.8, 10.9, 17.2, 8.2, 17.2, 13.1, 6.8, 15.8, 6.8, 15.8, 17.2, 13.1, 17.2];
const toPath = (s) => { let d = ""; for (let q = 0; q < s.length; q += 8) { d += `M${s[q]} ${s[q + 1]}`; for (let p = 2; p < 8; p += 2) d += ` L${s[q + p]} ${s[q + p + 1]}`; d += " Z"; } return d; };
const morph = (a, b, t) => toPath(a.map((v, i) => v + (b[i] - v) * t));
const clamp = (v, mn = 0, mx = 1) => Math.min(mx, Math.max(mn, v));
const formatTime = (sec) => { const w = Math.max(0, Math.round(sec)); return `${Math.floor(w / 60)}:${String(w % 60).padStart(2, "0")}`; };
const buildWaveform = (count, seed) => { let st = (seed >>> 0) + 0x9e3779b9; return Array.from({ length: count }, (_, i) => { st = (st * 1664525 + 1013904223) >>> 0; const noise = st / 0x100000000, env = Math.sin((Math.PI * (i + 0.5)) / count) ** 0.55, swell = 0.5 + 0.5 * Math.sin(i * 0.9 + seed); return Math.round(clamp(env * (0.3 + 0.5 * noise + 0.2 * swell), MIN_AMPLITUDE, 1) * 1000) / 1000; }); };
const pointOnPill = (dist, w, h) => { const r = h / 2, st = Math.max(0, w - h), arc = Math.PI * r, per = 2 * st + 2 * arc; let d = dist % per; if (d < 0) d += per; if (d < st) return [r + d, 0]; d -= st; if (d < arc) { const a = -Math.PI / 2 + d / r; return [w - r + r * Math.cos(a), r + r * Math.sin(a)]; } d -= arc; if (d < st) return [w - r - d, h]; d -= st; const a = Math.PI / 2 + d / r; return [r + r * Math.cos(a), r + r * Math.sin(a)]; };
const grupo = new Set();  // VoiceNoteGroup: al reproducir una nota se pausan las demás
const seedDe = (s) => { let h = 7; for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h % 1000; };
// Reproductor de nota de voz con el audio real de src. Devuelve el nodo .rui-voz.
export function voiceNote(src, { nombre = "", bars = 40 } = {}) {
  cargarCss("rui-media");
  const red = reduce(), m = SIZE, control = Math.round(m.height * CONTROL_RATIO), inset = Math.round((m.height - control) / 2);
  const raiz = document.createElement("div"); raiz.className = "rui-voz"; raiz.dataset.slot = "voice-note"; raiz.dataset.loading = "1";
  raiz.style.height = m.height + "px"; raiz.style.gap = m.gap + "px"; raiz.style.paddingLeft = inset + "px"; raiz.style.paddingRight = m.pad + "px";
  const fondo = document.createElement("div"); fondo.className = "rui-voz-fondo";
  const brillo = document.createElement("div"); brillo.className = "rui-voz-brillo"; brillo.setAttribute("aria-hidden", "true");
  const campo = document.createElement("div"); campo.className = "rui-voz-campo"; campo.style.filter = `blur(${m.height * BLUR_RATIO}px)`;
  const base = document.createElement("span"); base.className = "rui-voz-base"; campo.append(base);
  const nodos = BLOBS.map((b) => { const s = document.createElement("span"); s.className = "rui-voz-luz"; const z = b.size * m.height; s.style.cssText = `width:${z}px;height:${z}px;margin-left:${-z / 2}px;margin-top:${-z / 2}px;opacity:${b.alpha}`; campo.append(s); return s; });
  brillo.append(campo); brillo.style.mixBlendMode = temaOscuro() ? "screen" : "multiply";  // original: multiply en claro, screen en oscuro
  const btn = document.createElement("button"); btn.type = "button"; btn.className = "rui-voz-ctl"; btn.dataset.slot = "voice-note-control"; btn.style.width = btn.style.height = control + "px"; btn.disabled = true; btn.setAttribute("aria-label", "Reproducir nota de voz");
  const isz = Math.round(control * ICON_RATIO); btn.innerHTML = `<svg viewBox="0 0 24 24" width="${isz}" height="${isz}" aria-hidden="true"><path d="${toPath(PLAY_SHAPE)}" fill="currentColor" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" stroke-linecap="round"/></svg>`;
  const path = btn.querySelector("path");
  const pista = document.createElement("div"); pista.className = "rui-voz-pista"; pista.dataset.slot = "voice-note-track"; pista.setAttribute("role", "slider"); pista.tabIndex = 0; pista.setAttribute("aria-label", "Avanzar en la nota de voz"); pista.setAttribute("aria-valuemin", "0");
  const amps = buildWaveform(bars, seedDe(nombre || src));
  const barras = (cls) => { const f = document.createElement("div"); f.className = "rui-voz-barras " + cls; f.style.gap = m.barGap + "px"; amps.forEach((a) => { const s = document.createElement("span"); s.style.minWidth = m.bar + "px"; s.style.height = (a * PEAK_RATIO * 100).toFixed(2) + "%"; f.append(s); }); return f; };
  const llena = document.createElement("div"); llena.className = "rui-voz-llena"; llena.setAttribute("aria-hidden", "true"); llena.append(barras("on")); llena.style.clipPath = "inset(0 100% 0 0)";
  pista.append(barras("off"), llena);
  const tiempo = document.createElement("button"); tiempo.type = "button"; tiempo.className = "rui-voz-tiempo"; tiempo.dataset.slot = "voice-note-time";
  const tTxt = document.createElement("span"); tTxt.textContent = "0:00"; const tVel = document.createElement("span"); tVel.className = "rui-voz-vel"; tVel.hidden = true; tiempo.append(tTxt, tVel);
  const audio = document.createElement("audio"); audio.preload = "metadata"; audio.hidden = true; audio.src = src;
  raiz.append(fondo, brillo, btn, pista, tiempo, audio);
  let total = 0, playing = false, speed = 1, frame = 0, scrub = false, iconAnim = 0;
  const pintarTiempo = () => { const el = Math.floor(audio.currentTime || 0); tTxt.textContent = formatTime(total - el); pista.setAttribute("aria-valuemax", String(Math.round(total))); pista.setAttribute("aria-valuenow", String(el)); pista.setAttribute("aria-valuetext", `${formatTime(el)} de ${formatTime(total)}`); tiempo.setAttribute("aria-label", `Velocidad ${speed}x. Toca para cambiar`); };
  const progreso = (p) => { llena.style.clipPath = `inset(0 ${(1 - clamp(p)) * 100}% 0 0)`; };
  const icono = (aPausa) => {
    cancelAnimationFrame(iconAnim); const from = aPausa ? PLAY_SHAPE : PAUSE_SHAPE, to = aPausa ? PAUSE_SHAPE : PLAY_SHAPE;
    if (red) { path.setAttribute("d", toPath(to)); return; }
    const t0 = performance.now(), dur = 340; const paso = (now) => { const t = clamp((now - t0) / dur), k = 1 - Math.pow(1 - t, 3) * Math.cos(t * Math.PI * 0.4); path.setAttribute("d", morph(from, to, clamp(k))); if (t < 1) iconAnim = requestAnimationFrame(paso); else path.setAttribute("d", toPath(to)); }; iconAnim = requestAnimationFrame(paso);
  };
  const fijar = (sig) => {
    if (sig === playing) return; playing = sig; raiz.toggleAttribute("data-playing", sig); brillo.style.opacity = String(sig ? PLAYING_GLOW : 0); btn.setAttribute("aria-label", sig ? "Pausar nota de voz" : "Reproducir nota de voz"); icono(sig);
    if (sig) { grupo.forEach((o) => o !== pausar && o()); audio.playbackRate = speed; audio.play().catch(() => fijar(false)); bucle(); arrancarLuz(); } else audio.pause();
  };
  const pausar = () => fijar(false); grupo.add(pausar);
  const bucle = () => { cancelAnimationFrame(frame); const tick = () => { if (!playing) return; progreso(total ? audio.currentTime / total : 0); pintarTiempo(); frame = requestAnimationFrame(tick); }; frame = requestAnimationFrame(tick); };
  const reiniciar = () => { audio.currentTime = 0; progreso(0); fijar(false); pintarTiempo(); };
  audio.addEventListener("loadedmetadata", () => { total = Number.isFinite(audio.duration) ? audio.duration : 0; if (!total) { audio.currentTime = 1e9; audio.addEventListener("timeupdate", function f() { audio.removeEventListener("timeupdate", f); total = Number.isFinite(audio.duration) ? audio.duration : 0; audio.currentTime = 0; listo(); }); return; } listo(); });
  const listo = () => { delete raiz.dataset.loading; btn.disabled = false; pista.classList.add("ok"); pintarTiempo(); };
  audio.addEventListener("error", () => { delete raiz.dataset.loading; raiz.dataset.error = "1"; btn.disabled = true; tTxt.textContent = "sin audio"; });
  audio.addEventListener("ended", reiniciar);
  btn.addEventListener("click", () => fijar(!playing));
  const ir = (r) => { if (!total) return; audio.currentTime = clamp(r) * total; progreso(clamp(r)); pintarTiempo(); };
  const rx = (e) => { const r = pista.getBoundingClientRect(); return r.width ? (e.clientX - r.left) / r.width : 0; };
  pista.addEventListener("pointerdown", (e) => { if (btn.disabled) return; pista.setPointerCapture(e.pointerId); scrub = true; ir(rx(e)); });
  pista.addEventListener("pointermove", (e) => { if (scrub) ir(rx(e)); });
  pista.addEventListener("pointerup", () => { scrub = false; }); pista.addEventListener("pointercancel", () => { scrub = false; });
  pista.addEventListener("keydown", (e) => { if (btn.disabled || !total) return; const at = audio.currentTime, to = { ArrowLeft: at - SEEK_STEP, ArrowRight: at + SEEK_STEP, Home: 0, End: total }[e.key]; if (to === undefined) return; e.preventDefault(); ir(to / total); });
  tiempo.addEventListener("click", () => { speed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]; audio.playbackRate = speed; tVel.hidden = speed === 1; tVel.textContent = speed + "×"; pintarTiempo(); });
  // Aurora: luces que recorren el borde de la píldora solo mientras suena
  let reloj = START_AT, rate = 0, ancho = 0, luz = 0;
  const colocar = (t) => { if (!ancho) return; const per = 2 * Math.max(0, ancho - m.height) + Math.PI * m.height; BLOBS.forEach((b, i) => { const [x, y] = pointOnPill((b.offset + t / b.lap) * per, ancho, m.height), esc = 1 + Math.sin(t * PULSE_SPEED + b.offset * Math.PI * 2) * b.pulse; nodos[i].style.transform = `translate(${x}px, ${y}px) scale(${esc})`; }); };
  if (typeof ResizeObserver === "function") new ResizeObserver(([en]) => { ancho = en.contentRect.width; colocar(reloj); }).observe(campo);
  const arrancarLuz = () => { if (red || luz) return; let last = performance.now(); const loop = (now) => { const d = Math.min(0.05, (now - last) / 1000); last = now; rate += ((playing ? 1 : 0) - rate) * (1 - Math.exp(-d / SPIN_UP)); reloj += d * rate; colocar(reloj); if ((playing || rate > 0.002) && raiz.isConnected) { luz = requestAnimationFrame(loop); return; } rate = 0; luz = 0; }; luz = requestAnimationFrame(loop); };
  new MutationObserver((_, o) => { if (!raiz.isConnected && raiz.dataset.vista) { fijar(false); grupo.delete(pausar); o.disconnect(); } }).observe(document.body, { childList: true, subtree: true });
  requestAnimationFrame(() => { raiz.dataset.vista = "1"; });
  return raiz;
}
