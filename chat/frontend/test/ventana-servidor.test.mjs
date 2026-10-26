import test from "node:test";
import assert from "node:assert/strict";

const nodes = [];
function walk(n, acc = []) { acc.push(n); for (const c of n.children || []) walk(c, acc); return acc; }
function match(n, sel) {
  if (sel.startsWith("#")) return n.id === sel.slice(1);
  if (sel.startsWith(".")) return String(n.className || "").split(/\s+/).includes(sel.slice(1));
  return String(n.tagName) === sel.toUpperCase();
}
function buscar(root, sel) {
  let cur = [root];
  for (const p of sel.trim().split(/\s+/)) {
    const next = [];
    for (const n of cur) for (const d of walk(n)) if (d !== n && match(d, p)) next.push(d);
    cur = next;
  }
  return cur[0] || null;
}
function nodo(tag) {
  const n = { tagName: String(tag).toUpperCase(), className: "", id: "", textContent: "", hidden: false, type: "", disabled: false, title: "", innerHTML: "", children: [], attrs: {}, onclick: null };
  n.classList = { toggle() {}, add() {}, remove() {} };
  n.setAttribute = (k, v) => { n.attrs[k] = String(v); };
  n.getAttribute = (k) => (k in n.attrs ? n.attrs[k] : null);
  n.append = (...xs) => { for (const x of xs) if (x) { x.parentNode = n; n.children.push(x); } };
  n.replaceChildren = (...xs) => { n.children = []; n.append(...xs); };
  n.insertBefore = (node, ref) => { node.parentNode = n; const i = ref ? n.children.indexOf(ref) : -1; if (i < 0) n.children.push(node); else n.children.splice(i, 0, node); };
  n.querySelector = (sel) => buscar(n, sel);
  n.querySelectorAll = () => [];
  n.focus = () => {};
  n.addEventListener = () => {};
  nodes.push(n);
  return n;
}
const body = nodo("body");
const composer = nodo("div"); composer.id = "composer";
const bar = nodo("div"); bar.className = "composer-bar";
composer.append(bar); body.append(composer);
globalThis.MutationObserver = class { observe() {} disconnect() {} };
globalThis.document = { body, createElement: (t) => nodo(t), addEventListener() {}, querySelector: (sel) => buscar(body, sel) };
globalThis.sessionStorage = { getItem: (k) => (k === "riu_clave" ? "clave-chat" : null), setItem() {} };
globalThis.window = globalThis;
globalThis.RIU_CONFIG = { proxyDestino: "" };

const llamadas = [];
let fallo = null;
const json = (obj, status = 200) => ({ ok: status < 400, status, json: async () => obj });
globalThis.fetch = async (url, opt) => {
  const cuerpo = opt && opt.body ? JSON.parse(opt.body) : null;
  llamadas.push({ url: String(url), method: opt && opt.method, body: cuerpo, clave: opt && opt.headers && opt.headers["X-API-Key"] });
  if (String(url).endsWith("/health")) return json({ tareas_en_curso: 2, mantener_siempre: true, latido: { t: Math.floor(Date.now() / 1000), ok: true } });
  if (String(url).includes("/api/power")) return json({ stage: "RUNNING", hardware: "cpu-basic" });
  if (fallo) return json({ detail: fallo }, 500);
  return json({ status: "ok", result: { ok: true, siempre: !!(cuerpo && cuerpo.siempre), hasta: null } });
};

await import("../ventana-servidor.js");
const abrir = document.querySelector("#btn-power");
abrir.onclick();
await new Promise((r) => setTimeout(r, 40));

test("el interruptor no está en Servidor y sí en Configuración", async () => {
  const { readFileSync } = await import("node:fs");
  assert.equal(walk(body).some((x) => x.textContent === "Dejar encendido hasta que yo lo apague"), false);
  for (const nombre of ["Encender", "Apagar", "Reiniciar", "Actualizar"]) assert.equal(walk(body).some((x) => x.textContent === nombre), true);
  const html = readFileSync(new URL("../panel-apariencia.html", import.meta.url), "utf8");
  const js = readFileSync(new URL("../panel-apariencia.js", import.meta.url), "utf8");
  assert.equal(html.includes('id="tg-mantener"'), true);
  assert.equal(html.includes("Dejar encendido hasta que yo lo apague"), true);
  assert.equal(js.includes("/plugins/puente_chat/call/mantener_encendido"), true);
  assert.equal(js.includes("Encendido fijo: el servidor no se duerme hasta que lo apagues"), true);
  assert.equal(js.includes("pintar(antes)"), true);
  console.log("CRUDO", JSON.stringify({ servidor: false, configuracion: "tg-mantener" }));
});
