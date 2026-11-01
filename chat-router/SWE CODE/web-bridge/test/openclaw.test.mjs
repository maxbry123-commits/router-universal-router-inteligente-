import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import crypto from "node:crypto";
import os from "node:os";
import path from "node:path";
import { asegurarWorkspace, vigilarWorkspace, leerConfig, configVigente, vigilarConfig, espejo, normalizarEjecutor, EJECUTORES_TOOLS, catalogoTools, constitucionOficial, rutaConstitucion, claveEspacio, rutaArchivoChat, espacioDe, nombreArchivoValido, textoDeBase64, armarContextoFijo } from "../src/openclaw.js";
import { fileURLToPath } from "node:url";

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "oc-test-"));

test("calcula <base>/openclaw-home-<uid>/.openclaw/workspace, la crea con 0700 y devuelve creada:true", () => {
  const base = tmp();
  try {
    const r = asegurarWorkspace({ uid: 4242, base });
    assert.equal(r.ruta, path.join(base, "openclaw-home-4242", ".openclaw", "workspace"));
    assert.equal(r.creada, true);
    const st = fs.statSync(r.ruta);
    assert.ok(st.isDirectory());
    assert.equal(st.mode & 0o777, 0o700);
  } finally { fs.rmSync(base, { recursive: true, force: true }); }
});

test("si ya existe no la toca (creada:false, contenido intacto)", () => {
  const base = tmp();
  try {
    const a = asegurarWorkspace({ uid: 1, base });
    fs.writeFileSync(path.join(a.ruta, "x.txt"), "hola");
    const b = asegurarWorkspace({ uid: 1, base });
    assert.equal(b.creada, false); assert.equal(b.ruta, a.ruta);
    assert.equal(fs.readFileSync(path.join(a.ruta, "x.txt"), "utf8"), "hola");
  } finally { fs.rmSync(base, { recursive: true, force: true }); }
});

test("sin uid usa process.getuid() y sin base usa /tmp (fs inyectable, no escribe nada real)", () => {
  const llamadas = [];
  const fsFalso = { existsSync: () => false, mkdirSync: (p, o) => { llamadas.push([p, o]); } };
  const r = asegurarWorkspace({ fs: fsFalso });
  assert.equal(r.ruta, `/tmp/openclaw-home-${process.getuid()}/.openclaw/workspace`);
  assert.equal(r.creada, true);
  assert.deepEqual(llamadas, [[r.ruta, { recursive: true, mode: 0o700 }]]);
});

test("OPENCLAW_WORKSPACE_DIR tiene prioridad sobre la ruta calculada", () => {
  const base = tmp(), previo = process.env.OPENCLAW_WORKSPACE_DIR;
  try {
    const destino = path.join(base, "otro", "ws");
    process.env.OPENCLAW_WORKSPACE_DIR = destino;
    const r = asegurarWorkspace({ uid: 1, base });
    assert.equal(r.ruta, destino); assert.equal(r.creada, true); assert.ok(fs.existsSync(destino));
    assert.ok(!fs.existsSync(path.join(base, "openclaw-home-1")));
  } finally {
    if (previo === undefined) delete process.env.OPENCLAW_WORKSPACE_DIR; else process.env.OPENCLAW_WORKSPACE_DIR = previo;
    fs.rmSync(base, { recursive: true, force: true });
  }
});

test("vigilarWorkspace: comprueba al arrancar, repone si se borra, avisa solo al crear, y el timer es unref", async () => {
  const base = tmp(), previo = process.env.OPENCLAW_WORKSPACE_DIR, warn = console.warn, avisos = [];
  process.env.OPENCLAW_WORKSPACE_DIR = path.join(base, "ws");
  console.warn = (...a) => avisos.push(a.join(" "));
  let t;
  try {
    t = vigilarWorkspace(20);
    assert.ok(fs.existsSync(process.env.OPENCLAW_WORKSPACE_DIR), "se crea al arrancar");
    assert.equal(avisos.length, 1);
    await new Promise((ok) => setTimeout(ok, 80));
    assert.equal(avisos.length, 1, "no avisa si ya existe");
    fs.rmSync(process.env.OPENCLAW_WORKSPACE_DIR, { recursive: true });
    await new Promise((ok) => setTimeout(ok, 120));
    assert.ok(fs.existsSync(process.env.OPENCLAW_WORKSPACE_DIR), "se repone");
    assert.equal(avisos.length, 2);
    assert.equal(t.hasRef(), false, "timer con unref");
  } finally {
    clearInterval(t); console.warn = warn;
    if (previo === undefined) delete process.env.OPENCLAW_WORKSPACE_DIR; else process.env.OPENCLAW_WORKSPACE_DIR = previo;
    fs.rmSync(base, { recursive: true, force: true });
  }
});

