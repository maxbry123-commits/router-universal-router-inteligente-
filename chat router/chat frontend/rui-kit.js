// rui-kit.js — RUI 1-15 y 17-21 de Rare UI (swamimalode07/rare-ui @1d572f4, components/ui/*.tsx) llevados a JS simple sin React.
// Se conservan constantes, tiempos y geometría originales; colores = tokens del tema. RUI 16 y 22 viven en rui-media.js.
// Créditos: Rare UI (https://github.com/swamimalode07/rare-ui), con atribución según su licencia.
// Diferencias declaradas: sin framer-motion (resortes propios), code-block con resaltado mínimo (sin Prism), emoji-reaction con emoji nativo (sin CDN externo).
import { cargarCss } from "./ventanas-comun.js";
const SVGNS = "http://www.w3.org/2000/svg";
const h = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const s = (tag, attrs) => { const e = document.createElementNS(SVGNS, tag); for (const k in attrs || {}) e.setAttribute(k, attrs[k]); return e; };
const btn = (cls, txt, fn) => { const b = h("button", cls, txt); b.type = "button"; if (fn) b.addEventListener("click", fn); return b; };
const reduce = () => { try { return matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; } };
const css = () => cargarCss("rui-kit");
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
// resorte (stiffness/damping/mass o duration/bounce como framer-motion) sobre un objeto de números
function spring(from, opts, onUpdate) {
  let k = opts.stiffness, c = opts.damping, m = opts.mass || 1;
  if (k == null) { const d = opts.duration || 0.5, b = opts.bounce || 0; k = Math.pow((2 * Math.PI) / d, 2) * m; c = (1 - b) * 2 * Math.sqrt(k * m); }
  const cur = { ...from }, vel = {}, goal = { ...from }; let raf = 0, last = 0, delayUntil = 0;
  for (const key in cur) vel[key] = 0;
  const step = (now) => {
    if (now < delayUntil) { raf = requestAnimationFrame(step); return; }
    const dt = Math.min((now - (last || now)) / 1000, 0.032) || 0.016; last = now; let moving = false;
    for (const key in goal) { const f = -k * (cur[key] - goal[key]) - c * vel[key]; vel[key] += (f / m) * dt; cur[key] += vel[key] * dt; if (Math.abs(vel[key]) > 0.01 || Math.abs(cur[key] - goal[key]) > 0.01) moving = true; else { cur[key] = goal[key]; vel[key] = 0; } }
    onUpdate(cur); raf = moving ? requestAnimationFrame(step) : 0;
  };
  return { to(next, delay = 0) { Object.assign(goal, next); if (reduce()) { Object.assign(cur, goal); onUpdate(cur); return; } delayUntil = performance.now() + delay * 1000; if (!raf) { last = 0; raf = requestAnimationFrame(step); } }, kick(key, v) { vel[key] += v; if (!raf) { last = 0; raf = requestAnimationFrame(step); } }, get: () => cur, stop() { cancelAnimationFrame(raf); raf = 0; } };
}

// ---------- RUI 1 folder-component ----------
const FLAP = "M0 25C0 11.1929 11.1929 0 25 0H136.084C143.044 0 149.689 2.90139 154.42 8.00608L178.08 33.5343C182.811 38.639 189.456 41.5404 196.416 41.5404H296C309.807 41.5404 321 52.7333 321 66.5404V216C321 229.807 309.807 241 296 241H25C11.1929 241 0 229.807 0 216V25Z";
const CARD_POS = [ // [cerrada, hover, abierta] → {y,x,rot}, delay abierta/hover
  { c: [-10, 40, 10], hv: [-30, 40, 14], o: [-160, 70, 18], d: [0.1, 0.12] },
  { c: [-20, 3, 2], hv: [-35, 3, -1], o: [-180, 0, -3], d: [0.05, 0.06] },
  { c: [-22, -40, -5], hv: [-44, -40, -9], o: [-170, -65, -14], d: [0, 0] }];
export function folder({ size = "md" } = {}) {
  css(); const scale = { sm: 0.65, md: 1, lg: 1.35 }[size] || 1;
  const root = h("div", "rui-k rui-folder"); root.dataset.slot = "folder"; root.style.width = 321 * scale + "px"; root.style.height = 270 * scale + "px";
  root.tabIndex = 0; root.setAttribute("role", "button"); root.setAttribute("aria-label", "Carpeta"); root.setAttribute("aria-expanded", "false");
  const inner = h("div", "rui-folder-in"); inner.style.transform = `translate(-50%,-50%) scale(${scale})`; inner.style.perspective = 800 * scale + "px";
  const cards = h("div", "rui-folder-cards"); inner.append(h("div", "rui-folder-back"), cards);
  const springs = CARD_POS.map((p) => {
    const c = h("div", "rui-folder-card"), svg = s("svg", { width: 164, height: 214, viewBox: "0 0 164 214", fill: "none" });
    svg.append(s("rect", { width: 163.078, height: 213.262, rx: 20, fill: "var(--text)" }), s("rect", { x: 14.1193, y: 31.2091, width: 134.84, height: 11.8892, rx: 5.94459, fill: "var(--muted)" }));
    [[14.8, 61], [84.4, 61], [14.8, 75.1], [84.4, 75.1], [14.8, 89.2]].forEach(([x, y]) => svg.append(s("rect", { x, y, width: 64.5183, height: 5.88276, rx: 2.94138, fill: "var(--muted)" })));
    c.append(svg); cards.append(c);
    return spring({ y: p.c[0], x: p.c[1], r: p.c[2] }, { stiffness: 120, damping: 13 }, (v) => { c.style.transform = `translate(${v.x}px,${v.y}px) rotate(${v.r}deg)`; });
  });
  const flap = h("div", "rui-folder-flap"), blur = h("div"); blur.style.clipPath = `path('${FLAP}')`; blur.style.webkitClipPath = `path('${FLAP}')`;
  const fsvg = s("svg", { width: 321, height: 241, viewBox: "0 0 321 241", fill: "none" });
  fsvg.append(s("path", { d: FLAP, fill: "var(--surface)", "fill-opacity": 0.55 }), s("path", { d: FLAP, stroke: "var(--border-strong,var(--border))", fill: "none" }));
  flap.append(blur, fsvg); inner.append(flap); root.append(inner);
  const fs = spring({ rx: -15 }, { stiffness: 120, damping: 14 }, (v) => { flap.style.transform = `translate(-50%,-50%) rotateX(${v.rx}deg)`; });
  let hov = false, open = false;
  const apply = () => { root.setAttribute("aria-expanded", String(open)); CARD_POS.forEach((p, i) => { const t = open ? p.o : hov ? p.hv : p.c; springs[i].to({ y: t[0], x: t[1], r: t[2] }, open ? p.d[0] : hov ? p.d[1] : 0); }); fs.to({ rx: open ? -55 : hov ? -45 : -15 }); };
  CARD_POS.forEach((p, i) => springs[i].to({}));
  springs.forEach((sp) => { const v = sp.get(); sp.to(v); });
  fs.to({ rx: -15 });
  root.addEventListener("mouseenter", () => { hov = true; apply(); });
  root.addEventListener("mouseleave", () => { hov = false; open = false; apply(); });
  root.addEventListener("click", () => { open = !open; apply(); });
  root.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open = !open; apply(); } });
  return root;
}

