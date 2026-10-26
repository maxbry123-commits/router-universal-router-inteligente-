// ventana-mcp.js — pruebas HTTP y MCP del Router. La clave sale de la sesión, no del código.
import { el, btn, ventana } from "./ventanas-control.js";

function base() {
  const u = (window.RIU_CONFIG && window.RIU_CONFIG.proxyDestino) || "";
  return String(u).replace(/\/$/, "") || "https://comand-center-1-riu-router.hf.space";
}
function clave() { return sessionStorage.getItem("riu_clave") || ""; }

async function pedir(ruta, cuerpo) {
  const k = clave();
  if (ruta !== "/health" && !k) throw new Error("falta la clave de este chat");
  const h = { "Content-Type": "application/json" };
  if (k) { h["X-API-Key"] = k; h.Authorization = "Bearer " + k; }
  const r = await fetch(base() + ruta, { method: cuerpo ? "POST" : "GET", headers: h, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  const t = await r.text();
  let j = null;
  try { j = JSON.parse(t); } catch (e) {}
  if (!r.ok) throw new Error((j && (j.detail || j.error)) || ("HTTP " + r.status));
  return j || t;
}

function pintar(cuerpo) {
  const aviso = el("div", "mcp-out", "Sin prueba");
  const correr = async (b, fn) => {
    b.disabled = true;
    aviso.textContent = "probando…";
    try { aviso.textContent = await fn(); } catch (e) { aviso.textContent = e.message; } finally { b.disabled = false; }
  };
  const salud = btn("Salud", "secondary", () => correr(salud, async () => {
    const j = await pedir("/health");
    return "salud " + (j.status || "?") + " · " + (j.commit || "sin commit");
  }));
  const prov = btn("Proveedores", "secondary", () => correr(prov, async () => {
    const j = await pedir("/chat/providers");
    const lista = Array.isArray(j) ? j : (j.providers || j.proveedores || []);
    const nombres = lista.map((p) => (typeof p === "string" ? p : p.id || p.name || p.nombre)).filter(Boolean);
    return "proveedores " + (nombres.length ? nombres.join(", ") : "ninguno");
  }));
  const mcp = btn("MCP", "secondary", () => correr(mcp, async () => {
    const j = await pedir("/mcp", { jsonrpc: "2.0", id: 1, method: "tools/list" });
    const tools = (j.result && j.result.tools) || [];
    return "MCP " + tools.length + " · " + tools.map((t) => t.name).join(", ");
  }));
  const fila = el("div", "cv-form");
  fila.append(salud, prov, mcp);
  cuerpo.replaceChildren(el("div", "cv-sec", "MCP y HTTP"), fila, el("div", "fila-desc", "Llama al Router de este chat. No envía un mensaje al modelo."), aviso);
}

const montar = () => ventana("mcp", "MCP y HTTP", pintar);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
