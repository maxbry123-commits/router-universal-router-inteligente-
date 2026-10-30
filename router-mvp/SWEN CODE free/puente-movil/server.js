// SWEN CODE free — puente-movil.
// Canal: la APK abre WSS saliente a /agente (el movil esta tras NAT).
// API para modelos: MCP-HTTP JSON-RPC en POST /mcp (initialize, tools/list, tools/call).
// Acciones al movil: abrir_url, leer_pantalla, escribir, tap, atras.

const http = require("http");
const { WebSocketServer } = require("ws");

const PORT = process.env.PUENTE_PORT || 7860;
const TOKEN = process.env.PUENTE_TOKEN || "";
let agente = null;               // ws del movil conectado
let seq = 0;
const pendientes = new Map();    // id -> {resolve, timer}

const TOOLS = [
  { name: "abrir_url",     description: "Abre una URL en Chrome del movil", inputSchema: { type: "object", properties: { url: { type: "string" } }, required: ["url"] } },
  { name: "leer_pantalla", description: "Lee el texto visible de la pantalla del movil (accesibilidad)", inputSchema: { type: "object", properties: {} } },
  { name: "escribir",      description: "Escribe texto en el campo enfocado del movil", inputSchema: { type: "object", properties: { texto: { type: "string" } }, required: ["texto"] } },
  { name: "tap",           description: "Toca coordenadas x,y de la pantalla", inputSchema: { type: "object", properties: { x: { type: "number" }, y: { type: "number" } }, required: ["x", "y"] } },
  { name: "atras",         description: "Boton atras del movil", inputSchema: { type: "object", properties: {} } },
];

function alMovil(accion, args) {
  return new Promise((resolve, reject) => {
    if (!agente || agente.readyState !== 1) return reject(new Error("APK_NO_CONECTADA"));
    const id = ++seq;
    const timer = setTimeout(() => { pendientes.delete(id); reject(new Error("TIMEOUT_MOVIL")); }, 30000);
    pendientes.set(id, { resolve, timer });
    agente.send(JSON.stringify({ id, accion, args: args || {} }));
  });
}

function jsonRpc(res, obj) {
  res.writeHead(200, { "content-type": "application/json" });
  res.end(JSON.stringify(obj));
}

const server = http.createServer((req, res) => {
  if (req.url === "/health") return jsonRpc(res, { ok: true, movil: !!agente });
  if (req.url === "/mcp" && req.method === "POST") {
    if (TOKEN && req.headers["authorization"] !== `Bearer ${TOKEN}`) {
      res.writeHead(401); return res.end("unauthorized");
    }
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", async () => {
      let msg;
      try { msg = JSON.parse(body); } catch { return jsonRpc(res, { jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse error" } }); }
      const { id, method, params } = msg;
      try {
        if (method === "initialize")
          return jsonRpc(res, { jsonrpc: "2.0", id, result: { protocolVersion: "2024-11-05", capabilities: { tools: {} }, serverInfo: { name: "swecode-puente-movil", version: "0.1.0" } } });
        if (method === "tools/list")
          return jsonRpc(res, { jsonrpc: "2.0", id, result: { tools: TOOLS } });
        if (method === "tools/call") {
          const r = await alMovil(params.name, params.arguments);
          return jsonRpc(res, { jsonrpc: "2.0", id, result: { content: [{ type: "text", text: typeof r === "string" ? r : JSON.stringify(r) }] } });
        }
        jsonRpc(res, { jsonrpc: "2.0", id, error: { code: -32601, message: "method not found" } });
      } catch (e) {
        jsonRpc(res, { jsonrpc: "2.0", id, error: { code: -32000, message: String(e.message || e) } });
      }
    });
    return;
  }
  res.writeHead(404); res.end();
});

const wss = new WebSocketServer({ server, path: "/agente" });
wss.on("connection", (ws) => {
  if (TOKEN && ws.protocol !== `token-${TOKEN}`) { ws.close(4401, "unauthorized"); return; }
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

server.listen(PORT, () => console.log("puente-movil :" + PORT));
