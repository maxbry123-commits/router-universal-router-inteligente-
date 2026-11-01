// dom-falso.mjs — DOM minimo para probar modulos del chat con node --test (sin jsdom).
export function walk(n, acc = []) { acc.push(n); for (const c of n.children || []) walk(c, acc); return acc; }
function match(n, sel) {
  if (sel.startsWith("#")) return n.id === sel.slice(1);
  if (sel.startsWith(".")) return String(n.className || "").split(/\s+/).includes(sel.slice(1));
  return String(n.tagName) === sel.toUpperCase();
}
export function buscar(root, sel) {
  let cur = [root];
  for (const p of sel.trim().split(/\s+/)) {
    const next = [];
    for (const n of cur) for (const d of walk(n)) if (d !== n && match(d, p)) next.push(d);
    cur = next;
  }
  return cur[0] || null;
}
export function nodo(tag) {
  const n = { tagName: String(tag).toUpperCase(), className: "", id: "", textContent: "", hidden: false, type: "", disabled: false, title: "", innerHTML: "", children: [], attrs: {}, onclick: null, style: {}, dataset: {}, listeners: {} };
  n.classList = {
    add: (...c) => { const s = new Set(String(n.className).split(/\s+/).filter(Boolean)); c.forEach((x) => s.add(x)); n.className = [...s].join(" "); },
    remove: (...c) => { n.className = String(n.className).split(/\s+/).filter((x) => x && !c.includes(x)).join(" "); },
    contains: (c) => String(n.className).split(/\s+/).includes(c),
    toggle() {},
  };
  n.setAttribute = (k, v) => { n.attrs[k] = String(v); if (k === "id") n.id = String(v); if (k === "class") n.className = String(v); };
  n.getAttribute = (k) => (k in n.attrs ? n.attrs[k] : null);
  n.removeAttribute = (k) => { delete n.attrs[k]; };
  n.append = (...xs) => { for (const x of xs) if (x) { x.parentNode = n; n.children.push(x); } };
  n.appendChild = (x) => { n.append(x); return x; };
  n.replaceChildren = (...xs) => { n.children.forEach((c) => { c.parentNode = null; }); n.children = []; n.append(...xs); };
  n.remove = () => { if (n.parentNode) n.parentNode.children = n.parentNode.children.filter((c) => c !== n); n.parentNode = null; };
  n.insertBefore = (node, ref) => { node.parentNode = n; const i = ref ? n.children.indexOf(ref) : -1; if (i < 0) n.children.push(node); else n.children.splice(i, 0, node); };
  n.querySelector = (sel) => buscar(n, sel);
  n.querySelectorAll = (sel) => walk(n).filter((d) => d !== n && sel.split(",").some((s) => match(d, s.trim())));
  n.contains = (x) => walk(n).includes(x);
  n.focus = () => { n.enfocado = true; };
  n.addEventListener = (t, f) => { (n.listeners[t] = n.listeners[t] || []).push(f); };
  n.removeEventListener = (t, f) => { n.listeners[t] = (n.listeners[t] || []).filter((x) => x !== f); };
  return n;
}
