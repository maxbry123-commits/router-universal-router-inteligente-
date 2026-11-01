import test from "node:test";
import assert from "node:assert/strict";

// AP1: aprobar desde la UI envia x-operador y x-operator-token (cabeceras, nunca cuerpo ni storage) a /chat/swe/aprobar.
// "Servidor falso": globalThis.fetch imita el contrato de app.py (_identificar_operador): 503 sin aprobadores, 403 operador desconocido, 401/403 token malo, 200 si coincide. Claves SOLO de prueba.
const datos = new Map(), sdatos = new Map();
globalThis.window = globalThis;
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k) };
globalThis.sessionStorage = { getItem: (k) => sdatos.get(k) ?? "k", setItem: (k, v) => sdatos.set(k, String(v)), removeItem: (k) => sdatos.delete(k) };
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {}; globalThis.dispatchEvent = () => true;
globalThis.location = { hostname: "x.hf.space", origin: "https://x.hf.space", search: "" };
globalThis.CustomEvent = class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } };
window.RIU_CONFIG = { proxyDestino: "https://comand-center-1-riu-router.hf.space", liveUrl: "" };

// ---- DOM minimo con eventos, valores y busqueda por atributo ----
class Nodo {
  constructor(tag) { this.tag = tag; this.children = []; this.attrs = {}; this.listeners = {}; this.className = ""; this.textContent = ""; this.value = ""; this.hidden = false; this.parent = null; this.type = ""; this.disabled = false; }
  append(...xs) { for (const x of xs) { if (x && typeof x === "object") x.parent = this; this.children.push(x); } }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  addEventListener(k, fn) { (this.listeners[k] ||= []).push(fn); }
  focus() { this.doc && (this.doc.activeElement = this); }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter((x) => x !== this); this.parent = null; }
  click() { for (const f of this.listeners.click || []) f({ preventDefault() {} }); if (this.onclick) this.onclick(); }
  teclear(key) { const e = { key, preventDefault() {}, stopPropagation() {} }; for (const f of this.listeners.keydown || []) f(e); return e; }
  todos() { return this.children.flatMap((x) => (x instanceof Nodo ? [x, ...x.todos()] : [])); }
}
const crearDoc = () => { const d = { body: new Nodo("body"), activeElement: null, createElement: (t) => { const n = new Nodo(t); n.doc = d; return n; }, getElementById: () => null, head: new Nodo("head"), addEventListener() {} }; return d; };
const doc = crearDoc();
globalThis.document = doc;

// ---- servidor falso: contrato de /chat/swe/aprobar ----
const APROBADORES = { luna: "tok-de-prueba-luna" };  // el servidor real guarda solo sha256; aqui basta comparar (dato de prueba, no es una clave)
const visto = [];
let aprobadoresConfigurados = true;
globalThis.fetch = async (url, opts) => {
  const h = Object.fromEntries(Object.entries(opts.headers || {}).map(([k, v]) => [k.toLowerCase(), v]));
  const cuerpo = opts.body ? JSON.parse(opts.body) : null;
  visto.push({ url: String(url), headers: h, cuerpo, opts });
  const resp = (status, obj) => ({ ok: status < 400, status, headers: { get: () => "application/json" }, json: async () => obj });
  if (!String(url).endsWith("/chat/swe/aprobar")) return resp(200, { ok: true, resultado: { task_id: "t1", estado: "DONE" } });
  if (!aprobadoresConfigurados) return resp(503, { detail: "APROBADORES_NO_CONFIGURADOS" });
  const op = h["x-operador"], tk = h["x-operator-token"];
  if (!op) return resp(403, { detail: "OPERADOR_REQUERIDO" });
  if (!(op in APROBADORES)) return resp(403, { detail: "OPERADOR_NO_AUTORIZADO" });
  if (tk !== APROBADORES[op]) return resp(401, { detail: "OPERADOR_NO_AUTORIZADO" });
  return resp(200, { ok: true, resultado: { task_id: cuerpo.task_id, estado: "CONTINUAR" } });
};
const { api } = await import("../api.js");
const S = await import("../swe-directo.js");
const O = await import("../aprobar-operador.js");
const D = { task_id: "t1", op_id: "0123456789abcdef", sesion: "s", proyecto: "p" };
const TK = "tok-de-prueba-luna";
test.beforeEach(() => { visto.length = 0; aprobadoresConfigurados = true; doc.body.children.length = 0; });

