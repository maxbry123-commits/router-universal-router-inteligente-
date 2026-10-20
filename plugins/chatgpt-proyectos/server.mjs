// Puente ChatGPT -> Router (Director 2026-10-04).
// Un inicio de sesion por perfil (A, B, C...), 30 proyectos con estado aislado, cache y rotacion de perfil.
// Cada perfil es su propio cliente @siwc/local con su carpeta, asi varios proyectos corren en paralelo.
// Las credenciales se cifran (AES-256-GCM) con una llave derivada de la clave del banco (variable RIU_BANCO_CLAVE).
import http from "node:http";
import { createHash, timingSafeEqual } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { createChatGPT } from "@siwc/local";

const DATA = process.env.PUENTE_DATOS || "/data/chatgpt-proyectos";
const PUERTO = Number(process.env.PORT || 7861);
const CLAVE_PUENTE = process.env.PUENTE_CLAVE || ""; // la pide el Router en la cabecera x-puente-clave
const BANCO = process.env.RIU_BANCO_CLAVE || "";
const PERFILES = (process.env.PUENTE_PERFILES || "A").split(",").map(s => s.trim()).filter(Boolean);
const N_PROYECTOS = Number(process.env.PUENTE_PROYECTOS || 50);
const CACHE_S = Number(process.env.PUENTE_CACHE_S || 600);
if (!BANCO || !CLAVE_PUENTE) { console.error("Faltan RIU_BANCO_CLAVE o PUENTE_CLAVE"); process.exit(1); }

import { cifradoBanco } from "./cifrado.mjs";
const cifrado = cifradoBanco(BANCO);

// --- perfiles: un cliente por cuenta ---
const perfiles = {};
const carpeta = (p) => join(DATA, "perfiles", p);
// En la VM no se hace OAuth: la sesion llega por importacion (guia oficial "Self-hosted VMs").
const nuevo = (p) => createChatGPT({ appName: "YAIWES Proyectos", appId: `yaiwes-proyectos-${p.toLowerCase()}`, redirectPort: 0,
  storageDir: carpeta(p), credentialEncryption: cifrado,
  openBrowser: () => { throw new Error("En la VM no se inicia sesion: importa la credencial hecha en tu dispositivo."); } });
for (const p of PERFILES) perfiles[p] = { client: nuevo(p) };
const conectado = async (p) => { const s = await perfiles[p].client.getSession(); return s.status === "connected" && s.sharing; };

// --- 30 proyectos con estado aislado ---
const pid = (i) => `proyecto-${String(i).padStart(2, "0")}`;
const dir = (id) => join(DATA, "proyectos", id);
async function leer(id, f, def) { try { return JSON.parse(await readFile(join(dir(id), f), "utf8")); } catch { return def; } }
async function escribir(id, f, v) { await mkdir(dir(id), { recursive: true }); await writeFile(join(dir(id), f), JSON.stringify(v, null, 1)); }
const base = (i) => ({ project_id: pid(i), nombre: `Proyecto ${String(i).padStart(2, "0")}`, instrucciones: "", modelo: null,
  perfil: PERFILES[0], herramientas: [], max_historial: 40 });
async function config(id) { const i = Number(id.split("-")[1]); return { ...base(i), ...(await leer(id, "config.json", {})) }; }
const valido = (id) => /^proyecto-\d{2}$/.test(id) && Number(id.split("-")[1]) >= 1 && Number(id.split("-")[1]) <= N_PROYECTOS;

// --- cache corto por proyecto (misma pregunta, mismo contexto) ---
const cache = new Map();

async function ejecutar(id, texto, chat = "principal") {
  const cfg = await config(id);
  const hist = await leer(id, `chat-${chat}.json`, []);
  const memoria = await leer(id, "memoria.json", []);
  const clave = createHash("sha256").update(JSON.stringify([id, chat, hist.length, texto, cfg.instrucciones, cfg.modelo])).digest("hex");
  const c = cache.get(clave); if (c && Date.now() - c.t < CACHE_S * 1000) return { ...c.r, cache: true };
  const orden = [cfg.perfil]; // cada proyecto usa su perfil elegido; sin rotar cuentas para eludir limites
  let ultimo;
  for (const p of orden) {
    if (!perfiles[p] || !(await conectado(p))) { ultimo = `perfil ${p} sin sesion`; continue; }
    try {
      const modelos = await perfiles[p].client.listModels();
      const modelo = (cfg.modelo && modelos.find(m => m.slug === cfg.modelo)?.slug) || modelos[0]?.slug;
      if (!modelo) { ultimo = `perfil ${p} sin modelos`; continue; }
      const instrucciones = [cfg.instrucciones, memoria.length ? "Memoria del proyecto:\n" + memoria.join("\n") : ""].filter(Boolean).join("\n\n");
      const input = [...hist.slice(-cfg.max_historial).map(m => ({ role: m.role, content: m.content })), { role: "user", content: texto }];
      const { text } = await perfiles[p].client.streamResponse({ model: modelo, input, instructions: instrucciones || undefined });
      const t = Date.now();
      hist.push({ role: "user", content: texto, t }, { role: "assistant", content: text, t, modelo, perfil: p });
      await escribir(id, `chat-${chat}.json`, hist);
      const r = { proyecto: id, chat, perfil: p, modelo, texto: text };
      cache.set(clave, { t, r }); return r;
    } catch (e) { ultimo = `perfil ${p}: ${e.code || e.message}`; }
  }
  throw Object.assign(new Error(ultimo || "sin perfiles"), { status: 503 });
}

