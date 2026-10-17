// ventana-claves.js — banco de claves (tokens, API keys, secretos) conectado al Secret Bank del servidor (/vault/*).
// El valor se envía al servidor y NUNCA vuelve al navegador. "Compartir" = anclar solo el NOMBRE de la referencia al chat, la constitución,
// los workflows o los agentes remotos; el servidor la resuelve. Si el servidor no expone /vault, la ventana lo dice (GAP) y no guarda nada aquí.
import { leer, escribir, KEYS } from "./almacen.js";
import { el, boton, crearVentana, abrirVentana, agregarPill } from "./ventanas-comun.js";
import { plugin } from "./api.js";
const PROV = [["", "Sin proveedor"], ["groq", "Groq"], ["nvidia", "NVIDIA"], ["hf", "Hugging Face"], ["deepseek", "DeepSeek"], ["github", "GitHub"], ["openai", "OpenAI"]];
const REF = /^[a-z0-9][a-z0-9_.-]*\/[a-z0-9][a-z0-9_.-]*$/;
const DEST = [["chat", "Chat"], ["constitucion", "Constitución"], ["workflows", "Workflows"], ["agentes", "Agentes remotos"]];
const base = () => { try { return new URL((window.RIU_CONFIG || {}).harnessUrl).origin; } catch (e) { return ""; } };
async function llamar(metodo, ruta, cuerpo) {
  const b = base(); if (!b) throw new Error("no hay dirección del servidor");
  const h = { "Content-Type": "application/json" }, k = sessionStorage.getItem("riu_clave"); if (k) { h["X-API-Key"] = k; h.Authorization = "Bearer " + k; }
  const r = await fetch(b + ruta, { method: metodo, headers: h, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : "HTTP " + r.status);
  return j;
}
const reg = () => { const v = leer(KEYS.claves, { refs: {} }); if (!v.refs || typeof v.refs !== "object") v.refs = {}; return v; };
export function montarClaves({ root, q, tell }) {
  if (root.dataset.claves) return; root.dataset.claves = "1";
  const { sheet, caja } = crearVentana(root, { id: "ventana-claves", titulo: "Secretos y claves", css: "ventana-claves" });
  agregarPill(q, "pill-claves", "claves ⌄", () => { pintar(); abrirVentana(root, sheet); });  // /vault solo se consulta al abrir "Banco avanzado"
  const cuerpo = el("div", "cl-cuerpo"); caja.append(cuerpo);
  const msg = el("div", "vn-estado"); msg.setAttribute("role", "status");
  async function estado() { try { const s = await llamar("GET", "/vault/status"); msg.textContent = "Banco: " + (s.unlocked ? "abierto" : "cerrado") + (s.credentials != null ? " · " + s.credentials + " credenciales" : ""); } catch (e) { msg.textContent = "Banco no disponible: " + e.message + " (GAP si el servidor no expone /vault)"; } }
  // Secretos del chat (plugin secretos): cifrados en el servidor con la clave del banco, sin contraseña, solo vuelve la máscara
  const secBox = el("div", "cl-sec");
  const secLista = el("div", "cl-sec-lista");
  const sp = async (acc, p) => { const r = await plugin("secretos", acc, p); if (r && r.error) throw new Error(r.error); return r; };
  async function listarSecretos() {
    try {
      const r = await sp("listar"); secLista.replaceChildren();
      if (!(r.secretos || []).length) secLista.append(el("div", "fila-desc", "Todavía no hay secretos guardados."));
      (r.secretos || []).forEach((x) => {
        const f = el("div", "cl-ref"); f.append(el("strong", "", "🔐 " + x.nombre), el("span", "fila-desc", " " + (x.mascara || "••••") + (x.proveedor ? " · " + x.proveedor : "")));
        const bs = el("div", "vn-fila");
        bs.append(boton("Copiar nombre", "mini", () => { try { navigator.clipboard.writeText(x.nombre); } catch (e) {} tell("Nombre copiado: " + x.nombre + " (el valor nunca sale del servidor)"); }),
          boton("Borrar", "mini rojo", async () => { if (!confirm("¿Borrar el secreto " + x.nombre + "?")) return; try { await sp("borrar", { nombre: x.nombre }); tell("Secreto borrado: " + x.nombre); } catch (e) { tell("No se borró: " + e.message); } listarSecretos(); }));
        f.append(bs); secLista.append(f);
      });
    } catch (e) { secLista.replaceChildren(el("div", "fila-desc", "Secretos no disponibles: " + e.message)); }
  }
  function pintarSecretos() {
    secBox.replaceChildren(el("div", "vn-t", "Secretos (API keys y tokens)"));
    const nom = el("input", "vn-in"); nom.placeholder = "nombre (ej. groq-1, github/token)"; nom.autocomplete = "off"; nom.setAttribute("aria-label", "Nombre del secreto");
    const val = el("input", "vn-in"); val.type = "password"; val.placeholder = "valor (token, API key…)"; val.autocomplete = "off"; val.setAttribute("aria-label", "Valor del secreto");
    const prov = el("select", "vn-in"); prov.setAttribute("aria-label", "Proveedor"); PROV.forEach(([v, t]) => { const o = el("option", "", t); o.value = v; prov.append(o); });
    const tok = el("input", "vn-in"); tok.readOnly = true; tok.hidden = true; tok.setAttribute("aria-label", "Token MCP nuevo");
    const fs = el("div", "vn-fila");
    fs.append(boton("Guardar", "mini", async () => {
      const n = nom.value.trim(); if (!/^[A-Za-z0-9][A-Za-z0-9_.\-/]{0,63}$/.test(n)) { tell("Nombre: letras, números, . _ - / (máx. 64)"); return; } if (!val.value) { tell("Falta el valor"); return; }
      try { const r = await sp("guardar", { nombre: n, valor: val.value, proveedor: prov.value }); val.value = ""; nom.value = ""; tell((r.rotado ? "Secreto actualizado: " : "Secreto guardado: ") + n); listarSecretos(); } catch (e) { tell("No se guardó: " + e.message); }
    }), boton("Token MCP nuevo", "mini", async () => {
      if (!confirm("¿Generar un token nuevo para el MCP? El anterior deja de servir.")) return;
      try { const r = await sp("mcp_token_nuevo"); tok.hidden = false; tok.value = r.token || ""; tok.select(); try { await navigator.clipboard.writeText(tok.value); } catch (e) {} tell("Token MCP copiado. Se muestra una sola vez."); listarSecretos(); } catch (e) { tell("No se generó: " + e.message); }
    }));
    secBox.append(nom, val, prov, fs, tok, el("div", "vn-estado", "Se cifra en el servidor y solo vuelve enmascarado. Con proveedor, el Router lo usa en su pool de claves. MCP: POST " + location.origin + "/mcp con Authorization: Bearer <token>."), secLista);
    listarSecretos();
  }
  function pintar() {
    cuerpo.replaceChildren(); pintarSecretos(); cuerpo.append(secBox);
    const av = el("details", "cl-avanzado"); av.append(el("summary", "", "Banco avanzado (/vault, con contraseña maestra)")); cuerpo.append(av); av.addEventListener("toggle", () => { if (av.open) estado(); });
    const cuerpoVault = av;
    cuerpoVault.append(msg);
    const ph = el("input", "vn-in"); ph.type = "password"; ph.autocomplete = "off"; ph.placeholder = "Contraseña maestra (solo abre el banco en el servidor)"; ph.setAttribute("aria-label", "Contraseña maestra");
    const fa = el("div", "vn-fila");
    fa.append(boton("Abrir banco", "mini", async () => { try { await llamar("POST", "/vault/unlock", { passphrase: ph.value }); ph.value = ""; tell("Banco abierto"); } catch (e) { tell("No se abrió: " + e.message); } estado(); }),
      boton("Cerrar banco", "mini", async () => { try { await llamar("POST", "/vault/lock"); tell("Banco cerrado"); } catch (e) { tell(e.message); } estado(); }));
    cuerpoVault.append(ph, fa, el("div", "vn-t", "Guardar o rotar una clave"));
    const ref = el("input", "vn-in"); ref.placeholder = "referencia: grupo/nombre (minúsculas, ej. hf/token)"; ref.setAttribute("aria-label", "Referencia"); ref.autocomplete = "off";
    const sec = el("input", "vn-in"); sec.type = "password"; sec.placeholder = "valor secreto (token, API key…)"; sec.autocomplete = "off"; sec.setAttribute("aria-label", "Valor secreto");
    const valida = () => { if (!REF.test(ref.value.trim())) { tell("La referencia debe ser grupo/nombre en minúsculas, números, punto, guion o guion bajo"); return false; } if (!sec.value) { tell("Falta el valor"); return false; } return true; };
    const anota = (r) => { const v = reg(); v.refs[r] = v.refs[r] || { comparte: { chat: false, constitucion: false, workflows: false, agentes: false }, creada: Date.now() }; escribir(KEYS.claves, v); };
    const fg = el("div", "vn-fila");
    fg.append(boton("Guardar", "mini", async () => { if (!valida()) return; const r = ref.value.trim(); try { await llamar("POST", "/vault/credentials", { ref: r, secret: sec.value, scope: "inference" }); anota(r); sec.value = ""; ref.value = ""; tell("Clave guardada en el banco: " + r); pintar(); estado(); } catch (e) { tell("No se guardó: " + e.message); } }),
      boton("Rotar", "mini", async () => { if (!valida()) return; const r = ref.value.trim(); try { await llamar("POST", "/vault/rotate", { ref: r, secret: sec.value }); anota(r); sec.value = ""; ref.value = ""; tell("Clave rotada: " + r); pintar(); } catch (e) { tell("No se rotó: " + e.message); } }));
    cuerpoVault.append(ref, sec, fg, el("div", "vn-estado", "El valor viaja al servidor y no vuelve al navegador."), el("div", "vn-t", "Compartir con… (solo viaja el nombre de la referencia)"));
    const v = reg(), nombres = Object.keys(v.refs);
    if (!nombres.length) cuerpoVault.append(el("div", "fila-desc", "Las claves que guardes desde aquí aparecerán para compartirlas."));
    nombres.forEach((n) => {
      const f = el("div", "cl-ref"); f.append(el("strong", "", "🔑 " + n));
      const bs = el("div", "vn-fila");
      DEST.forEach(([id, nom]) => { const on = !!(v.refs[n].comparte || {})[id]; const b = boton(nom, "toggle" + (on ? " on" : ""), () => { const x = reg(); x.refs[n].comparte = x.refs[n].comparte || {}; x.refs[n].comparte[id] = !on; escribir(KEYS.claves, x); pintar(); }); b.setAttribute("aria-pressed", String(on)); bs.append(b); });
      bs.append(boton("Olvidar", "mini rojo", () => { if (!confirm("¿Quitar " + n + " de esta lista? (el banco del servidor no se toca)")) return; const x = reg(); delete x.refs[n]; escribir(KEYS.claves, x); pintar(); }));
      f.append(bs); cuerpoVault.append(f);
    });
  }
}