test("api(): options.headers viaja como cabeceras de ESA peticion; sin headers no cambia nada; Content-Type y X-API-Key no se pisan", async () => {
  await api("/chat/swe/aprobar", { method: "POST", body: { a: 1 }, headers: { "x-operador": "luna", "x-operator-token": TK, "Content-Type": "text/plain" } });
  assert.equal(visto[0].headers["x-operador"], "luna"); assert.equal(visto[0].headers["x-operator-token"], TK);
  assert.equal(visto[0].headers["content-type"], "application/json"); assert.equal(visto[0].headers["x-api-key"], "k");
  await api("/chat/swe/estado", { method: "POST", body: {} });
  assert.ok(!("x-operador" in visto[1].headers) && !("x-operator-token" in visto[1].headers), "la siguiente peticion no arrastra las cabeceras");
  assert.deepEqual(Object.keys(visto[1].headers).sort(), ["content-type", "x-api-key"]);
});

test("aprobarTareaSwe: operador y token van en CABECERAS; el cuerpo no los lleva; 200 -> CONTINUAR", async () => {
  const r = await S.aprobarTareaSwe(api, { ...D, headers: { "x-operador": "luna", "x-operator-token": TK } });
  assert.equal(r.estado, "CONTINUAR");
  const v = visto.find((x) => x.url.endsWith("/chat/swe/aprobar"));
  assert.equal(v.headers["x-operador"], "luna"); assert.equal(v.headers["x-operator-token"], TK);
  assert.ok(!JSON.stringify(v.cuerpo).includes(TK) && !("operador" in v.cuerpo) && !("aprobacion" in v.cuerpo), JSON.stringify(v.cuerpo));
});

test("aprobarYContinuarSwe: las cabeceras solo salen en /chat/swe/aprobar, no en avanzar", async () => {
  const r = await S.aprobarYContinuarSwe(api, { ...D, headers: { "x-operador": "luna", "x-operator-token": TK } });
  assert.ok(r);
  const ap = visto.filter((x) => x.url.endsWith("/chat/swe/aprobar")), otros = visto.filter((x) => !x.url.endsWith("/chat/swe/aprobar"));
  assert.equal(ap.length, 1); assert.ok(otros.length >= 1, "continua despues de aprobar");
  for (const o of otros) assert.ok(!("x-operador" in o.headers) && !("x-operator-token" in o.headers), o.url);
});

test("errores: 403 (operador desconocido), 401/403 token malo y 503 llevan el status; mensajeAprobacion los explica sin eco de secretos", async () => {
  const intenta = async (cab) => { try { await S.aprobarTareaSwe(api, { ...D, headers: cab }); } catch (e) { return e; } };
  const e403 = await intenta({ "x-operador": "otro", "x-operator-token": TK });
  assert.equal(e403.status, 403); assert.match(O.mensajeAprobacion(e403), /operador|token/i); assert.match(O.mensajeAprobacion(e403), /incorrect/i);
  const e401 = await intenta({ "x-operador": "luna", "x-operator-token": "mal-token-prueba" });
  assert.equal(e401.status, 401); assert.match(O.mensajeAprobacion(e401), /incorrect/i);
  assert.ok(!O.mensajeAprobacion(e401).includes("mal-token-prueba") && !O.mensajeAprobacion(e401).includes(TK));
  aprobadoresConfigurados = false;
  const e503 = await intenta({ "x-operador": "luna", "x-operator-token": TK });
  assert.equal(e503.status, 503); assert.match(O.mensajeAprobacion(e503), /RIU_SWE_APROBADORES/); assert.match(O.mensajeAprobacion(e503), /no configurada/i);
  assert.match(O.mensajeExito("luna"), /aprobad/i);
});

