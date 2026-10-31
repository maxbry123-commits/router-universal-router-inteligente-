// SWEN CODE free — puente-movil.
// Canal: la APK abre WSS saliente a /agente (el movil esta tras NAT).
// API para modelos: MCP-HTTP JSON-RPC en POST /mcp (initialize, tools/list, tools/call).
// Acciones al movil: abrir_url, leer_pantalla, escribir, tap, atras.
// Seguridad: fail-closed (sin PUENTE_TOKEN de >= 16 caracteres el proceso no arranca),
// comparacion de tokens en tiempo constante, body maximo 1 MB.

const http = require("http");
const crypto = require("crypto");

const MIN_TOKEN = 16;
const MAX_BODY = 1024 * 1024; // 1 MB
let agente = null;               // ws del movil conectado
let seq = 0;
const pendientes = new Map();    // id -> {resolve, timer}

const TOOLS = [
  { name: "abrir_url",     description: "Abre una URL (solo http/https) en Chrome del movil", inputSchema: { type: "object", properties: { url: { type: "string" } }, required: ["url"] } },
  { name: "leer_pantalla", description: "Lee el texto visible de la pantalla del movil (accesibilidad)", inputSchema: { type: "object", properties: {} } },
  { name: "escribir",      description: "Escribe texto en el campo enfocado del movil", inputSchema: { type: "object", properties: { texto: { type: "string" } }, required: ["texto"] } },
  { name: "tap",           description: "Toca coordenadas x,y de la pantalla", inputSchema: { type: "object", properties: { x: { type: "number" }, y: { type: "number" } }, required: ["x", "y"] } },
  { name: "atras",         description: "Boton atras del movil", inputSchema: { type: "object", properties: {} } },
];

// null si el token sirve; si no, el motivo (para el mensaje de arranque).
function validarToken(token) {
  if (typeof token !== "string" || !token) return "PUENTE_TOKEN no definido: el puente no arranca sin token (fail-closed)";
  if (token.length < MIN_TOKEN) return `PUENTE_TOKEN demasiado corto: minimo ${MIN_TOKEN} caracteres`;
  return null;
}

// Igualdad en tiempo constante: se comparan los sha256 de ambos lados (misma longitud siempre).
function igualesSeguro(a, b) {
  const ha = crypto.createHash("sha256").update(String(a)).digest();
  const hb = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(ha, hb);
}

// HTTP: Authorization: Bearer <token>. Sin token valido configurado, nunca autoriza.
function autorizado(headers, token) {
  if (validarToken(token)) return false;
  const h = headers && headers["authorization"];
  if (typeof h !== "string" || !h.startsWith("Bearer ")) return false;
  return igualesSeguro(h.slice(7), token);
}

// WS: subprotocolo "token-<token>" (cabecera Sec-WebSocket-Protocol, lista separada por comas) o Bearer.
function autorizadoWs(headers, token) {
  if (validarToken(token)) return false;
  if (autorizado(headers, token)) return true;
  const p = headers && headers["sec-websocket-protocol"];
  if (typeof p !== "string") return false;
  return p.split(",").some((x) => x.trim().startsWith("token-") && igualesSeguro(x.trim().slice(6), token));
}

function alMovil(accion, args) {
  return new Promise((resolve, reject) => {
    if (!agente || agente.readyState !== 1) return reject(new Error("APK_NO_CONECTADA"));
    const id = ++seq;
    const timer = setTimeout(() => { pendientes.delete(id); reject(new Error("TIMEOUT_MOVIL")); }, 30000);
    pendientes.set(id, { resolve, timer });
    agente.send(JSON.stringify({ id, accion, args: args || {} }));
  });
}

const rpcError = (id, code, message) => ({ jsonrpc: "2.0", id: id === undefined ? null : id, error: { code, message } });

