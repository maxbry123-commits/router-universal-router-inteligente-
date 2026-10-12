// Navegador minimo en Node (sin dependencias) para probar el chat de verdad: DOM, eventos, almacenamiento. Solo para pruebas.
const VOID = new Set(['input', 'br', 'img', 'link', 'meta', 'hr', 'source']);
class Ev { constructor(type, o = {}) { this.type = type; this.bubbles = !!o.bubbles; this.cancelable = !!o.cancelable; this.detail = o.detail; this.defaultPrevented = false; this._stop = false; this._stopI = false; } preventDefault() { if (this.cancelable) this.defaultPrevented = true; } stopPropagation() { this._stop = true; } stopImmediatePropagation() { this._stop = true; this._stopI = true; } }
class Txt { constructor(t) { this.nodeType = 3; this.data = String(t); this.parentNode = null; } get textContent() { return this.data; } set textContent(v) { this.data = String(v); } remove() { if (this.parentNode) this.parentNode.removeChild(this); } }
const ESTILO = () => new Proxy({ setProperty(k, v) { this[k] = v; }, removeProperty(k) { delete this[k]; } }, {});
export const ERRORES = [];
export class El {
  constructor(tag) { this.nodeType = 1; this.tagName = String(tag).toUpperCase(); this.childNodes = []; this.parentNode = null; this.attrs = {}; this._l = {}; this.style = ESTILO(); this._value = ''; this.files = []; this.checked = false; this.disabled = false; this.scrollTop = 0; this.scrollHeight = 0; this.open = false; }
  get dataset() { const a = this.attrs, kb = (k) => 'data-' + String(k).replace(/[A-Z]/g, (c) => '-' + c.toLowerCase()); return new Proxy({}, { get: (t, k) => (typeof k === 'string' && kb(k) in a ? a[kb(k)] : undefined), set: (t, k, v) => { a[kb(k)] = String(v); return true; }, has: (t, k) => kb(k) in a, deleteProperty: (t, k) => { delete a[kb(k)]; return true; } }); }
  get children() { return this.childNodes.filter((n) => n.nodeType === 1); }
  get firstChild() { return this.childNodes[0] || null; } get lastChild() { return this.childNodes[this.childNodes.length - 1] || null; }
  get firstElementChild() { return this.children[0] || null; } get lastElementChild() { const c = this.children; return c[c.length - 1] || null; }
  get parentElement() { return this.parentNode && this.parentNode.nodeType === 1 ? this.parentNode : null; }
  get nextElementSibling() { const p = this.parentNode; if (!p) return null; const c = p.children, i = c.indexOf(this); return c[i + 1] || null; }
  get previousElementSibling() { const p = this.parentNode; if (!p) return null; const c = p.children, i = c.indexOf(this); return c[i - 1] || null; }
  get isConnected() { let n = this; while (n.parentNode) n = n.parentNode; return n === DOC; }
  get id() { return this.attrs.id || ''; } set id(v) { this.attrs.id = String(v); }
  get className() { return this.attrs.class || ''; } set className(v) { this.attrs.class = String(v); }
  get classList() { const s = this; const l = () => (s.attrs.class || '').split(/\s+/).filter(Boolean); const w = (a) => { s.attrs.class = a.join(' '); }; return { add: (...c) => { const a = l(); c.forEach((x) => { if (!a.includes(x)) a.push(x); }); w(a); }, remove: (...c) => w(l().filter((x) => !c.includes(x))), toggle: (c, f) => { const a = l(), h = a.includes(c), on = f === undefined ? !h : !!f; w(on ? (h ? a : [...a, c]) : a.filter((x) => x !== c)); return on; }, contains: (c) => l().includes(c) }; }
  get hidden() { return 'hidden' in this.attrs; } set hidden(v) { if (v) this.attrs.hidden = ''; else delete this.attrs.hidden; }
  get value() { return this._value; } set value(v) { this._value = String(v); }
  get type() { return this.attrs.type || (this.tagName === 'BUTTON' ? 'submit' : 'text'); } set type(v) { this.attrs.type = String(v); }
  get textContent() { return this.childNodes.map((n) => n.textContent).join(''); } set textContent(v) { this.childNodes.forEach((n) => { n.parentNode = null; }); this.childNodes = []; if (v !== '' && v != null) this.append(String(v)); }
  get innerHTML() { return this.textContent; } set innerHTML(h) { this.childNodes.forEach((n) => { n.parentNode = null; }); this.childNodes = []; parseHTML(String(h), this); }
  get offsetWidth() { return 100; } get offsetHeight() { return 40; } get offsetTop() { return 0; } get offsetLeft() { return 0; } get clientHeight() { return 40; }
  getBoundingClientRect() { return { top: 0, left: 0, width: 100, height: 40, right: 100, bottom: 40 }; }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; } setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'value') this._value = String(v); } removeAttribute(k) { delete this.attrs[k]; } hasAttribute(k) { return k in this.attrs; }
  _ins(n, i) { if (typeof n === 'string' || typeof n === 'number') n = new Txt(n); if (n.parentNode) n.parentNode.removeChild(n); n.parentNode = this; if (i == null) this.childNodes.push(n); else this.childNodes.splice(i, 0, n); return n; }
  append(...ns) { ns.forEach((n) => this._ins(n)); } appendChild(n) { return this._ins(n); } prepend(...ns) { ns.reverse().forEach((n) => this._ins(n, 0)); }
  insertBefore(n, ref) { const i = ref ? this.childNodes.indexOf(ref) : -1; return this._ins(n, i < 0 ? null : i); }
  removeChild(n) { const i = this.childNodes.indexOf(n); if (i >= 0) { this.childNodes.splice(i, 1); n.parentNode = null; } return n; }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  replaceChildren(...ns) { this.childNodes.forEach((n) => { n.parentNode = null; }); this.childNodes = []; ns.forEach((n) => this._ins(n)); }
  after(...ns) { const p = this.parentNode; if (!p) return; let i = p.childNodes.indexOf(this) + 1; ns.forEach((n) => { p._ins(n, i++); }); }
  before(...ns) { const p = this.parentNode; if (!p) return; let i = p.childNodes.indexOf(this); ns.forEach((n) => { p._ins(n, i++); }); }
  replaceWith(n) { const p = this.parentNode; if (!p) return; const i = p.childNodes.indexOf(this); p.removeChild(this); p._ins(n, i); }
  contains(n) { while (n) { if (n === this) return true; n = n.parentNode; } return false; }
  closest(sel) { let n = this; while (n && n.nodeType === 1) { if (matchesSel(n, sel)) return n; n = n.parentNode; } return null; }
  matches(sel) { return matchesSel(this, sel); }
  querySelectorAll(sel) { return qsa(this, sel); } querySelector(sel) { return qsa(this, sel)[0] || null; }
  addEventListener(t, f, o) { const cap = o === true || (o && o.capture); (this._l[t] = this._l[t] || []).push({ f, cap: !!cap }); }
  removeEventListener(t, f) { this._l[t] = (this._l[t] || []).filter((x) => x.f !== f); }
  dispatchEvent(ev) {
    ev.target = this; const path = []; for (let n = this; n; n = n.parentNode) path.push(n);
    const run = (n, fase) => { for (const x of [...((n._l && n._l[ev.type]) || [])]) { if (fase === 'cap' && !x.cap) continue; if (fase === 'bub' && x.cap) continue; ev.currentTarget = n; try { x.f.call(n, ev); } catch (e) { ERRORES.push(ev.type + ' en ' + n.tagName + '#' + n.id + ': ' + e.message); } if (ev._stopI) return; } };
    for (let i = path.length - 1; i > 0 && !ev._stop; i--) run(path[i], 'cap');
    if (!ev._stop) { run(this, 'cap'); if (!ev._stopI) run(this, 'bub'); }
    if (ev.bubbles) for (let i = 1; i < path.length && !ev._stop; i++) run(path[i], 'bub');
    return !ev.defaultPrevented;
  }
  click() { if (this.disabled) return; const ev = new Ev('click', { bubbles: true, cancelable: true }); if (this.tagName === 'INPUT' && this.type === 'checkbox') this.checked = !this.checked; const ok = this.dispatchEvent(ev); if (ok && this.tagName === 'BUTTON' && this.type === 'submit') { const f = this.closest('form'); if (f) f.requestSubmit(); } }
  requestSubmit() { this.dispatchEvent(new Ev('submit', { bubbles: true, cancelable: true })); }
  focus() {} blur() {} select() {} scrollIntoView() {} setPointerCapture() {}
}
function parseHTML(h, padre) {
  const pila = [padre]; const re = /<!--[\s\S]*?-->|<\/([a-zA-Z0-9-]+)\s*>|<([a-zA-Z][a-zA-Z0-9-]*)((?:"[^"]*"|'[^']*'|[^>"'])*?)(\/?)>|([^<]+)/g; let m;
  while ((m = re.exec(h)) !== null) {
    if (m[1]) { const t = m[1].toUpperCase(); for (let i = pila.length - 1; i > 0; i--) if (pila[i].tagName === t) { pila.length = i; break; } }
    else if (m[2]) { const e = new El(m[2]); const ar = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g; let a; while ((a = ar.exec(m[3])) !== null) e.setAttribute(a[1], a[2] ?? a[3] ?? a[4] ?? ''); pila[pila.length - 1]._ins(e); if (!VOID.has(m[2].toLowerCase()) && !m[4]) pila.push(e); }
    else if (m[5] !== undefined) { if (m[5].trim() !== '' || pila.length > 1) pila[pila.length - 1]._ins(new Txt(m[5])); }
  }
}
function parseCompound(s) { const c = { tag: null, id: null, cls: [], attrs: [], not: [], first: false, last: false, scope: false }; let m; const re = /^([a-zA-Z][a-zA-Z0-9-]*|\*)|#([-\w]+)|\.([-\w]+)|\[([-\w:]+)(?:([~|^$*]?=)(?:"([^"]*)"|'([^']*)'|([^\]]*)))?\]|:not\(([^)]*)\)|:first-child|:last-child|:scope|:hover|:focus|:checked/y; re.lastIndex = 0; while (re.lastIndex < s.length && (m = re.exec(s))) { if (m[1]) c.tag = m[1] === '*' ? null : m[1].toUpperCase(); else if (m[2]) c.id = m[2]; else if (m[3]) c.cls.push(m[3]); else if (m[4]) c.attrs.push([m[4], m[5], m[6] ?? m[7] ?? m[8]]); else if (m[9] !== undefined) c.not.push(parseCompound(m[9])); else if (m[0] === ':first-child') c.first = true; else if (m[0] === ':last-child') c.last = true; else if (m[0] === ':scope') c.scope = true; } return c; }
function parseSel(sel) { return String(sel).split(',').map((p) => { const toks = p.trim().replace(/\s*>\s*/g, ' > ').split(/\s+/).filter(Boolean); const cad = []; let comb = ' '; toks.forEach((t) => { if (t === '>') comb = '>'; else { cad.push({ c: parseCompound(t), comb }); comb = ' '; } }); return cad; }); }
function cmpMatch(e, c, ctx) { if (c.scope) return e === ctx; if (c.tag && e.tagName !== c.tag) return false; if (c.id && e.id !== c.id) return false; const cl = (e.attrs.class || '').split(/\s+/); if (!c.cls.every((x) => cl.includes(x))) return false; for (const [k, op, v] of c.attrs) { if (!(k in e.attrs)) return false; const val = e.attrs[k]; if (op === '=' && val !== v) return false; if (op === '^=' && !val.startsWith(v)) return false; if (op === '*=' && !val.includes(v)) return false; } if (c.not.some((n) => cmpMatch(e, n, ctx))) return false; if (c.first && (!e.parentNode || e.parentNode.children[0] !== e)) return false; if (c.last && (!e.parentNode || e.parentNode.children.slice(-1)[0] !== e)) return false; return true; }
function cadMatch(e, cad, i, ctx) { if (!cmpMatch(e, cad[i].c, ctx)) return false; if (i === 0) return true; if (cad[i].comb === '>') { const p = e.parentNode; return !!(p && p.nodeType === 1 && cadMatch(p, cad, i - 1, ctx)); } for (let p = e.parentNode; p && p.nodeType === 1; p = p.parentNode) if (cadMatch(p, cad, i - 1, ctx)) return true; return false; }
function matchesSel(e, sel) { return parseSel(sel).some((cad) => cadMatch(e, cad, cad.length - 1, null)); }
function qsa(raiz, sel) { const lista = parseSel(sel), out = []; const rec = (n) => { n.children.forEach((e) => { if (lista.some((cad) => cadMatch(e, cad, cad.length - 1, raiz))) out.push(e); rec(e); }); }; rec(raiz); return out; }
const DOC = new El('#document'); DOC.documentElement = new El('html'); DOC.head = new El('head'); DOC.body = new El('body'); DOC.documentElement.append(DOC.head, DOC.body); DOC.append(DOC.documentElement);
DOC.createElement = (t) => new El(t); DOC.createTextNode = (t) => new Txt(t); DOC.getElementById = (id) => DOC.querySelector('#' + id); DOC.hidden = false;
const store = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); }, key: (i) => [...m.keys()][i], get length() { return m.size; }, clear: () => m.clear() }; };
globalThis.document = DOC; globalThis.window = globalThis; globalThis.Event = Ev; globalThis.CustomEvent = class extends Ev { constructor(t, o = {}) { super(t, o); } };
globalThis.localStorage = store(); globalThis.sessionStorage = store(); globalThis.addEventListener = (t, f) => { (globalThis.__wl = globalThis.__wl || {})[t] = [...((globalThis.__wl || {})[t] || []), f]; }; globalThis.removeEventListener = () => {}; globalThis.dispatchEvent = (ev) => { for (const f of ((globalThis.__wl || {})[ev.type] || [])) { try { f(ev); } catch (e) { ERRORES.push('window ' + ev.type + ': ' + e.message); } } return true; };
globalThis.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} }); globalThis.MutationObserver = class { observe() {} disconnect() {} }; globalThis.requestAnimationFrame = (f) => setTimeout(() => f(Date.now()), 0); globalThis.cancelAnimationFrame = clearTimeout;
globalThis.confirm = () => true; globalThis.prompt = () => null; globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' }); globalThis.DataTransfer = class { constructor() { this.items = { add() {} }; this.files = []; } };
try { Object.defineProperty(globalThis, 'navigator', { value: { clipboard: { writeText: async () => {}, readText: async () => '' } }, configurable: true }); } catch (e) {}
globalThis.IntersectionObserver = class { observe() {} disconnect() {} }; globalThis.ResizeObserver = class { observe() {} disconnect() {} };
export { DOC };