// ---------- configuracion vigente de OpenClaw (solo lectura, sin secretos): la leen Vercel y el Space por GET /v1/openclaw ----------
const escribirConfig = (dir, extra = {}) => {
  fs.writeFileSync(path.join(dir, "provider-openclaw.json"), JSON.stringify({ provider: "swecode", nombre: "SWE", tipo: "openai-compatible", base_url: "http://localhost:7870/v1", api_key: "SECRETO-NO-DEBE-SALIR", modelos: [{ id: "web-qwen38max", nombre: "Qwen" }], ...extra }));
  fs.writeFileSync(path.join(dir, "swen.json"), JSON.stringify({ modos: ["revision", "solucion"], seleccion_modelo: { aliases: { "web-qwen38max": ["qwen38"] } }, credenciales: { x: "SECRETO-2" } }));
};

test("leerConfig: provider, modelos, modos y alias; nunca api_key ni credenciales; version estable", () => {
  const dir = tmp();
  try {
    escribirConfig(dir);
    const c = leerConfig({ dir });
    assert.equal(c.provider.provider, "swecode"); assert.equal(c.provider.base_url, "http://localhost:7870/v1");
    assert.deepEqual(c.provider.modelos.map(m => m.id), ["web-qwen38max"]);
    assert.deepEqual(c.modos, ["revision", "solucion"]); assert.deepEqual(c.aliases, { "web-qwen38max": ["qwen38"] });
    assert.ok(!JSON.stringify(c).includes("SECRETO"), "sin secretos"); assert.ok(!("api_key" in c.provider));
    assert.equal(leerConfig({ dir }).version, c.version, "misma config => misma version");
    escribirConfig(dir, { modelos: [{ id: "otro", nombre: "Otro" }] });
    assert.notEqual(leerConfig({ dir }).version, c.version, "config distinta => version distinta");
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test("leerConfig: sin provider-openclaw.json devuelve null; swen.json ausente no la rompe", () => {
  const dir = tmp();
  try {
    assert.equal(leerConfig({ dir }), null);
    fs.writeFileSync(path.join(dir, "provider-openclaw.json"), JSON.stringify({ provider: "swecode", modelos: [] }));
    assert.deepEqual(leerConfig({ dir }).modos, []);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test("vigilarConfig: toma la config al arrancar y la mantiene al dia en cada vuelta (timer unref)", async () => {
  const dir = tmp(); let t;
  try {
    escribirConfig(dir);
    t = vigilarConfig(20, { dir });
    assert.equal(configVigente({ dir }).provider.modelos[0].id, "web-qwen38max");
    escribirConfig(dir, { modelos: [{ id: "nuevo-modelo", nombre: "N" }] });
    await new Promise((ok) => setTimeout(ok, 120));
    assert.equal(configVigente({ dir }).provider.modelos[0].id, "nuevo-modelo", "el vigilante la actualizo");
    assert.equal(t.hasRef(), false);
  } finally { clearInterval(t); fs.rmSync(dir, { recursive: true, force: true }); }
});

// ---------- ESPEJO de emergencia: OpenClaw usa las mismas funciones del chat Yaiwes (Router MVP) si la UI de Vercel/Space cae ----------
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");  // chat-router/

test("espejo: sin env usa el Router local 7861 y lista mcp, plugins, almacen, memoria, constitucion y tools", () => {
  const e = espejo({ env: {} });
  assert.equal(e.router_url, "http://127.0.0.1:7861"); assert.equal(e.router_url_origen, "defecto");
  assert.deepEqual(Object.keys(e.endpoints).sort(), ["almacen", "chat", "constitucion", "health", "mcp", "memoria", "plugins", "tools", "ui"]);
  assert.deepEqual([e.endpoints.mcp.metodo, e.endpoints.mcp.ruta], ["POST", "/mcp"]);
  assert.equal(e.endpoints.plugins.ruta, "/plugins/{plugin}/call/{accion}");
  assert.equal(e.endpoints.almacen.ruta, "/almacen");
  assert.deepEqual(Object.values(e.endpoints.memoria).map((x) => x.ruta).sort(), ["/memoria/load", "/memoria/save", "/memoria/search"]);
  assert.equal(e.endpoints.constitucion.campo, "constitucion"); assert.equal(e.endpoints.constitucion.ruta, "/chat/send");
  assert.ok(e.plugins.includes("motor_archivos") && e.plugins.includes("nct_loop") && e.plugins.includes("deepseek_harness"));
});

test("espejo: RIU_ROUTER_URL manda (sin barra final) y marca el origen env", () => {
  const e = espejo({ env: { RIU_ROUTER_URL: "https://mi-router.hf.space/" } });
  assert.equal(e.router_url, "https://mi-router.hf.space"); assert.equal(e.router_url_origen, "env");
  assert.equal(espejo({ env: { RIU_ROUTER_URL: "   " } }).router_url, "http://127.0.0.1:7861");
});

test("espejo: auth solo con NOMBRES de cabecera/variables; ningun valor de clave sale jamas", () => {
  const env = { RIU_API_KEY: "SECRETO-API", RIU_MCP_KEY: "SECRETO-MCP", RIU_ROUTER_API_KEY: "SECRETO-ROUTER", HF_TOKEN: "hf_SECRETO" };
  const e = espejo({ env }), txt = JSON.stringify(e);
  assert.equal(e.auth.cabecera, "X-API-Key"); assert.equal(e.auth.alternativa, "Authorization: Bearer"); assert.equal(e.auth.query, "key");
  assert.ok(e.auth.variables.includes("RIU_API_KEY"));
  assert.ok(!/SECRETO/.test(txt), "sin valores");
  assert.deepEqual(e.auth.configuradas, ["RIU_API_KEY", "RIU_MCP_KEY", "RIU_ROUTER_API_KEY"], "solo los nombres de las variables presentes");
});

test("espejo: el catalogo de tools MCP coincide con las herramientas reales de mcp_route.py (sin deriva)", () => {
  const src = fs.readFileSync(path.join(REPO, "chat/backend/mvp/mcp_route.py"), "utf8");
  const reales = [...src.matchAll(/'name': '([a-z_]+)'/g)].map((m) => m[1]);
  assert.ok(reales.length >= 10);
  assert.deepEqual([...espejo({ env: {} }).tools.mcp].sort(), [...new Set(reales)].sort());
});

test("espejo: las rutas declaradas existen en el Router MVP (app.py / memoria.py / mcp_route.py)", () => {
  const leer = (f) => fs.readFileSync(path.join(REPO, "chat/backend/mvp", f), "utf8");
  const todo = leer("app.py") + leer("memoria.py") + leer("mcp_route.py");
  const e = espejo({ env: {} });
  for (const r of ["/mcp", "/plugins/{plugin}/call/{accion}", "/almacen", "/chat/send", "/health", "/memoria/save", "/memoria/load", "/memoria/search"]) assert.ok(todo.includes(r), r);
  assert.ok(e.endpoints.ui.ruta.includes("/chat/ui/") && leer("frontend_estatico.py").includes("/chat/ui/{ruta:path}"));
});

test("ejecutor_tools: solo 'swe' u 'openclaw'; todo lo demas cae a 'swe' (defecto)", () => {
  assert.deepEqual(EJECUTORES_TOOLS, ["swe", "openclaw"]);
  assert.equal(normalizarEjecutor("openclaw"), "openclaw"); assert.equal(normalizarEjecutor(" OpenClaw "), "openclaw");
  for (const v of ["swe", "", undefined, null, 5, "otro", "constructor"]) assert.equal(normalizarEjecutor(v), "swe", String(v));
  const c = espejo({ env: {} }).ejecutor_tools;
  assert.deepEqual([c.campo, c.defecto, c.valores], ["ejecutor_tools", "swe", ["swe", "openclaw"]]);
  assert.equal(c.openclaw.estado, "WAIT_TOOLS");
});

test("provider-openclaw.json (repo): trae la entrada MCP del Router para OpenClaw, sin valor de clave", () => {
  const c = leerConfig();  // dir por defecto = SWE CODE free del repo
  assert.ok(c && c.provider.mcp, "falta provider.mcp");
  const m = c.provider.mcp;
  assert.match(m.url, /\/mcp$/); assert.equal(m.cabecera_auth, "X-API-Key"); assert.equal(m.valor_desde_env, "RIU_API_KEY");
  assert.ok(m.url.includes("${RIU_ROUTER_URL"), "la URL se resuelve con RIU_ROUTER_URL");
  assert.deepEqual(Object.keys(m).filter((k) => /^(api_key|token|clave|valor)$/.test(k)), []);
  assert.equal(c.provider.ejecutor_tools.defecto, "swe");
});

// ---------- UI3: catalogo de TOOLS de OpenClaw = las funciones del chat Yaiwes que el Router YA expone por MCP/HTTP (sin deriva respecto al codigo del Router) ----------
const MVP = (f) => fs.readFileSync(path.join(REPO, "chat/backend/mvp", f), "utf8");

test("catalogoTools: cada tool MCP del Router (mcp_route.py) esta cubierta por una tool MCP o por su plugin HTTP equivalente", () => {
  const reales = [...new Set([...MVP("mcp_route.py").matchAll(/'name': '([a-z_]+)'/g)].map((m) => m[1]))];
  const c = catalogoTools();
  const mcp = c.tools.filter((t) => t.via === "mcp").map((t) => t.destino.tool);
  const equivalentes = c.tools.map((t) => t.mcp_equivalente).filter(Boolean);
  for (const r of reales) assert.ok(mcp.includes(r) || equivalentes.includes(r), `tool MCP sin cubrir: ${r}`);
  for (const t of mcp) assert.ok(reales.includes(t), `el catalogo inventa la tool MCP ${t}`);
});

test("catalogoTools: plugins HTTP e acciones declaradas existen de verdad (loop_puente.PLUGINS, archivos.ACCIONES, plugin.py ACCIONES)", () => {
  const c = catalogoTools(), por = Object.fromEntries(c.tools.map((t) => [t.id, t]));
  const plugins = /PLUGINS = \(([^)]*)\)/.exec(MVP("loop_puente.py"))[1].match(/"(\w+)"/g).map((x) => x.slice(1, -1));
  for (const [id, plugin] of [["loop", "nct_loop"], ["cola", "cola50"], ["watchdog", "watchdog48"]]) {
    assert.ok(plugins.includes(plugin)); assert.equal(por[id].via, "plugin"); assert.equal(por[id].destino.plugin, plugin);
    const src = fs.readFileSync(path.join(REPO, "plugins", plugin, "plugin.py"), "utf8");
    const reales = [...src.matchAll(/^ACCIONES = \[([^\]]*)\]/gm)].flatMap((m) => m[1].match(/'(\w+)'/g).map((x) => x.slice(1, -1)));
    assert.deepEqual([...por[id].acciones].sort(), [...new Set(reales)].sort(), id);
  }
  const arch = /^ACCIONES = \(([^)]*)\)/m.exec(MVP("archivos/__init__.py"))[1].match(/"(\w+)"/g).map((x) => x.slice(1, -1));
  assert.deepEqual([...por.motor_archivos.acciones].sort(), [...arch].sort());
  assert.equal(por.motor_archivos.destino.plugin, "motor_archivos");
  assert.ok(MVP("app.py").includes('plugin == "motor_archivos"'));
});

test("catalogoTools: toda carpeta de chat-router/plugins esta como tool, como cubierta o como GAP honesto (nada se pierde en silencio)", () => {
  const c = catalogoTools();
  const nombres = fs.readdirSync(path.join(REPO, "plugins"), { withFileTypes: true }).filter((d) => d.name !== "__pycache__" && d.name !== "__init__.py").map((d) => d.name);
  const conocidos = new Set([...c.tools.map((t) => t.destino?.plugin), ...c.tools.map((t) => t.plugin_repo), ...c.cubiertos.map((x) => x.plugin), ...c.gaps.map((g) => g.id)]);
  for (const n of nombres) assert.ok(conocidos.has(n), `plugin sin clasificar: ${n}`);
  for (const g of c.gaps) { assert.ok(g.motivo.length > 20, g.id); assert.ok(!c.tools.some((t) => t.id === g.id), "un GAP no es tool"); }
  const ids = c.gaps.map((g) => g.id);
  for (const esperado of ["anclados-navegador", "constitucion-propia-navegador", "workflows-navegador", "workflow-loop-yaiwes"]) assert.ok(ids.includes(esperado), esperado);
  const ruteados = /if plugin not in \(([^)]*)\)/.exec(MVP("app.py"))[1];
  for (const g of c.gaps.filter((x) => x.plugin_repo === true)) assert.ok(!ruteados.includes(`"${g.id}"`), `${g.id} figura como ruteado por el Router: ya no es GAP`);
});

test("catalogoTools: lo que el navegador guarda (anclados de la pestana, constitucion propia) llega al Router solo como CAMPOS de /chat/send; el GAP lo dice y apunta a chat_send", () => {
  const c = catalogoTools(), t = c.tools.find((x) => x.id === "chat_send");
  assert.deepEqual([t.via, t.destino.metodo, t.destino.ruta], ["http", "POST", "/chat/send"]);
  assert.ok(t.campos.includes("anclados") && t.campos.includes("constitucion"));
  const app = MVP("app.py"); assert.ok(app.includes('q.get("anclados")') && app.includes('q.get("constitucion")'));
  for (const id of ["anclados-navegador", "constitucion-propia-navegador"]) assert.equal(c.gaps.find((g) => g.id === id).usar_con, "chat_send");
  assert.equal(c.gaps.find((g) => g.id === "workflows-navegador").usar_con, "workflows");
});

test("catalogoTools: las REPLICAS (anclaje, constitucion, contexto) solo leen, y las vias que usan existen en el codigo del Router", () => {
  const c = catalogoTools(), por = Object.fromEntries(c.tools.map((t) => [t.id, t]));
  for (const id of ["anclaje", "constitucion", "contexto"]) { assert.equal(por[id].via, "replica", id); assert.equal(por[id].efectos, "lectura", id); assert.ok(!c.gaps.some((g) => g.id === id)); }
  const app = MVP("app.py"), control = MVP("control.py");
  // las acciones del servidor que la replica pide por /plugins/puente_chat/call/<accion> estan en control.ACCIONES y el Router las deriva a CONTROL
  const acciones = /^ACCIONES = \{([^}]*)\}/m.exec(control)[1].match(/"(\w+)"/g).map((x) => x.slice(1, -1));
  for (const a of ["archivos", "proyecto", "sandbox"]) assert.ok(acciones.includes(a), a);
  assert.ok(app.includes('if plugin not in ("fichas_qwen", "puente_chat", "almacen")') && app.includes("if accion in control.ACCIONES"));
  // lectura de contenido: /almacen leer destino hf; la ruta del archivo es la de control.ruta_archivo (sha1[:12] de "destino|project_id|sesion")
  assert.ok(control.includes('hashlib.sha1(clave_espacio(c).encode()).hexdigest()[:12]') && control.includes('"|".join((str(c.get("destino") or "chat"), str(c.get("project_id") or ""), str(c.get("sesion") or "web-general")))[:160]'));
  assert.ok(app.includes('"accion": "leer", "destino": "hf", "nombre": ruta'));
  // sandbox sin `texto` = lectura; proyecto op list|get = lectura; yaiwes_md leer y pendientes listar son lectura
  assert.ok(control.includes('if "texto" in c:') && control.includes('c.get("op") or "list"'));
});

test("catalogoTools: cada tool declara si tiene efectos; sin efectos = lectura; con efectos exigen operador identificado en el bridge; JSON sin secretos", () => {
  const c = catalogoTools();
  for (const t of c.tools) {
    assert.match(t.id, /^[a-z][a-z0-9_]{1,40}$/); assert.ok(["mcp", "plugin", "http", "harness", "replica"].includes(t.via), t.id);
    assert.ok(["lectura", "efectos", "por_accion"].includes(t.efectos), t.id);
    if (t.efectos === "por_accion") assert.ok(Array.isArray(t.lectura) && t.lectura.every((a) => t.acciones.includes(a)), t.id);
  }
  const por = Object.fromEntries(c.tools.map((t) => [t.id, t]));
  assert.equal(por.github_escribir.efectos, "efectos"); assert.equal(por.salud.efectos, "lectura"); assert.equal(por.almacen.efectos, "por_accion"); assert.ok(por.almacen.lectura.includes("leer"));
  assert.ok(!/Bearer|X-API-Key:|sk-|hf_[A-Za-z0-9]{10}/.test(JSON.stringify(c)));
});

// ---------- REPLICAS de lectura: calculos propios del bridge (no tocan el Router ni el chat) ----------
test("rutaArchivoChat: misma ruta que control.ruta_archivo del Router (vector calculado con Python: constitucion||web-general -> 509e21d6a3cc)", () => {
  assert.equal(claveEspacio({ destino: "constitucion" }), "constitucion||web-general");
  assert.equal(rutaArchivoChat({ destino: "constitucion" }, "a b.txt"), "chat_archivos/509e21d6a3cc/a b.txt");
  assert.equal(claveEspacio({ destino: "proyecto", project_id: "p1", sesion: "s" }), "proyecto|p1|s");
  assert.equal(claveEspacio({}), "chat||web-general");
});

test("espacioDe / nombreArchivoValido: nada de rutas, separadores ni espacios desconocidos", () => {
  assert.deepEqual(espacioDe({}), { destino: "chat" });
  assert.deepEqual(espacioDe({ destino: "proyecto", project_id: "p-1", sesion: "web-general" }), { destino: "proyecto", project_id: "p-1", sesion: "web-general" });
  for (const mal of [{ destino: "x" }, { sesion: "a/b" }, { sesion: "" }, { project_id: "../x" }, { sesion: 5 }]) assert.equal(espacioDe(mal), null, JSON.stringify(mal));
  for (const ok of ["a.txt", "mi doc (1).md", "informe-ñandú.txt"]) assert.ok(nombreArchivoValido(ok), ok);
  for (const mal of ["../x", "a/b", "..", ".env", "", "x".repeat(130), 5]) assert.ok(!nombreArchivoValido(mal), String(mal));
});

test("textoDeBase64: texto con tope y marca de truncado; binario solo informa el tamano", () => {
  assert.deepEqual(textoDeBase64(Buffer.from("hola").toString("base64")), { binario: false, bytes: 4, texto: "hola", truncado: false });
  assert.equal(textoDeBase64(Buffer.from("abcdef").toString("base64"), 3).texto, "abc"); assert.equal(textoDeBase64(Buffer.from("abcdef").toString("base64"), 3).truncado, true);
  assert.deepEqual(textoDeBase64(Buffer.from([1, 0, 2]).toString("base64")), { binario: true, bytes: 3 });
});

test("constitucionOficial: lee el archivo real del repo (id, version, FAIL_CLOSED, sha256); RIU_CONSTITUCION_PATH manda; inexistente o invalida = codigo, sin ruta", () => {
  const c = constitucionOficial({ env: {} });
  assert.equal(c.ok, true); assert.equal(c.id, "CONSTITUCION-YAIWES"); assert.equal(c.version, "1.1.0"); assert.match(c.sha256, /^[0-9a-f]{64}$/);
  assert.equal(c.sha256, crypto.createHash("sha256").update(fs.readFileSync(path.join(REPO, "plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json"))).digest("hex"));
  const dir = tmp();
  try {
    const f = path.join(dir, "c.json");
    assert.deepEqual(constitucionOficial({ env: { RIU_CONSTITUCION_PATH: f } }), { ok: false, codigo: "CONSTITUCION_NO_ENCONTRADA" });
    fs.writeFileSync(f, "{no json"); assert.equal(constitucionOficial({ env: { RIU_CONSTITUCION_PATH: f } }).codigo, "CONSTITUCION_INVALIDA");
    fs.writeFileSync(f, JSON.stringify({ id: "X", version: "1", modo: "ABIERTO" })); assert.equal(constitucionOficial({ env: { RIU_CONSTITUCION_PATH: f } }).codigo, "CONSTITUCION_INVALIDA", "fail-closed como _gov_base");
    fs.writeFileSync(f, JSON.stringify({ id: "X", version: "2", modo: "FAIL_CLOSED" })); assert.equal(constitucionOficial({ env: { RIU_CONSTITUCION_PATH: f } }).version, "2");
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
  assert.ok(rutaConstitucion({}).endsWith("plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json"));
});

test("armarContextoFijo: mismas capas que app._chat_ficha (encendidas = con texto), en el mismo orden y formato [nombre]\\ntexto", () => {
  const c = armarContextoFijo({ constitucion: "LEY", yaiwes: "", sandbox: "  ", pendientes: "- [ ] a" });
  assert.deepEqual(c.capas.map((x) => x.presente), [true, false, false, true]);
  assert.equal(c.texto, "[CONSTITUCION OFICIAL YAIWES (solo lectura): es ley para este trabajo; respetala al programar y en lo que respondes]\nLEY\n\n[PENDIENTES (lista compartida; la herramienta pendientes la consulta y la actualiza)]\n- [ ] a");
  assert.equal(armarContextoFijo({}).texto, "");
  const app = MVP("app.py");
  for (const n of ["CONSTITUCION: es ley para este trabajo", "yaiwes.md (información del proyecto", "SANDBOX (system prompt de code)", "PENDIENTES (lista compartida"]) assert.ok(app.includes(n), n);
});