// ---------- RUI 2 bounce-sidebar ----------
export function bounceSidebar(items, { value = 0, onChange, dotColor = "var(--active)" } = {}) {
  css(); const ul = h("ul", "rui-k rui-bounce"), dot = h("span", "rui-bounce-dot"), lis = []; let active = value, prevY = null, anim = 0;
  const size = Math.round(6 * (devicePixelRatio || 1)) / (devicePixelRatio || 1); dot.style.cssText = `width:${size}px;height:${size}px;background:${dotColor};opacity:0`; dot.setAttribute("aria-hidden", "true"); ul.append(dot);
  const yOf = (li) => { const d = devicePixelRatio || 1; return Math.round((li.offsetTop + li.offsetHeight / 2 - size / 2) * d) / d; };
  const move = (toY) => {
    if (prevY === null || reduce()) { dot.style.transform = `translate(0,${toY}px)`; prevY = toY; dot.style.opacity = 1; return; }
    const from = prevY, delta = toY - from; prevY = toY; if (!delta) return;
    const strength = Math.min(0.8, 14 / Math.abs(delta)), dir = delta > 0 ? 1 : -1, t0 = performance.now(); cancelAnimationFrame(anim);
    const f = (now) => { const t = Math.min(1, (now - t0) / 250), e = 1 - Math.pow(1 - t, 2), y = from + delta * e, x = -dir * Math.sin(Math.PI * e) * Math.abs(delta) * strength * 0.5; dot.style.transform = `translate(${x}px,${y}px)`; if (t < 1) anim = requestAnimationFrame(f); };
    anim = requestAnimationFrame(f);
  };
  const sync = () => { lis.forEach((li, i) => { const b = li.querySelector("button"); if (b) b.dataset.active = String(i === active); }); if (lis[active]) move(yOf(lis[active])); };
  items.forEach((it, i) => {
    const label = typeof it === "string" ? it : it.label, li = h("li");
    if (typeof it !== "string" && it.heading) { li.className = "rui-bounce-h"; li.textContent = label; li.style.color = dotColor; li.setAttribute("role", "presentation"); }
    else li.append(btn("", label, () => { active = i; sync(); onChange && onChange(i); }));
    lis.push(li); ul.append(li);
  });
  requestAnimationFrame(() => { prevY = null; sync(); });
  ul.setValue = (i) => { active = i; sync(); };
  return ul;
}

// ---------- RUI 3 hook-sidebar ----------
export function hookSidebar(items, { label, value = 0, onChange, color = "var(--active)", dashed = true } = {}) {
  css(); const CORNER = 6, DASH = "repeating-linear-gradient(to top, transparent 0 2px, currentColor 2px 4px)";
  const nav = h("nav", "rui-k rui-hook"); if (label) { nav.setAttribute("aria-label", label); nav.append(h("span", "rui-hook-lbl", label)); }
  const list = h("div", "rui-hook-list"); nav.append(list);
  const rail = (cls, col) => { const r = h("span", "rui-hook-rail" + (cls ? " " + cls : "")), line = h("span", "rui-hook-line"), svg = s("svg", { width: 12, height: 7, viewBox: "0 0 12 7", fill: "none" }); r.style.color = col; r.style.opacity = 0; line.style[dashed ? "backgroundImage" : "backgroundColor"] = dashed ? DASH : "currentColor"; svg.append(s("path", { d: "M0.5 0a6 6 0 0 0 6 6H12", stroke: "currentColor", "stroke-dasharray": dashed ? "2 2" : "none" })); r.append(line, svg); list.append(r);
    const sp = spring({ top: 0, y: 0 }, { stiffness: 420, damping: 34, mass: 0.7 }, (v) => { line.style.top = v.top + "px"; line.style.height = Math.max(0, v.y - CORNER - v.top) + "px"; svg.style.top = v.y - CORNER + "px"; }); return { r, sp }; };
  const hover = rail("", "color-mix(in srgb,var(--text) 30%,transparent)"), act = rail("", color); let active = value, hi = null, inside = false; const rows = [];
  const center = (i) => rows[i].offsetTop + rows[i].offsetHeight / 2;
  const sync = () => {
    rows.forEach((b, i) => { b.dataset.active = String(i === active); });
    const ay = center(active); act.sp.to({ top: 0, y: ay }); act.r.style.opacity = 1;
    if (hi !== null && inside && hi !== active) { const hy = center(hi), from = hy <= ay ? Math.max(0, hy - CORNER) : ay; hover.sp.to({ top: from, y: hy }); hover.r.style.opacity = 1; } else hover.r.style.opacity = 0;
  };
  items.forEach((it, i) => { const b = btn("", typeof it === "string" ? it : it.label, () => { active = i; sync(); onChange && onChange(i); }); b.addEventListener("mouseenter", () => { hi = i; inside = true; sync(); }); b.addEventListener("focus", () => { hi = i; inside = true; sync(); }); b.addEventListener("blur", () => { inside = false; sync(); }); rows.push(b); list.append(b); });
  list.addEventListener("mouseleave", () => { inside = false; sync(); });
  new ResizeObserver(() => { const y = center(active); act.sp.to({ y }); sync(); }).observe(list);
  return nav;
}

// ---------- RUI 4 family-drawer ----------
// views: { id: (go) => Node }, la vista "default" abre primero. La altura se anima al alto real de la vista.
export function familyDrawer(views, { trigger = "Abrir" } = {}) {
  css(); const t = btn("rui-k pill", trigger); let ov, dr, cur, prevH = null;
  const close = () => { if (!dr) return; ov.classList.remove("on"); dr.classList.remove("on"); const a = ov, b = dr; ov = dr = null; setTimeout(() => { a.remove(); b.remove(); }, 500); };
  const go = (id) => {
    const nv = h("div", "rui-fd-v"); nv.append(views[id](go, close)); const old = cur; cur = nv;
    dr.append(nv); const nh = nv.offsetHeight, dur = prevH ? clamp(Math.abs(nh - prevH) / 500, 0.15, 0.27) : 0.15; prevH = nh;
    const ease = "cubic-bezier(.26,.08,.25,1)"; dr.style.height = nh + "px";
    if (old) { old.style.cssText = `position:absolute;left:0;right:0;top:0;transition:opacity ${dur}s ${ease},transform ${dur}s ${ease}`; requestAnimationFrame(() => { old.style.opacity = 0; old.style.transform = "scale(.96)"; }); setTimeout(() => old.remove(), dur * 1000); }
    nv.style.cssText = `opacity:0;transform:scale(.96);transition:opacity ${dur}s ${ease},transform ${dur}s ${ease}`; requestAnimationFrame(() => requestAnimationFrame(() => { nv.style.opacity = 1; nv.style.transform = "none"; }));
  };
  t.addEventListener("click", () => {
    ov = h("div", "rui-k rui-fd-ov"); dr = h("div", "rui-k rui-fd"); dr.setAttribute("role", "dialog"); dr.setAttribute("aria-modal", "true"); dr.tabIndex = -1; prevH = null; cur = null;
    const x = btn("rui-fd-x", "✕", close); x.setAttribute("aria-label", "Cerrar"); dr.append(x); ov.addEventListener("click", close);
    document.body.append(ov, dr); go("default"); requestAnimationFrame(() => { ov.classList.add("on"); dr.classList.add("on"); dr.focus(); });
    dr.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  });
  return t;
}

