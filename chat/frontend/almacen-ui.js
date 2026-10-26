// Almacen local del chat y puerta a la tool/plugin del Router (almacen + memoria).
import { KEYS } from "./almacen.js";

const CAJA = "riu_caja_v1";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const btn = (txt, fn) => { const b = el("button", "secondary", txt); b.type = "button"; b.onclick = fn; return b; };
const campo = (aria, ph) => { const i = el("input"); i.placeholder = ph; i.setAttribute("aria-label", aria); i.style.cssText = "flex:1 1 120px;min-width:0;min-height:32px"; return i; };

function caja() { try { const v = JSON.parse(localStorage.getItem(CAJA) || "{}"); return v && typeof v === "object" ? v : {}; } catch (e) { return {}; } }
function poner(mapa) { localStorage.setItem(CAJA, JSON.stringify(mapa)); try { window.dispatchEvent(new CustomEvent("riu:almacen", { detail: CAJA })); } catch (e) {} }

async function http(url, opt) {
  const h = { ...(opt && opt.headers) };
  const k = sessionStorage.getItem("riu_clave");
  if (k) h["X-API-Key"] = k;
  if (opt && opt.body) h["Content-Type"] = "application/json";
  const r = await fetch(url, { method: opt && opt.method || "POST", headers: h, body: opt && opt.body });
  const p = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(p.detail || p.error || ("HTTP " + r.status));
  return p;
}

async function tool(nombre, arguments_) {
  const p = await http("/mcp", { body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: nombre, arguments: arguments_ } }) });
  if (p.error) throw new Error(p.error.message || "tool");
  return (p.result && p.result.structuredContent) || p.result || p;
}

const local = {
  listar() { return caja(); },
  leer(nombre) { return caja()[nombre]; },
  guardar(nombre, valor) { const m = caja(); m[nombre] = valor; poner(m); return true; },
  quitar(nombre) { const m = caja(); delete m[nombre]; poner(m); return true; },
};
async function hf(accion, nombre, valor) {
  try { return await tool("almacen", { accion, destino: "hf", nombre, valor }); }
  catch (e) {
    if (!/no disponible|404/.test(e.message)) throw e;
    return http("/almacen", { body: JSON.stringify({ accion, destino: "hf", nombre, valor }) });
  }
}
async function memoria(accion, cuerpo) {
  try { return await tool("memoria", { accion, ...cuerpo }); }
  catch (e) {
    if (accion === "save") return http("/memoria/save", { body: JSON.stringify(cuerpo) });
    const q = new URLSearchParams({ scope: cuerpo.scope || "", key: cuerpo.key || "", query: cuerpo.query || "" });
    return http("/memoria/" + (accion === "search" ? "search" : "load") + "?" + q, { method: "GET" });
  }
}
window.RIU_ALMACEN = { local, hf, memoria, tool };

function instalar() {
  const temas = document.querySelector("#ap-temas");
  if (!temas || document.querySelector("#cfg-almacen")) return;
  const sec = el("section", "ap-sec"); sec.id = "cfg-almacen";
  sec.append(el("h2", "", "Almacenamiento y memoria"));
  const est = el("div", "muted", "Tool MCP almacen y memoria. Local queda en este dispositivo.");
  const nom = campo("Nombre", "nombre");
  const val = el("textarea"); val.rows = 2; val.placeholder = "valor"; val.setAttribute("aria-label", "Valor"); val.style.width = "100%";
  const lista = el("div", "list");
  const pintar = () => {
    const m = caja();
    const claves = Object.keys(m);
    lista.replaceChildren(...(claves.length ? claves : ["(vacío)"]).map((k) => el("div", "item", k === "(vacío)" ? k : k + " · " + String(m[k]).slice(0, 80))));
  };
  const decir = (t) => { est.textContent = typeof t === "string" ? t : JSON.stringify(t).slice(0, 180); };
  const fila = el("div", "row");
  fila.append(
    btn("Guardar local", () => { if (!nom.value.trim()) return decir("falta nombre"); local.guardar(nom.value.trim(), val.value); pintar(); decir("guardado en este dispositivo"); }),
    btn("Leer local", () => { const v = local.leer(nom.value.trim()); val.value = v == null ? "" : String(v); decir(v == null ? "no está" : "leído"); }),
    btn("Quitar", () => { local.quitar(nom.value.trim()); pintar(); decir("quitado"); }),
    btn("Guardar HF", async () => { try { decir(await hf("guardar", nom.value.trim(), val.value)); } catch (e) { decir(e.message); } }),
    btn("Leer HF", async () => { try { const r = await hf("leer", nom.value.trim()); val.value = r.valor || ""; decir(r); } catch (e) { decir(e.message); } }),
  );
  const scope = campo("Scope", "scope"); scope.value = "chat";
  const key = campo("Clave de memoria", "key");
  const memFila = el("div", "row");
  memFila.append(
    btn("Guardar memoria", async () => { try { decir(await memoria("save", { scope: scope.value.trim(), key: key.value.trim(), data: val.value })); } catch (e) { decir(e.message); } }),
    btn("Cargar memoria", async () => { try { const r = await memoria("load", { scope: scope.value.trim(), key: key.value.trim() }); const rec = (r.records || [])[0]; val.value = rec ? JSON.stringify(rec.data) : ""; decir(rec ? "cargada" : "sin registros"); } catch (e) { decir(e.message); } }),
  );
  const conocidas = el("div", "muted", "Claves del chat: " + Object.values(KEYS).join(", "));
  sec.append(est, nom, val, fila, lista, el("h2", "", "Memoria del chat"), scope, key, memFila, conocidas);
  temas.closest("section").before(sec);
  pintar();
}
const revisar = () => { try { instalar(); } catch (e) { console.warn("almacen-ui", e); } };
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