// --- HTTP para el Router ---
const ok = (res, code, v) => { res.writeHead(code, { "content-type": "application/json" }); res.end(JSON.stringify(v)); };
const cuerpo = (req) => new Promise((r) => { let b = ""; req.on("data", d => b += d); req.on("end", () => { try { r(JSON.parse(b || "{}")); } catch { r({}); } }); });
const autorizado = (req) => { const a = Buffer.from(String(req.headers["x-puente-clave"] || "")), b = Buffer.from(CLAVE_PUENTE);
  return a.length === b.length && timingSafeEqual(a, b); };

http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, "http://x"); const partes = u.pathname.split("/").filter(Boolean);
    if (u.pathname === "/salud") return ok(res, 200, { ok: true });
    if (!autorizado(req)) return ok(res, 401, { error: "clave" });
    if (req.method === "GET" && u.pathname === "/estado") {
      const est = {}; for (const p of PERFILES) est[p] = await perfiles[p].client.getSession();
      return ok(res, 200, { perfiles: est, proyectos: N_PROYECTOS });
    }
    if (partes[0] === "perfiles" && perfiles[partes[1]]) {
      const P = perfiles[partes[1]];
      if (partes[2] === "importar" && req.method === "POST") { // credencial protegida hecha en el dispositivo local
        const auth = (await cuerpo(req)).auth;
        if (!auth || auth.version !== 3 || auth.provider !== cifrado.id || typeof auth.ciphertext !== "string")
          return ok(res, 400, { error: "credencial invalida (debe venir de login-local.mjs con la clave del banco)" });
        await mkdir(carpeta(partes[1]), { recursive: true });
        await writeFile(join(carpeta(partes[1]), "chatgpt-auth.json"), JSON.stringify(auth), { mode: 0o600 }); // chatgpt-host.json de la VM no se toca
        P.client = nuevo(partes[1]);
        return ok(res, 200, { sesion: await P.client.getSession() });
      }
      if (partes[2] === "modelos") return ok(res, 200, await P.client.listModels());
    }
    if (req.method === "GET" && u.pathname === "/proyectos") {
      const l = []; for (let i = 1; i <= N_PROYECTOS; i++) l.push(await config(pid(i))); return ok(res, 200, l);
    }
    if (partes[0] === "proyectos" && valido(partes[1] || "")) {
      const id = partes[1];
      if (req.method === "PUT" && partes.length === 2) { const b = await cuerpo(req); delete b.project_id;
        await escribir(id, "config.json", { ...(await leer(id, "config.json", {})), ...b }); return ok(res, 200, await config(id)); }
      if (req.method === "POST" && partes[2] === "chat") { const b = await cuerpo(req);
        return ok(res, 200, await ejecutar(id, String(b.texto || ""), b.chat || "principal")); }
      if (req.method === "POST" && partes[2] === "memoria") { const b = await cuerpo(req); const m = await leer(id, "memoria.json", []);
        m.push(String(b.nota || "")); await escribir(id, "memoria.json", m); return ok(res, 200, { notas: m.length }); }
      if (req.method === "GET" && partes[2] === "chat") return ok(res, 200, await leer(id, `chat-${u.searchParams.get("chat") || "principal"}.json`, []));
    }
    if (req.method === "POST" && u.pathname === "/paralelo") { // varios proyectos a la vez, cada uno con su contexto
      const b = await cuerpo(req); const ids = (b.proyectos || []).filter(valido);
      const r = await Promise.allSettled(ids.map(id => ejecutar(id, String(b.texto || ""), b.chat || "principal")));
      return ok(res, 200, r.map((x, i) => x.status === "fulfilled" ? x.value : { proyecto: ids[i], error: x.reason.message }));
    }
    ok(res, 404, { error: "ruta" });
  } catch (e) { ok(res, e.status || 500, { error: e.message }); }
}).listen(PUERTO, () => console.log(`puente chatgpt en ${PUERTO}, perfiles ${PERFILES.join(",")}, proyectos ${N_PROYECTOS}`));