// ---------- RUI 5 proximity-sidebar ----------
const DASH_P = { title: [40, 70], subtitle: [36, 64], section: [30, 56], body: [24, 50] };
export function proximitySidebar(sections, { side = "left", scroller } = {}) {
  css(); const RADIUS = 40, MAX = 110, nav = h("nav", "rui-k rui-prox"); nav.dataset.side = side; nav.setAttribute("aria-label", "Secciones");
  const tip = h("span", "rui-prox-tip"); nav.append(tip); let mouseY = -1e4, activeId = sections[0] && sections[0].id;
  const kind = (sec) => sec.kind || ({ 1: "title", 2: "subtitle", 3: "section" }[sec.level] || "body");
  const dashes = sections.map((sec) => { const b = btn("rui-prox-dash"), bar = h("span"), k = kind(sec), [base, bump] = DASH_P[k]; b.dataset.kind = k; b.setAttribute("aria-label", sec.label); b.append(bar); nav.append(b);
    const sp = spring({ sx: base / MAX }, { stiffness: 300, damping: 30 }, (v) => { bar.style.transform = `scaleX(${v.sx})`; });
    b.addEventListener("click", () => { const t = document.getElementById(sec.id); if (t) t.scrollIntoView({ behavior: reduce() ? "auto" : "smooth", block: "start" }); });
    b.addEventListener("mouseenter", () => { tip.textContent = sec.label; tip.style.top = b.offsetTop + b.offsetHeight / 2 + "px"; tip.style.opacity = 1; });
    b.addEventListener("mouseleave", () => { tip.style.opacity = 0; });
    return { sec, b, sp, base, bump }; });
  const upd = () => dashes.forEach((d) => { const r = d.b.getBoundingClientRect(), dist = mouseY - (r.top + r.height / 2), near = Math.max(0, 1 - Math.abs(dist) / RADIUS), on = d.sec.id === activeId; d.b.dataset.active = String(on); d.sp.to({ sx: (on ? d.base + d.bump : d.base + d.bump * near) / MAX }); });
  nav.addEventListener("pointermove", (e) => { mouseY = e.clientY; upd(); }); nav.addEventListener("pointerleave", () => { mouseY = -1e4; upd(); });
  const sc = scroller || window; const onScroll = () => { const top = (scroller ? scroller.getBoundingClientRect().top : 0) + 80; let a = sections[0]; for (const sec of sections) { const el = document.getElementById(sec.id); if (el && el.getBoundingClientRect().top <= top) a = sec; } if (a && a.id !== activeId) { activeId = a.id; upd(); } };
  sc.addEventListener("scroll", onScroll, { passive: true }); requestAnimationFrame(() => { onScroll(); upd(); });
  return nav;
}

// ---------- RUI 6 duration-picker ----------
const PEN = "M3.78181 16.3092L3 21L7.69086 20.2182C8.50544 20.0825 9.25725 19.6956 9.84119 19.1116L20.4198 8.53288C21.1934 7.75922 21.1934 6.50489 20.4198 5.73123L18.2688 3.58023C17.4951 2.80657 16.2408 2.80657 15.4671 3.58023L4.88851 14.1588C4.30457 14.7428 3.91761 15.4946 3.78181 16.3092Z";
const TICK = "M7.959 20.513L1.592 12.872L3.128 11.592L8.041 17.487L20.947 3.587L22.413 4.948L7.959 20.513Z";
export function durationPicker({ value = { hours: 1, minutes: 30 }, maxHours = 24, maxMinutes = 59, hoursLabel = "Hr.", minutesLabel = "Min.", onConfirm } = {}) {
  css(); const root = h("div", "rui-k rui-dur"), meas = h("span", "rui-meas"); let editing = false;
  const field = (v, unit, max, aria) => { const seg = h("div", "rui-dur-seg"), inp = h("input"); inp.inputMode = "numeric"; inp.value = String(v); inp.disabled = true; inp.setAttribute("aria-label", aria); inp.maxLength = 2;
    const fit = () => { meas.textContent = inp.value || "0"; document.body.append(meas); inp.style.setProperty("--w", Math.max(meas.offsetWidth + 2, 12) + "px"); meas.remove(); };
    inp.addEventListener("input", () => { const raw = inp.value.replace(/\D/g, "").slice(0, 2); if (Number(raw) > max) { root.classList.remove("err"); void root.offsetWidth; root.classList.add("err"); inp.value = String(max); } else inp.value = raw; fit(); });
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") toggle(); });
    seg.append(inp, h("span", "rui-dur-u", unit)); requestAnimationFrame(fit); return { seg, inp, fit }; };
  const H = field(value.hours, hoursLabel, maxHours, "Horas"), M = field(value.minutes, minutesLabel, maxMinutes, "Minutos");
  const b = btn("rui-dur-btn"), svg = s("svg", { width: 18, height: 18, viewBox: "0 0 24 24" }), p = s("path", { d: PEN, fill: "none", stroke: "currentColor", "stroke-width": 1.8 }); svg.append(p); b.append(svg); b.setAttribute("aria-label", "Editar duración");
  const segB = h("div", "rui-dur-seg"); segB.style.padding = "0"; segB.append(b);
  function toggle() { editing = !editing; root.classList.toggle("edit", editing); H.inp.disabled = M.inp.disabled = !editing; p.setAttribute("d", editing ? TICK : PEN); p.setAttribute("fill", editing ? "currentColor" : "none"); p.setAttribute("stroke", editing ? "none" : "currentColor"); b.setAttribute("aria-label", editing ? "Confirmar duración" : "Editar duración");
    if (editing) { H.inp.focus(); H.inp.select(); } else { const v = { hours: clamp(Math.trunc(+H.inp.value) || 0, 0, maxHours), minutes: clamp(Math.trunc(+M.inp.value) || 0, 0, maxMinutes) }; H.inp.value = v.hours; M.inp.value = v.minutes; H.fit(); M.fit(); onConfirm && onConfirm(v); } }
  b.addEventListener("click", toggle); root.append(H.seg, M.seg, segB); return root;
}

// ---------- RUI 7 fluid-orb (shader original) ----------
const F_VERT = "attribute vec2 a_pos;void main(){gl_Position=vec4(a_pos,0.0,1.0);}";
const F_FRAG = `#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 u_resolution;uniform float u_time;uniform vec3 u_color;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
float noise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);vec2 u=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1.0,0.0)),u.x),mix(hash(i+vec2(0.0,1.0)),hash(i+vec2(1.0,1.0)),u.x),u.y);}
float fbm(vec2 p){float v=0.0;float a=0.6;for(int i=0;i<3;i++){v+=a*noise(p);p*=2.0;a*=0.5;}return v;}
void main(){vec2 uv=gl_FragCoord.xy/u_resolution.xy;float t=u_time*0.22;
vec2 drift=vec2(sin(t)+0.6*sin(t*1.7+1.3),cos(t*0.8)+0.6*cos(t*1.3+2.1));
vec2 p=vec2(uv.x*1.8,uv.y*1.0)+drift*0.7;vec2 q=vec2(fbm(p+drift),fbm(p+vec2(3.2,1.5)-drift));float f=fbm(p+1.2*q);
float g=clamp(1.0-uv.y,0.0,1.0);float anchor=smoothstep(0.0,0.3,uv.y);float shade=clamp(g+(f-0.5)*0.8*anchor,0.0,1.0);
vec3 white=vec3(0.99,1.0,1.0);vec3 light=mix(white,u_color,0.5);vec3 dark=u_color;vec3 col=white;
col=mix(col,light,smoothstep(0.28,0.52,shade));col=mix(col,dark,smoothstep(0.58,0.88,shade));
float edge=smoothstep(0.5,0.49,distance(uv,vec2(0.5)));gl_FragColor=vec4(col*edge,edge);}`;
const hexRgb = (hex) => { let x = String(hex).replace("#", "").trim(); if (x.length === 3) x = x.split("").map((c) => c + c).join(""); const n = parseInt(x, 16); return x.length !== 6 || isNaN(n) ? [0.1, 0.45, 0.95] : [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]; };
export function fluidOrb({ size = 240, color = "#1A73F2" } = {}) {
  css(); const root = h("div", "rui-k rui-orb"), c = h("canvas"); c.style.width = c.style.height = size + "px"; c.setAttribute("aria-hidden", "true"); root.append(c);
  const gl = c.getContext("webgl", { antialias: true, alpha: true }); if (!gl) { root.dataset.error = "sin WebGL"; return root; }
  const sh = (t, src) => { const x = gl.createShader(t); gl.shaderSource(x, src); gl.compileShader(x); return gl.getShaderParameter(x, gl.COMPILE_STATUS) ? x : null; };
  const pr = gl.createProgram(), v = sh(gl.VERTEX_SHADER, F_VERT), f = sh(gl.FRAGMENT_SHADER, F_FRAG); if (!v || !f) { root.dataset.error = "shader"; return root; }
  gl.attachShader(pr, v); gl.attachShader(pr, f); gl.linkProgram(pr); gl.useProgram(pr);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer()); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
  const a = gl.getAttribLocation(pr, "a_pos"); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
  gl.uniform3f(gl.getUniformLocation(pr, "u_color"), ...hexRgb(color));
  const px = Math.round(size * Math.min(devicePixelRatio || 1, 2)); c.width = c.height = px; gl.viewport(0, 0, px, px); gl.uniform2f(gl.getUniformLocation(pr, "u_resolution"), px, px);
  const uT = gl.getUniformLocation(pr, "u_time"), t0 = performance.now(), red = reduce();
  const r = (now) => { if (!root.isConnected && now - t0 > 2000) return; gl.uniform1f(uT, red ? 0 : (now - t0) / 1000); gl.drawArrays(gl.TRIANGLES, 0, 6); if (!red) requestAnimationFrame(r); }; r(t0);
  return root;
}

