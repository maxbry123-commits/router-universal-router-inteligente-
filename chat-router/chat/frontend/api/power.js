// api/power.js — Encender / Apagar / Reiniciar el Space del Router desde Vercel (el Router dormido no puede recibir la orden).
// GET -> {stage, hardware}; POST {accion: encender|apagar|reiniciar}. Acceso: X-API-Key = RIU_ROUTER_API_KEY. El token nunca sale de aquí.
const { timingSafeEqual } = require("node:crypto");
const ACCIONES = { encender: "/restart", reiniciar: "/restart", apagar: "/pause" };  // restart es la única forma de despertar un Space en pausa
const urlRouter = () => {
  if (process.env.RIU_ROUTER_URL) return String(process.env.RIU_ROUTER_URL).replace(/\/$/, "");
  const id = process.env.HF_SPACE_ID || "COMAND-CENTER-1/riu-router";
  const partes = String(id).split("/");
  return "https://" + String(partes[0] || "").toLowerCase() + "-" + String(partes[1] || "").toLowerCase() + ".hf.space";
};
const tareasEnCurso = async (clave) => {
  const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), 4000);
  try {
    const r = await fetch(urlRouter() + "/health", { method: "GET", headers: { "X-API-Key": clave }, signal: ctl.signal });
    if (!r.ok) return null;
    const d = JSON.parse(await r.text());
    const n = Number(d && d.tareas_en_curso);
    return Number.isFinite(n) ? n : null;
  } catch (e) { return null; }
  finally { clearTimeout(t); }
};

const igual = (a, b) => typeof a === "string" && typeof b === "string" && a.length === b.length && timingSafeEqual(Buffer.from(a), Buffer.from(b));

module.exports = async (req, res) => {
  const { RIU_ROUTER_API_KEY: clave, HF_POWER_TOKEN, HF_TOKEN_1, HF_SPACE_ID } = process.env;
  const token = HF_POWER_TOKEN || HF_TOKEN_1, base = "https://huggingface.co/api/spaces/" + (HF_SPACE_ID || "COMAND-CENTER-1/riu-router");
  res.setHeader("Cache-Control", "no-store");
  if (!clave || !igual(req.headers["x-api-key"], clave)) return res.status(401).json({ detail: "clave de acceso invalida" });
  if (!token) return res.status(503).json({ detail: "falta HF_TOKEN_1 (o HF_POWER_TOKEN) en Vercel" });
  const accion = req.method === "POST" ? (req.body || {}).accion : "estado";
  if (req.method !== "GET" && !ACCIONES[accion]) return res.status(400).json({ detail: "accion debe ser encender, apagar o reiniciar" });
  if ((accion === "apagar" || accion === "reiniciar") && (req.body || {}).forzar !== true) {
    const n = await tareasEnCurso(clave);
    if (n > 0) return res.status(409).json({ detail: "hay " + n + " tareas en curso" });
  }
  try {
    const r = await fetch(base + (accion === "estado" ? "/runtime" : ACCIONES[accion]), { method: accion === "estado" ? "GET" : "POST", headers: { Authorization: "Bearer " + token } });
    const texto = await r.text();
    let d = {}; try { d = JSON.parse(texto); } catch (e) { d = { detail: texto.slice(0, 300) }; }
    if (!r.ok) return res.status(r.status).json({ detail: String(d.error || d.detail || "Hugging Face HTTP " + r.status).slice(0, 300) });  // 402 = faltan creditos: mensaje tal cual
    const hw = d.hardware || {};
    return res.status(200).json({ accion, stage: d.stage || null, hardware: hw.current || hw.requested || null });
  } catch (e) {
    return res.status(502).json({ detail: "Hugging Face no responde" });
  }
};
