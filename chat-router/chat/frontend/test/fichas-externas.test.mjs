// fichas-externas.js: solo los modelos elegidos por el Director, y solo si aparecen en el catalogo REAL (GET /chat/providers/{groq,nvidia}/models).
// Un id elegido que el proveedor no publica se muestra NO DISPONIBLE y NUNCA se sustituye por otro en silencio.
import test from "node:test";
import assert from "node:assert/strict";

const storage = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), clear: () => m.clear() }; };
globalThis.localStorage = storage(); globalThis.sessionStorage = storage();
sessionStorage.setItem("riu_clave", "prueba");
globalThis.window = globalThis;
globalThis.addEventListener = () => {}; globalThis.dispatchEvent = (e) => { eventos.push(e); };
globalThis.CustomEvent = class { constructor(type, opts) { this.type = type; this.detail = opts?.detail; } };
globalThis.MutationObserver = class { observe() {} };
globalThis.document = { readyState: "loading", addEventListener() {}, getElementById() { return null; }, createElement: () => ({}), body: { append() {} } };
const eventos = [];
let catalogos = {}, providers = ["groq", "nvidia"], fallos = {}, puente = null;
const ok = (cuerpo) => ({ ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => cuerpo, text: async () => JSON.stringify(cuerpo) });
globalThis.fetch = async (url) => {
  const ruta = String(url).replace(/^https?:\/\/[^/]+/, "");
  if (ruta === "/web/v1/modelos/disponibilidad" && puente) return ok({ ok: true, modelos: puente.modelos, locales: puente.locales || [], ...(puente.configurados ? { configurados: puente.configurados } : {}) });
  if (ruta === "/web/v1/claves" && puente) return ok({ ok: true, groq: puente.groq, nvidia: puente.nvidia });
  if (ruta === "/chat/providers") return ok({ providers: providers.map((id) => ({ id })) });
  const m = ruta.match(/^\/chat\/providers\/(groq|nvidia)\/models$/);
  if (m && fallos[m[1]]) return { ok: false, status: 502, headers: { get: () => "application/json" }, json: async () => ({ detail: fallos[m[1]] }), text: async () => JSON.stringify({ detail: fallos[m[1]] }) };
  if (m) return ok({ models: (catalogos[m[1]] || []).map((id) => ({ model_id: id, label: id.split("/").slice(1).join("/"), tipo: "texto" })) });
  throw new Error("fetch inesperado: " + ruta);
};
const { MODELOS_SELECCIONADOS, seleccionar, cargar } = await import("../fichas-externas.js");

const GROQ = "groq/qwen/qwen3.8-27b";
const NV = ["nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"];
const reiniciar = () => { localStorage.clear(); eventos.length = 0; fallos = {}; puente = null; providers = ["groq", "nvidia"]; window.RIU_CONFIG = { modelos: [{ id: "nv-muse-glimmer", etiqueta: "viejo" }] }; };

test("MODELOS_SELECCIONADOS tiene exactamente los 5 ids del Director, Muse Glimmer una sola vez", () => {
  assert.deepEqual([...MODELOS_SELECCIONADOS], [GROQ, ...NV]);
  assert.equal([...MODELOS_SELECCIONADOS].filter((i) => i.includes("muse-glimmer")).length, 1);
  assert.equal(MODELOS_SELECCIONADOS.size, 5);
});

test("seleccionar muestra solo los elegidos del catalogo real; el resto del catalogo antiguo desaparece", () => {
  const groq = seleccionar("groq", ["groq/openai/gpt-oss-120b", GROQ, "groq/gemma2-9b-it"]);
  assert.deepEqual(groq.map((m) => [m.id, m.disponible, m.etiqueta]), [[GROQ, true, "Groq · Qwen 3.8 27B"]]);
  const nv = seleccionar("nvidia", ["nvidia/deepseek-ai/deepseek-v4.1-flash", NV[3], NV[0], NV[0], "nvidia/z-ai/glm-4.7"]);
  assert.deepEqual(nv.filter((m) => m.disponible).map((m) => m.id), [NV[0], NV[3]]);  // el duplicado del catalogo sale una vez
});