// ---------- RUI 8 scroll-progress ----------
export function scrollProgress(sections, { scroller, offset = 120 } = {}) {
  css(); const wrap = h("div", "rui-k rui-sp"), pill = h("div", "rui-sp-pill"), head = btn("rui-sp-head"), R = 9, C = 2 * Math.PI * R;
  const ring = s("svg", { width: 22, height: 22, viewBox: "0 0 22 22", class: "rui-sp-ring" }), bg = s("circle", { cx: 11, cy: 11, r: R, fill: "none", stroke: "var(--border)", "stroke-width": 2.5 }), fg = s("circle", { cx: 11, cy: 11, r: R, fill: "none", stroke: "var(--text)", "stroke-width": 2.5, "stroke-linecap": "round", transform: "rotate(-90 11 11)", "stroke-dasharray": C, "stroke-dashoffset": C });
  ring.append(bg, fg); const lbl = h("span", "rui-sp-lbl"); head.append(ring, lbl); head.setAttribute("aria-expanded", "false"); const list = h("div", "rui-sp-list"); list.hidden = true; pill.append(head, list); wrap.append(pill);
  let active = sections[0] && sections[0].id, open = false, lock = false, lockT; const sc = scroller || window;
  const prog = spring({ p: 0 }, { stiffness: 120, damping: 30, mass: 0.3 }, (v) => fg.setAttribute("stroke-dashoffset", C * (1 - clamp(v.p, 0, 1))));
  const items = sections.map((sec) => { const b = btn("", sec.label, () => { lock = true; clearTimeout(lockT); lockT = setTimeout(() => { lock = false; }, reduce() ? 0 : 700); active = sec.id; paint(); setOpen(false); const t = document.getElementById(sec.id); t && t.scrollIntoView({ behavior: reduce() ? "auto" : "smooth", block: "start" }); }); list.append(b); return [sec.id, b]; });
  const size = () => { pill.style.width = pill.scrollWidth + "px"; };
  const paint = () => { const sec = sections.find((x) => x.id === active); if (sec && lbl.textContent !== sec.label) { lbl.style.opacity = 0; setTimeout(() => { lbl.textContent = sec.label; lbl.style.opacity = 1; pill.style.width = "auto"; const w = pill.offsetWidth; pill.style.width = w + "px"; }, 110); } items.forEach(([id, b]) => { b.dataset.active = String(id === active); }); };
  const setOpen = (o) => { const w0 = pill.offsetWidth, h0 = pill.offsetHeight; open = o; list.hidden = !o; head.setAttribute("aria-expanded", String(o)); pill.style.width = pill.style.height = "auto"; const w1 = pill.offsetWidth, h1 = pill.offsetHeight; pill.style.width = w0 + "px"; pill.style.height = h0 + "px"; requestAnimationFrame(() => { pill.style.width = w1 + "px"; pill.style.height = h1 + "px"; }); };
  head.addEventListener("click", () => setOpen(!open));
  document.addEventListener("pointerdown", (e) => { if (open && !wrap.contains(e.target)) setOpen(false); }); document.addEventListener("keydown", (e) => { if (open && e.key === "Escape") setOpen(false); });
  const upd = () => { const el = scroller || document.documentElement, max = el.scrollHeight - el.clientHeight; prog.to({ p: max > 0 ? (scroller ? scroller.scrollTop : scrollY) / max : 0 }); if (lock) return; const anchor = (scroller ? scroller.getBoundingClientRect().top : 0) + offset; let a = sections[0]; for (const sec of sections) { const t = document.getElementById(sec.id); if (t && t.getBoundingClientRect().top <= anchor) a = sec; } if (a && a.id !== active) { active = a.id; paint(); } };
  sc.addEventListener("scroll", upd, { passive: true }); addEventListener("resize", upd);
  lbl.textContent = (sections[0] || {}).label || ""; requestAnimationFrame(() => { size(); pill.style.height = pill.offsetHeight + "px"; upd(); paint(); });
  return wrap;
}