// Logica JSON-RPC pura: recibe el body ya parseado y devuelve el objeto de respuesta. Nunca lanza.
async function manejarMcp(msg, enviarAlMovil = alMovil) {
  if (!msg || typeof msg !== "object" || Array.isArray(msg)) return rpcError(null, -32600, "invalid request");
  const { id, method, params } = msg;
  if (typeof method !== "string") return rpcError(id, -32600, "invalid request");
  try {
    if (method === "initialize")
      return { jsonrpc: "2.0", id, result: { protocolVersion: "2024-11-05", capabilities: { tools: {} }, serverInfo: { name: "swecode-puente-movil", version: "0.1.0" } } };
    if (method === "tools/list")
      return { jsonrpc: "2.0", id, result: { tools: TOOLS } };
    if (method === "tools/call") {
      if (!params || typeof params !== "object" || Array.isArray(params) || !TOOLS.some((t) => t.name === params.name))
        return rpcError(id, -32602, "invalid params");
      const r = await enviarAlMovil(params.name, params.arguments);
      return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text: typeof r === "string" ? r : JSON.stringify(r) }] } };
    }
    return rpcError(id, -32601, "method not found");
  } catch (e) {
    return rpcError(id, -32000, String((e && e.message) || e));
  }
}

function jsonRpc(res, obj) {
  res.writeHead(200, { "content-type": "application/json" });
  res.end(JSON.stringify(obj));
}

function crearServidor({ token, enviarAlMovil } = {}) {
  return http.createServer((req, res) => {
    if (req.url === "/health") return jsonRpc(res, { ok: true, movil: !!agente });
    if (req.url === "/mcp" && req.method === "POST") {
      if (!autorizado(req.headers, token)) {
        res.writeHead(401); return res.end("unauthorized");
      }
      const declarado = Number(req.headers["content-length"]);
      const demasiado = () => {
        res.writeHead(413, { connection: "close" });
        res.end("payload too large", () => req.destroy());
      };
      if (declarado > MAX_BODY) return demasiado();
      const trozos = [];
      let total = 0, cortado = false;
      req.on("data", (c) => {
        if (cortado) return;
        total += c.length;
        if (total > MAX_BODY) { cortado = true; trozos.length = 0; return demasiado(); }
        trozos.push(c);
      });
      req.on("error", () => {});
      req.on("end", async () => {
        if (cortado) return;
        let msg;
        try { msg = JSON.parse(Buffer.concat(trozos).toString("utf8")); } catch { return jsonRpc(res, rpcError(null, -32700, "parse error")); }
        jsonRpc(res, await manejarMcp(msg, enviarAlMovil));
      });
      return;
    }
    res.writeHead(404); res.end();
  });
}

// `ws` se carga solo aqui (perezoso) para poder probar el resto sin la dependencia.
function adjuntarWs(server, token) {
  const { WebSocketServer } = require("ws");
  const wss = new WebSocketServer({ server, path: "/agente" });
  wss.on("connection", (ws, req) => {
    if (!autorizadoWs(req.headers, token)) { ws.close(4401, "unauthorized"); return; }
    agente = ws;
    ws.on("message", (d) => {
      try {
        const m = JSON.parse(d);
        const p = pendientes.get(m.id);
        if (p) { clearTimeout(p.timer); pendientes.delete(m.id); p.resolve(m.resultado); }
      } catch {}
    });
    ws.on("close", () => { if (agente === ws) agente = null; });
  });
  return wss;
}

function main() {
  const token = process.env.PUENTE_TOKEN || "";
  const motivo = validarToken(token);
  if (motivo) { console.error("puente-movil: " + motivo); process.exit(1); }
  const PORT = process.env.PUENTE_PORT || 7860;
  const server = crearServidor({ token });
  adjuntarWs(server, token);
  server.listen(PORT, () => console.log("puente-movil :" + PORT));
  // se actualiza solo cuando llega codigo nuevo (mismo vigilante del bridge): sin reiniciar el Space
  try {
    const ruta = require("path").resolve(__dirname, "../../SWE CODE/web-bridge/src/autoactualizar.js");
    import(require("url").pathToFileURL(ruta).href).then((m) => m.vigilarActualizacion()).catch(() => {});
  } catch { /* sin el vigilante, sigue funcionando */ }
}

if (require.main === module) main();

module.exports = { validarToken, autorizado, autorizadoWs, manejarMcp, crearServidor, adjuntarWs, TOOLS, MAX_BODY, MIN_TOKEN };