test("un id elegido que el proveedor no publica se muestra NO DISPONIBLE (no se oculta ni se reemplaza)", () => {
  const nv = seleccionar("nvidia", [NV[0], NV[3]]);
  assert.deepEqual(nv.map((m) => m.id), [NV[0], NV[3], NV[1], NV[2]]);  // disponibles primero, luego los NO DISPONIBLE en el orden del Director
  assert.deepEqual(nv.map((m) => m.disponible), [true, true, false, false]);
  assert.equal(nv[2].etiqueta, "NVIDIA · Muse Glimmer 30B — NO DISPONIBLE");
  assert.equal(nv[3].etiqueta, "NVIDIA · Nemotron 3 Ultra 550B — NO DISPONIBLE");
});

test("cargar: Groq y NVIDIA quedan solo con los modelos elegidos y el primero disponible es el defecto", async () => {
  reiniciar();
  catalogos = { groq: ["groq/openai/gpt-oss-120b", GROQ], nvidia: ["nvidia/deepseek-ai/deepseek-v4.1-flash", ...NV] };
  await cargar();
  assert.deepEqual(window.RIU_GROQ.lista.map((m) => m.id), [GROQ]);
  assert.equal(window.RIU_GROQ.modelo, GROQ); assert.equal(window.RIU_GROQ.aviso, "");
  assert.deepEqual(window.RIU_CONFIG.modelos.map((m) => m.id), NV);
  assert.equal(window.RIU_CONFIG.defecto, NV[0]);
  assert.ok(window.RIU_CONFIG.modelos.every((m) => !/NO DISPONIBLE/.test(m.etiqueta)));
  const ev = eventos.filter((e) => e.type === "riu:fichas").pop();
  assert.deepEqual(ev.detail, { groq: 1, nvidia: 4 });
});

test("cargar: si Groq no publica qwen3.8-27b NO se cambia a otro modelo del catalogo", async () => {
  reiniciar();
  catalogos = { groq: ["groq/openai/gpt-oss-120b", "groq/gemma2-9b-it"], nvidia: NV };
  await cargar();
  assert.deepEqual(window.RIU_GROQ.lista.map((m) => [m.id, m.disponible]), [[GROQ, false]]);
  assert.equal(window.RIU_GROQ.modelo, "");  // enviar-mensaje.js no envia nada con modelo vacio y dice el aviso
  assert.match(window.RIU_GROQ.aviso, /Qwen 3\.8 27B.*NO DISPONIBLE/);
});

test("cargar: la eleccion guardada que deja de existir no se sustituye en silencio; la disponible se conserva", async () => {
  reiniciar();
  localStorage.setItem("riu_groq_modelo", GROQ);
  catalogos = { groq: ["groq/otro"], nvidia: [NV[0], NV[3]] };
  await cargar();
  assert.equal(window.RIU_GROQ.modelo, "");
  catalogos.groq = [GROQ]; await cargar();
  assert.equal(window.RIU_GROQ.modelo, GROQ);
  catalogos.nvidia = [NV[3]]; await cargar();
  assert.equal(window.RIU_CONFIG.defecto, NV[3]);  // el primero DISPONIBLE (no el primero de la lista)
  assert.deepEqual(window.RIU_CONFIG.modelos.filter((m) => /NO DISPONIBLE/.test(m.etiqueta)).map((m) => m.id), [NV[0], NV[1], NV[2]]);
});

test("cargar: si el catalogo no se pudo leer no se afirma NO DISPONIBLE (se dice el error) y sin proveedor se avisa", async () => {
  reiniciar();
  fallos = { nvidia: "NVIDIA: ninguna de las 2 claves fue aceptada" };
  catalogos = { groq: [GROQ] };
  await cargar();
  assert.equal(window.RIU_GROQ.modelo, GROQ);
  assert.ok(!window.RIU_CONFIG.modelos.some((m) => /NO DISPONIBLE/.test(m.etiqueta)));  // sin lista nueva queda lo anterior, marcado como que responde Qwen
  assert.ok(window.RIU_CONFIG.modelos.every((m) => /responde Qwen/.test(m.etiqueta)));
  reiniciar();
  providers = ["nvidia"]; catalogos = { nvidia: NV };
  await cargar();
  assert.equal(window.RIU_GROQ.modelo, ""); assert.match(window.RIU_GROQ.aviso, /GROQ_API_KEY/);
});