// ---------- RUI 9 code-block ----------
const KW = /\b(const|let|var|function|return|if|else|for|while|import|from|export|default|new|class|extends|async|await|try|catch|throw|true|false|null|undefined|def|self|None|True|False)\b/;
function resaltar(line) {
  const out = document.createDocumentFragment(), re = /(\/\/.*$|#.*$)|("(?:\\.|[^"])*"|'(?:\\.|[^'])*'|`(?:\\.|[^`])*`)|(\b\d+(?:\.\d+)?\b)|(\b[A-Za-z_]\w*\b)/g; let i = 0, m;
  while ((m = re.exec(line))) { if (m.index > i) out.append(line.slice(i, m.index)); const cls = m[1] ? "t-c" : m[2] ? "t-s" : m[3] ? "t-n" : KW.test(m[4]) && m[4].match(KW)[0] === m[4] ? "t-k" : ""; if (cls) out.append(h("span", cls, m[0])); else out.append(m[0]); i = m.index + m[0].length; }
  if (i < line.length) out.append(line.slice(i)); return out;
}
export function codeBlock(code, { language = "js", filename, showLineNumbers = true, highlightLines = [] } = {}) {
  css(); const root = h("div", "rui-k rui-code"), head = h("div", "rui-code-h"), copy = btn("rui-code-copy"); root.dataset.slot = "code-block";
  const ico = (ok) => { copy.replaceChildren(); const sv = s("svg", { width: 15, height: 15, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }); if (ok) sv.append(s("path", { d: "M5 12l5 5L20 7" })); else { sv.append(s("rect", { x: 9, y: 9, width: 12, height: 12, rx: 2 }), s("path", { d: "M5 15V5a2 2 0 0 1 2-2h10" })); } copy.append(sv); copy.setAttribute("aria-label", ok ? "Copiado" : "Copiar código"); };
  ico(false); let t; copy.addEventListener("click", async () => { try { await navigator.clipboard.writeText(code); } catch (e) { const ta = h("textarea"); ta.value = code; document.body.append(ta); ta.select(); try { document.execCommand("copy"); } catch (_) {} ta.remove(); } ico(true); clearTimeout(t); t = setTimeout(() => ico(false), 1800); });
  head.append(h("span", "", filename || language), copy); const pre = h("pre"), cd = h("code");
  String(code).replace(/\n$/, "").split("\n").forEach((ln, i) => { const row = h("div", "rui-code-l" + (highlightLines.includes(i + 1) ? " hl" : "")); if (showLineNumbers) row.append(h("span", "rui-code-n", String(i + 1))); const tx = h("span"); tx.append(resaltar(ln)); row.append(tx); cd.append(row); });
  pre.append(cd); root.append(head, pre); return root;
}

// ---------- RUI 10 otp-input ----------
export function otpInput({ length = 6, type = "numbers", onComplete, mask = false } = {}) {
  css(); const PAT = { numbers: /^[0-9]$/, letters: /^[a-zA-Z]$/, both: /^[a-zA-Z0-9]$/ }[type]; const root = h("div", "rui-k rui-otp"); root.setAttribute("role", "group"); root.setAttribute("aria-label", "Código");
  const slots = Array(length).fill(""), cells = [];
  const paint = () => cells.forEach((c, i) => { const ch = slots[i], old = c.ch; c.caret.hidden = !(document.activeElement === c.inp && !ch); if (old.textContent !== (mask && ch ? "•" : ch)) { const n = h("span", "rui-otp-ch", mask && ch ? "•" : ch); n.style.transform = "translateY(110%)"; c.cell.append(n); requestAnimationFrame(() => { n.style.transform = "none"; }); old.style.transform = ch ? "translateY(-110%)" : "translateY(110%)"; old.style.opacity = 0; setTimeout(() => old.remove(), 280); c.ch = n; } });
  const commit = () => { root.dataset.status = "idle"; paint(); if (slots.every(Boolean)) onComplete && onComplete(slots.join(""), (st) => { root.dataset.status = st; if (st === "error") { root.animate([0, -5, 4, -2, 0].map((x) => ({ transform: `translateX(${x}px)` })), { duration: 350 }); } }); };
  const focusAt = (i) => { const c = cells[clamp(i, 0, length - 1)]; c.inp.focus(); c.inp.select(); };
  for (let i = 0; i < length; i++) {
    const cell = h("div", "rui-otp-cell"), inp = h("input"), ch = h("span", "rui-otp-ch"), caret = h("span", "rui-otp-caret"); caret.hidden = true;
    inp.inputMode = type === "numbers" ? "numeric" : "text"; inp.autocomplete = i ? "off" : "one-time-code"; inp.setAttribute("aria-label", `Dígito ${i + 1} de ${length}`);
    inp.addEventListener("input", () => { const v = inp.value.split("").filter((x) => PAT.test(x)); inp.value = ""; if (!v.length) return; v.slice(0, length - i).forEach((x, k) => { slots[i + k] = x; }); commit(); focusAt(i + v.length); });
    inp.addEventListener("keydown", (e) => { if (e.key === "Backspace") { e.preventDefault(); if (slots[i]) slots[i] = ""; else if (i) { slots[i - 1] = ""; focusAt(i - 1); } commit(); } else if (e.key === "ArrowLeft") focusAt(i - 1); else if (e.key === "ArrowRight") focusAt(i + 1); });
    inp.addEventListener("paste", (e) => { e.preventDefault(); const v = (e.clipboardData.getData("text") || "").split("").filter((x) => PAT.test(x)).slice(0, length); v.forEach((x, k) => { slots[k] = x; }); commit(); focusAt(v.length); });
    inp.addEventListener("focus", paint); inp.addEventListener("blur", () => setTimeout(paint));
    cell.append(inp, ch, caret); root.append(cell); cells.push({ cell, inp, ch, caret });
  }
  root.value = () => slots.join(""); return root;
}

// ---------- RUI 11 gravity-letters ----------
const POOLS = { letters: "ABCDEFGHIJKLMNOPQRSTUVWXYZ", numbers: "0123456789", both: "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" };
export function gravityLetters({ type = "letters", gravity = 800, maxGlyphs = 120, hint = "Toca para soltar letras · mantén para verter" } = {}) {
  css(); const COL = 8, CLEARANCE = 24, BOUNCE = 0.22, TILT = 26, HOLD_MS = 300, POUR_MS = 120;
  const root = h("div", "rui-k rui-grav"); root.setAttribute("role", "img"); root.setAttribute("aria-label", "Letras que caen"); const hintEl = h("div", "rui-grav-hint", hint); root.append(hintEl);
  let heights = [], bodies = [], raf = 0, last = 0, holdT, pourT;
  const cols = () => Math.ceil(root.clientWidth / COL);
  const spawn = (x) => {
    if (!heights.length) heights = Array(cols()).fill(0); hintEl.style.opacity = 0;
    if (bodies.length >= maxGlyphs) { const o = bodies.shift(); o.el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 350 }).onfinish = () => o.el.remove(); heights = Array(cols()).fill(0); bodies.forEach((b) => { if (b.rest) for (let c = b.c0; c <= b.c1; c++) heights[c] = Math.max(heights[c], root.clientHeight - b.y); }); }
    const el = h("span", "", POOLS[type][Math.floor(Math.random() * POOLS[type].length)]); root.append(el); const w = el.offsetWidth, ht = el.offsetHeight;
    const bx = clamp(x - w / 2, 0, root.clientWidth - w), c0 = Math.max(0, Math.floor(bx / COL)), c1 = Math.min(heights.length - 1, Math.floor((bx + w) / COL));
    let top = 0; for (let c = c0; c <= c1; c++) top = Math.max(top, heights[c]);
    const rot = (Math.random() * 2 - 1) * TILT, floor = root.clientHeight - top - ht, y = Math.min(-ht, floor - CLEARANCE - ht);
    bodies.push({ el, x: bx, y, vy: 0, w, h: ht, rot, floor, c0, c1, bounced: false, rest: false });
    for (let c = c0; c <= c1; c++) heights[c] = top + ht * 0.82; // reserva el hueco al nacer (orden de llegada)
    if (!raf) { last = 0; raf = requestAnimationFrame(tick); }
  };
  const tick = (now) => { const dt = Math.min((now - (last || now)) / 1000, 0.032); last = now; let moving = false;
    for (const b of bodies) { if (b.rest) continue; moving = true; b.vy += gravity * dt; b.y += b.vy * dt;
      if (b.y >= b.floor) { b.y = b.floor; const reb = -b.vy * BOUNCE; if (!b.bounced && reb * reb > gravity * 6) { b.vy = reb; b.bounced = true; } else { b.vy = 0; b.rest = true; b.el.animate([{ transform: `translate(${b.x}px,${b.y}px) rotate(${b.rot}deg) scale(1.08,.9)` }, { transform: `translate(${b.x}px,${b.y}px) rotate(${b.rot}deg)` }], { duration: 160, easing: "cubic-bezier(0.215,0.61,0.355,1)" }); } }
      b.el.style.transform = `translate(${b.x}px,${b.y}px) rotate(${b.rot * (b.rest ? 1 : clamp(b.vy / 600, 0, 1))}deg)`; }
    raf = moving ? requestAnimationFrame(tick) : 0; };
  const xOf = (e) => e.clientX - root.getBoundingClientRect().left;
  root.addEventListener("pointerdown", (e) => { const x = xOf(e); spawn(x); let px = x; const mv = (ev) => { px = xOf(ev); }; root.addEventListener("pointermove", mv); holdT = setTimeout(() => { pourT = setInterval(() => spawn(px + (Math.random() * 16 - 8)), POUR_MS); }, HOLD_MS);
    const up = () => { clearTimeout(holdT); clearInterval(pourT); root.removeEventListener("pointermove", mv); removeEventListener("pointerup", up); removeEventListener("pointercancel", up); }; addEventListener("pointerup", up); addEventListener("pointercancel", up); });
  root.spawn = spawn; return root;
}