test("dialogo: role=dialog, aria-modal, etiquetas, operador texto + token password sin autocompletar, boton Cancelar; foco al abrir", async () => {
  const p = O.pedirOperadorYToken(doc);
  const fondo = doc.body.children[0];
  assert.equal(fondo.getAttribute("role"), "dialog"); assert.equal(fondo.getAttribute("aria-modal"), "true"); assert.ok(fondo.getAttribute("aria-labelledby") || fondo.getAttribute("aria-label"));
  const todos = fondo.todos(), inputs = todos.filter((n) => n.tag === "input"), botones = todos.filter((n) => n.tag === "button");
  const op = inputs.find((n) => n.type === "text"), tk = inputs.find((n) => n.type === "password");
  assert.ok(op && tk, "campo de texto y campo password"); assert.ok(op.getAttribute("aria-label") && tk.getAttribute("aria-label"));
  assert.equal(tk.autocomplete, "off"); assert.equal(op.autocomplete, "off");
  assert.ok(botones.some((b) => /cancelar/i.test(b.textContent)) && botones.some((b) => /aprobar/i.test(b.textContent)));
  assert.equal(doc.activeElement, op, "el foco va al campo operador");
  botones.find((b) => /cancelar/i.test(b.textContent)).click();
  assert.equal(await p, null); assert.equal(doc.body.children.length, 0, "el dialogo se retira");
});

test("dialogo: Aprobar con campos vacios no resuelve y avisa (role=alert); con datos devuelve {operador,token}, limpia los campos y se retira; Escape cancela", async () => {
  let p = O.pedirOperadorYToken(doc);
  let fondo = doc.body.children[0], todos = fondo.todos();
  const op = todos.find((n) => n.type === "text"), tk = todos.find((n) => n.type === "password"), ok = todos.find((n) => n.tag === "button" && /aprobar/i.test(n.textContent));
  ok.click();
  const alerta = todos.find((n) => n.getAttribute("role") === "alert");
  assert.ok(alerta && alerta.textContent.length > 0 && doc.body.children.length === 1, "sigue abierto con aviso");
  op.value = " luna "; tk.value = TK; ok.click();
  const cred = await p;
  assert.deepEqual(cred, { operador: "luna", token: TK });
  assert.equal(tk.value, "", "el campo token se vacia al enviar"); assert.equal(op.value, ""); assert.equal(doc.body.children.length, 0);
  assert.equal([...datos.values(), ...sdatos.values()].some((v) => String(v).includes(TK)), false, "nada en storage");
  p = O.pedirOperadorYToken(doc); fondo = doc.body.children[0];
  const e = fondo.teclear("Escape"); assert.equal(await p, null); assert.equal(doc.body.children.length, 0); assert.ok(e);
});

test("dialogo: caracteres no validos en una cabecera (saltos de linea, no ASCII) se rechazan antes de enviar", async () => {
  const p = O.pedirOperadorYToken(doc);
  const todos = doc.body.children[0].todos(), op = todos.find((n) => n.type === "text"), tk = todos.find((n) => n.type === "password"), ok = todos.find((n) => n.tag === "button" && /aprobar/i.test(n.textContent));
  op.value = "luna"; tk.value = "abc\ndef"; ok.click();
  assert.equal(doc.body.children.length, 1, "sigue abierto"); assert.ok(todos.find((n) => n.getAttribute("role") === "alert").textContent.length > 0);
  todos.find((n) => n.tag === "button" && /cancelar/i.test(n.textContent)).click(); assert.equal(await p, null);
});

test("el modulo no usa storage ni console", async () => {
  const { readFileSync } = await import("node:fs");
  const src = readFileSync(new URL("../aprobar-operador.js", import.meta.url), "utf8");
  assert.ok(!/localStorage|sessionStorage|console\./.test(src));
});