test("X-Ray: banco cifrado del bridge controla los modelos en los selectores (no solo /chat/providers)", async () => {
  reiniciar();
  providers = []; // Router MVP NO posee las claves, pero el bridge SI.
  puente = { groq: 1, nvidia: 1, modelos: [
    { id: GROQ, proveedor: "groq", disponible: true },
    ...NV.map((id, i) => ({ id, proveedor: "nvidia", disponible: i === 0 ? true : null })),
  ], locales: [{ id: "hf/qwen3-0.6b", estado: "SIN VERIFICAR" }] };
  await cargar();
  assert.equal(window.RIU_GROQ.modelo, GROQ, "el modelo se selecciona con el banco real del bridge");
  assert.equal(window.RIU_CONFIG.defecto, NV[0]);
  assert.equal(window.RIU_CONFIG.modelos[0].disponible, true);
  assert.equal(window.RIU_CONFIG.modelos[1].disponible, null, "desconocido NO se declara no disponible");
  assert.equal(window.RIU_LOCAL.lista[0].id, "hf/qwen3-0.6b");
});

test("X-Ray: sin claves reales en el bridge no se marca DISPONIBLE un modelo externo", async () => {
  reiniciar();
  puente = { groq: 0, nvidia: 0, modelos: [
    { id: GROQ, proveedor: "groq", disponible: null },
    ...NV.map((id) => ({ id, proveedor: "nvidia", disponible: null })),
  ] };
  await cargar();
  assert.equal(window.RIU_GROQ.modelo, "");
  assert.equal(window.RIU_GROQ.lista[0].estado, "NO CONFIGURADO");
  assert.ok(window.RIU_CONFIG.modelos.every(m => m.disponible === false && m.estado === "NO CONFIGURADO"));
  assert.equal(window.RIU_CONFIG.defecto, "", "sin clave el selector NVIDIA no inventa un modelo funcional");
});

test("X-Ray: claves de entorno en el bridge habilitan el selector aunque el panel de claves no informe ese numero", async () => {
  reiniciar(); providers = [];
  puente = { groq: 0, nvidia: 0, configurados: { groq: true, nvidia: true },
    modelos: [{ id: GROQ, proveedor: "groq", disponible: true }, ...NV.map(id => ({ id, proveedor: "nvidia", disponible: null }))] };
  await cargar();
  assert.equal(window.RIU_GROQ.modelo, GROQ);
  assert.equal(window.RIU_GROQ.lista[0].estado, "DISPONIBLE");
  assert.equal(window.RIU_CONFIG.modelos[0].estado, "SIN VERIFICAR");
  assert.equal(window.RIU_CONFIG.modelos[0].disponible, null);
  assert.ok(!window.RIU_CONFIG.modelos.some(m => m.estado === "NO CONFIGURADO"));
});

test("X-Ray: disponibilidad sin contador y panel protegido NO se interpreta como cero claves", async () => {
  reiniciar(); providers = [];
  puente = { groq: 0, nvidia: 0, configurados: { groq: true, nvidia: true },
    modelos: [{ id: GROQ, proveedor: "groq", disponible: null }, ...NV.map(id => ({ id, proveedor: "nvidia", disponible: null }))] };
  await cargar();
  assert.equal(window.RIU_GROQ.lista[0].estado, "SIN VERIFICAR");
  assert.equal(window.RIU_GROQ.modelo, GROQ, "permite intentar el modelo exacto sin prometer conexion");
  assert.equal(window.RIU_CONFIG.defecto, NV[0]);
});