// ---------- RUI 12 github-activity (datos reales: API pública de contribuciones + eventos de GitHub) ----------
export function githubActivity(login, { months = 12, cellSize = 11, accent = "#39d353" } = {}) {
  css(); const root = h("div", "rui-k rui-gh"), gap = Math.max(2, Math.round(cellSize / 4)), head = h("div", "rui-gh-h", "Contribuciones de " + login + " · cargando…"), grid = h("div", "rui-gh-grid"), reps = h("div");
  grid.style.setProperty("--c", cellSize + "px"); grid.style.setProperty("--g", gap + "px"); root.append(head, grid, reps); root.setAttribute("aria-busy", "true");
  const OP = [0, 0.3, 0.55, 0.8, 1], weeks = Math.ceil(months * (365.25 / 12 / 7));
  fetch(`https://github-contributions-api.jogruber.de/v4/${encodeURIComponent(login)}?y=last`).then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); }).then((j) => {
    const days = (j && j.contributions) || []; const start = days.findIndex((d) => new Date(d.date).getDay() === 0); const ds = days.slice(Math.max(0, start)).slice(-weeks * 7); const total = ds.reduce((a, d) => a + d.count, 0);
    head.textContent = `${total} contribuciones en ${months} meses · ${login}`;
    ds.forEach((d, i) => { const c = h("i"); c.title = `${d.count} contribuciones · ${d.date}`; if (d.level) { c.style.background = accent; c.style.opacity = 0; c.dataset.op = OP[d.level]; } grid.append(c); setTimeout(() => { c.classList.add("on"); if (d.level) c.style.opacity = OP[d.level]; }, reduce() ? 0 : Math.floor(i / 7) * 12); });
    grid.scrollLeft = grid.scrollWidth; root.removeAttribute("aria-busy");
  }).catch((e) => { head.textContent = "Contribuciones de " + login; root.append(h("div", "rui-gh-err", "No se pudo leer la actividad (" + e.message + ").")); });
  fetch(`https://api.github.com/users/${encodeURIComponent(login)}/events/public?per_page=100`).then((r) => (r.ok ? r.json() : [])).then((ev) => {
    const m = {}; (ev || []).forEach((e) => { if (e.type === "PushEvent") { const n = e.repo.name; m[n] = (m[n] || 0) + ((e.payload && e.payload.size) || 1); } });
    Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 3).forEach(([n, c], i) => { const row = h("div", "rui-gh-rep"); row.append(h("span", "", n), h("span", "", c + " commits")); reps.append(row); setTimeout(() => row.classList.add("on"), 80 + i * 80); });
  }).catch(() => {});
  return root;
}

// ---------- RUI 13 emoji-reaction ----------
export function emojiReaction({ emojis = ["🥰", "🤩", "😕", "🥺", "😄"], onReact } = {}) {
  css(); const BURST = 5, HOLD = 550, MAXP = 60, RISE = 450; const root = h("div", "rui-k rui-emo"), trig = btn("rui-emo-trig"), bar = h("div", "rui-emo-bar"), cnt = h("span", "rui-emo-cnt"), counts = {};
  trig.setAttribute("aria-label", "Reaccionar"); trig.setAttribute("aria-expanded", "false"); trig.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>';
  const toggle = (o) => { bar.classList.toggle("on", o); trig.setAttribute("aria-expanded", String(o)); };
  trig.addEventListener("click", () => toggle(!bar.classList.contains("on")));
  document.addEventListener("pointerdown", (e) => { if (!root.contains(e.target)) toggle(false); });
  const burst = (em, from) => { if (reduce()) return; const br = root.getBoundingClientRect(), fr = from.getBoundingClientRect(); for (let i = 0; i < BURST; i++) { if (root.querySelectorAll(".rui-emo-p").length >= MAXP) break; const p = h("span", "rui-emo-p", em), lane = Math.random() * 2 - 1, dur = 1400 + Math.random() * 400; p.style.left = fr.left - br.left + fr.width / 2 - 11 + "px"; p.style.top = fr.top - br.top + "px"; root.append(p); const dx = lane * 78, rise = RISE * (0.7 + Math.random() * 0.3);
      p.animate([{ transform: "translate(0,0) scale(.6)", opacity: 1 }, { transform: `translate(${dx * 0.3}px,${-rise * 0.35}px) scale(1)`, opacity: 1, offset: 0.3 }, { transform: `translate(${dx * 0.65}px,${-rise * 0.7}px) scale(1)`, opacity: 0.8, offset: 0.65 }, { transform: `translate(${dx}px,${-rise}px) scale(.9)`, opacity: 0 }], { duration: dur, easing: "cubic-bezier(.4,.3,.5,1)" }).onfinish = () => p.remove(); } };
  const paintCnt = () => { cnt.replaceChildren(...Object.entries(counts).map(([e, n]) => h("span", "", e + " " + n))); };
  emojis.forEach((em) => { const b = btn("", em); b.setAttribute("aria-label", "Reaccionar " + em); let iv;
    const fire = () => { counts[em] = (counts[em] || 0) + 1; paintCnt(); burst(em, b); onReact && onReact(em); };
    b.addEventListener("pointerdown", () => { fire(); iv = setInterval(fire, HOLD); }); const stop = () => clearInterval(iv); b.addEventListener("pointerup", stop); b.addEventListener("pointerleave", stop); b.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fire(); } }); bar.append(b); });
  root.append(bar, trig, cnt); return root;
}

// ---------- RUI 14 notification-bell ----------
export function notificationBell({ size = 40, count = 0, onClick } = {}) {
  css(); const b = btn("rui-k rui-bell"), ICON = 0.56, BADGE = 0.38, FONT = 0.21; b.style.width = b.style.height = size + "px";
  const sv = s("svg", { width: size * ICON, height: size * ICON, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" });
  const body = s("path", { d: "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" }), clap = s("path", { d: "M10.3 21a1.94 1.94 0 0 0 3.4 0" }); sv.append(body, clap); b.append(sv);
  const badge = h("span", "rui-bell-badge"), side = size * BADGE; badge.style.cssText = `min-width:${side}px;height:${side}px;font-size:${size * FONT}px;padding:0 ${size * 0.09}px;top:${-side * 0.2}px;right:${-side * 0.2}px`; b.append(badge);
  const sw = spring({ a: 0, c: 0 }, { stiffness: 220, damping: 8, mass: 1 }, (v) => { sv.style.transform = `rotate(${v.a}deg)`; clap.style.transform = `translateX(${clamp(v.c, -13, 13) * 0.12}px)`; });
  let total = count; const paint = () => { badge.textContent = total > 99 ? "99+" : String(total); badge.classList.toggle("on", total > 0); b.setAttribute("aria-label", total ? `Notificaciones: ${total} sin leer` : "Notificaciones"); };
  b.set = (n) => { const d = n - total; total = Math.max(0, n); paint(); if (d > 0 && !reduce()) { const w = 0.7 + (0.6 * Math.min(d, 5)) / 5; sw.kick("a", clamp(500 * w, -900, 900) * (Math.random() < 0.5 ? -1 : 1)); sw.kick("c", 450 * w); sw.to({ a: 0, c: 0 }); } };
  if (onClick) b.addEventListener("click", onClick); paint(); return b;
}

// ---------- RUI 15 step-player ----------
export function stepPlayer({ steps = 4, duration = 4000, loop = false, size = 12, onStep } = {}) {
  css(); const root = h("div", "rui-k rui-step"), b = btn("rui-step-btn"), track = h("div", "rui-step-track"), dot = Math.max(2, Math.round(Math.max(12, size) * 0.115)) * 2;
  track.style.setProperty("--dot", dot + "px"); track.style.setProperty("--gap", Math.round(dot * 0.9) + "px"); root.setAttribute("role", "group"); root.setAttribute("aria-label", "Reproductor de pasos");
  const PATHS = { play: "M9.8 7 L17.7 12 L9.8 17 Z", pause: "M8.4 5.9 L10.4 5.9 L10.4 18.1 L8.4 18.1 Z M13.6 5.9 L15.6 5.9 L15.6 18.1 L13.6 18.1 Z", replay: "M12 5V2L7 6l5 4V7a5 5 0 1 1-5 5H5a7 7 0 1 0 7-7z" };
  const sv = s("svg", { width: 24, height: 24, viewBox: "0 0 24 24" }), p = s("path", { fill: "currentColor" }); sv.append(p); b.append(sv);
  const segs = Array.from({ length: steps }, () => { const g = h("span", "rui-step-seg"), i = h("i"); g.append(i); track.append(g); return g; });
  let idx = 0, playing = false, t0 = 0, done = 0, raf = 0;
  const icon = (st) => { if (p.getAttribute("d") === PATHS[st]) return; sv.animate([{ transform: "scale(.82)", opacity: 0.2 }, { transform: "scale(1)", opacity: 1 }], { duration: 260, easing: "cubic-bezier(.32,.72,0,1)" }); p.setAttribute("d", PATHS[st]); b.setAttribute("aria-label", st === "play" ? "Reproducir" : st === "pause" ? "Pausar" : "Repetir"); };
  const paint = (prog) => segs.forEach((g, i) => { g.classList.toggle("cur", i === idx); g.classList.toggle("done", i < idx); g.firstChild.style.width = i === idx ? prog * 100 + "%" : ""; });
  const frame = (now) => { const prog = clamp((done + now - t0) / duration, 0, 1); paint(prog); if (prog >= 1) { if (idx < steps - 1) { idx++; done = 0; t0 = now; onStep && onStep(idx); } else if (loop) { idx = 0; done = 0; t0 = now; onStep && onStep(0); } else { playing = false; paint(1); segs[idx].classList.add("done"); icon("replay"); return; } } raf = requestAnimationFrame(frame); };
  b.addEventListener("click", () => { if (!playing && idx === steps - 1 && p.getAttribute("d") === PATHS.replay) { idx = 0; done = 0; segs.forEach((g) => g.classList.remove("done")); }
    playing = !playing; if (playing) { t0 = performance.now(); raf = requestAnimationFrame(frame); icon("pause"); } else { cancelAnimationFrame(raf); done += performance.now() - t0; icon("play"); } });
  segs.forEach((g, i) => { g.addEventListener("click", () => { idx = i; done = 0; t0 = performance.now(); paint(0); onStep && onStep(i); }); });
  icon("play"); paint(0); root.append(b, track); return root;
}

// ---------- RUI 17 gooey-nav ----------
export function gooeyNav(items, { value = 0, size = "md", onChange } = {}) {
  css(); const S = { xs: [8, 14], sm: [10, 16], md: [12, 20], lg: [14, 24] }[size] || [12, 20], [rad, sep] = S;
  if (!document.getElementById("rui-goo")) { const d = s("svg", { width: 0, height: 0, style: "position:absolute" }), f = s("filter", { id: "rui-goo" }); f.append(s("feGaussianBlur", { in: "SourceGraphic", stdDeviation: 5, result: "b" }), s("feColorMatrix", { in: "b", mode: "matrix", values: "1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 20 -9", result: "g" }), s("feComposite", { in: "SourceGraphic", in2: "g", operator: "atop" })); d.append(f); document.body.append(d); }
  const nav = h("nav", "rui-k rui-gooey"), bs = []; let active = value; nav.setAttribute("role", "tablist");
  const paint = () => bs.forEach((b, i) => { const on = i === active, prevOn = i - 1 === active || i === active; b.dataset.active = String(on); b.setAttribute("aria-selected", String(on)); b.style.marginLeft = i === 0 ? "0" : (prevOn ? sep : 0) + "px";
    const L = i === 0 || on || i - 1 === active ? rad : 0, R = i === bs.length - 1 || on || i + 1 === active ? rad : 0; b.style.borderRadius = `${L}px ${R}px ${R}px ${L}px`; });
  items.forEach((it, i) => { const b = btn("", typeof it === "string" ? it : it.label, () => { active = i; paint(); onChange && onChange(i); }); b.setAttribute("role", "tab"); bs.push(b); nav.append(b); });
  paint(); return nav;
}

// ---------- RUI 18 delete-button ----------
export function deleteButton({ onDelete, label = "Eliminar" } = {}) {
  css(); const root = h("div", "rui-k"), box = h("div", "rui-del"), tile = btn("rui-del-tile"), panel = h("div", "rui-del-panel"), msg = h("span", "rui-del-msg"); root.style.display = "inline-flex"; root.style.alignItems = "center";
  tile.setAttribute("aria-label", label); tile.setAttribute("aria-expanded", "false");
  tile.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><g class="rui-del-lid"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></g><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>';
  const ok = btn("rui-del-c"), no = btn("rui-del-c"); ok.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FF5F2E" stroke-width="2.5" stroke-linecap="round"><path d="M5 12l5 5L20 7"/></svg>'; no.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  ok.setAttribute("aria-label", "Confirmar eliminar"); no.setAttribute("aria-label", "Cancelar"); panel.append(ok, no); box.append(tile, panel); root.append(box, msg);
  const set = (o) => { box.classList.toggle("open", o); tile.classList.toggle("hot", o); tile.setAttribute("aria-expanded", String(o)); };
  tile.addEventListener("click", () => set(!box.classList.contains("open")));
  const fin = (t, ms) => { set(false); msg.textContent = t; setTimeout(() => { msg.textContent = ""; }, ms); };
  ok.addEventListener("click", () => { onDelete && onDelete(); fin("Eliminado", 1400); }); no.addEventListener("click", () => fin("Conservado", 600));
  root.addEventListener("keydown", (e) => { if (e.key === "Escape") set(false); }); return root;
}

// ---------- RUI 19 animated-counter ----------
export function animatedCounter({ value = 0, decimals = 0, separator = ",", duration = 0.9 } = {}) {
  css(); const root = h("span", "rui-k rui-cnt"); root.setAttribute("role", "status"); let wheels = [];
  const fmt = (v) => { const [w, d] = Math.abs(v).toFixed(clamp(decimals, 0, 15)).split("."); return (v < 0 ? "-" : "") + w.replace(/\B(?=(\d{3})+(?!\d))/g, separator) + (d ? "." + d : ""); };
  const set = (v) => { const str = fmt(Number.isFinite(v) ? v : 0); root.setAttribute("aria-label", str); const chars = str.split("");
    if (wheels.length !== chars.length) { root.replaceChildren(); wheels = chars.map((ch) => { if (ch < "0" || ch > "9") { const x = h("span", "", ch); root.append(x); return { st: true, el: x }; } const w = h("span", "rui-cnt-w"), col = h("span"); col.setAttribute("aria-hidden", "true"); [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0].forEach((f) => col.append(h("b", "", String(f)))); w.append(col); root.append(w); const sp = spring({ p: 0 }, { duration, bounce: 0.18 }, (o) => { col.style.transform = `translateY(${-(((o.p % 10) + 10) % 10) * 1.5}em)`; }); return { col, sp, pos: 0 }; }); }
    chars.forEach((ch, i) => { const w = wheels[i]; if (w.st) { w.el.textContent = ch; return; } const d = +ch, cur = ((w.pos % 10) + 10) % 10; let step = d - cur; if (step < 0) step += 10; w.pos += step; w.sp.to({ p: w.pos }); }); };
  set(value); root.set = set; return root;
}

// ---------- RUI 20 matrix-orb (dibujo original) ----------
export function matrixOrb({ state = "idle", size = 240, color = "#F75001", dots = 11, labels = { idle: "En reposo", listening: "Escuchando", thinking: "Pensando" } } = {}) {
  css(); const TAU = Math.PI * 2, STATES = ["idle", "listening", "thinking"], SCALE = { idle: 0.88, listening: 1, thinking: 0.92 }, ORB = [{ radius: 0.62, speed: 2.2, phase: 0, spread: 0.42 }, { radius: 0.4, speed: -1.7, phase: 2.1, spread: 0.36 }, { radius: 0.8, speed: 1.15, phase: 4, spread: 0.34 }];
  const env = (t) => { const sl = 0.5 + 0.5 * Math.sin(t * 0.62 + 0.4), fa = 0.5 + 0.5 * Math.sin(t * 1.9 + 1.1); return 0.22 + 0.78 * (0.45 + 0.55 * sl) * fa; };
  const inten = (st, d, nx, ny, t, amp) => { if (st === "listening") return 0.32 + amp * (0.34 + 0.38 * (0.5 + 0.5 * Math.sin(d * 4.2 - t * 3))); if (st === "thinking") { let heat = 0; for (const o of ORB) { const a = t * o.speed + o.phase, dx = nx - Math.cos(a) * o.radius, dy = ny - Math.sin(a) * o.radius; heat += Math.exp(-(dx * dx + dy * dy) / (o.spread * o.spread)); } return 0.26 + 0.8 * Math.min(1, heat); } return 0.62 + 0.12 * Math.sin(t * 1.05 - d * 2.4); };
  const root = h("div", "rui-k rui-orb"), c = h("canvas"), lbl = h("span", "rui-orb-lbl"); lbl.setAttribute("aria-live", "polite"); c.style.width = c.style.height = size + "px"; root.append(c, lbl);
  const dpr = Math.min(devicePixelRatio || 1, 4), buf = Math.round(size * dpr), ctx = c.getContext("2d"); c.width = c.height = buf; ctx.scale(buf / size, buf / size); ctx.fillStyle = color;
  const grid = Math.max(3, Math.round(dots)), half = (grid - 1) / 2, spacing = (size * 0.74) / (grid - 1), maxR = spacing * 0.6, ctr = size / 2, W = { idle: 0, listening: 0, thinking: 0 }; W[state] = 1; let level;
  const draw = (t, amp, sc) => { ctx.clearRect(0, 0, size, size); for (let iy = 0; iy < grid; iy++) for (let ix = 0; ix < grid; ix++) { const nx = (ix - half) / half, ny = (iy - half) / half, d = Math.hypot(nx, ny); if (d > 1.12) continue; let bl = 0; for (const st of STATES) if (W[st] >= 0.001) bl += W[st] * inten(st, d, nx, ny, t, amp); const r = maxR * Math.exp(-d * d * 1.7) * clamp(bl, 0, 1) * sc; if (r * dpr < 0.5) continue; ctx.beginPath(); ctx.arc(ctr + (ix - half) * spacing * sc, ctr + (iy - half) * spacing * sc, r, 0, TAU); ctx.fill(); } };
  const lvl = (t) => (level === undefined || !Number.isFinite(level) ? env(t) : clamp(level, 0, 1));
  let t = 0, amp = 0, sc = SCALE[state], vel = 0, last = performance.now();
  const frame = (now) => { const dt = Math.min((now - last) / 1000, 0.05); last = now; t += dt; const tg = lvl(t); amp += (tg - amp) * (1 - Math.pow(1 - (tg > amp ? 0.22 : 0.08), dt * 60)); const stp = 1 - Math.pow(1 - 0.16, dt * 60); for (const st of STATES) W[st] += ((st === state ? 1 : 0) - W[st]) * stp; vel += (-180 * (sc - SCALE[state]) - 26 * vel) * dt; sc += vel * dt; draw(t, amp, sc); requestAnimationFrame(frame); };
  if (reduce()) draw(0, lvl(0), SCALE[state]); else requestAnimationFrame(frame);
  root.dataset.state = state; lbl.textContent = labels[state];
  root.setState = (st, lv) => { state = st; level = lv; root.dataset.state = st; lbl.textContent = labels[st]; if (reduce()) { for (const x of STATES) W[x] = x === st ? 1 : 0; draw(0, lvl(0), SCALE[st]); } };
  return root;
}

// ---------- RUI 21 task-list ----------
export function taskList(tasks, { onChange } = {}) {
  css(); const ul = h("ul", "rui-k rui-tasks"); ul.style.cssText = "list-style:none;margin:0;padding:0"; const cur = tasks.map((t) => ({ ...t })); const lis = new Map();
  const R = 11, DASH = `1 ${(2 * Math.PI * R) / 13 - 1}`;
  const flip = () => { const first = new Map([...lis].map(([id, li]) => [id, li.getBoundingClientRect().top])); const open = cur.filter((t) => !t.parked), fin = cur.filter((t) => t.parked); [...open, ...fin].forEach((t) => ul.append(lis.get(t.id))); if (reduce()) return; lis.forEach((li, id) => { const dy = first.get(id) - li.getBoundingClientRect().top; if (dy) li.animate([{ transform: `translateY(${dy}px)` }, { transform: "none" }], { duration: 420, easing: "cubic-bezier(.3,1.15,.5,1)" }); }); };
  cur.forEach((t) => { t.parked = !!t.done; const li = h("li"), b = btn("rui-task"); b.setAttribute("role", "checkbox");
    b.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><circle class="rui-task-ring" cx="12" cy="12" r="${R}" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="${DASH}"/><circle class="rui-task-fill" cx="12" cy="12" r="${R}" fill="var(--active)"/><path class="rui-task-tick" d="M7.5 12.5l3 3 6-6.5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    const lab = h("span", "rui-task-t", t.label); b.append(lab); li.append(b); lis.set(t.id, li);
    const paint = () => { b.dataset.done = String(!!t.done); b.setAttribute("aria-checked", String(!!t.done)); }; paint();
    b.addEventListener("click", () => { t.done = !t.done; paint(); onChange && onChange(cur.map(({ id, label, done }) => ({ id, label, done }))); if (t.done) { if (!reduce()) b.animate([{ transform: "scale(1)" }, { transform: "scale(1.08)" }, { transform: "scale(1)" }], { duration: 340, easing: "cubic-bezier(.22,1,.36,1)" }); setTimeout(() => { if (!reduce()) b.animate([0, 8, -2, 0].map((x) => ({ transform: `translateX(${x}px)` })), { duration: 300 }); setTimeout(() => { if (t.done) { t.parked = true; flip(); } }, 300); }, 440); } else if (t.parked) { t.parked = false; flip(); } });
  }); flip(); return ul;
}
