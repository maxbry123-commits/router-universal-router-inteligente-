// ventana-claves.js — banco de claves (tokens, API keys, secretos) conectado al Secret Bank del servidor (/vault/*).
// El valor se envía al servidor y NUNCA vuelve al navegador. "Compartir" = anclar solo el NOMBRE de la referencia al chat, la constitución,
// los workflows o los agentes remotos; el servidor la resuelve. Si el servidor no expone /vault, la ventana lo dice (GAP) y no guarda nada aquí.
import { leer, escribir, KEYS } from "./almacen.js";
import { guardarConEstado as guardarSwe, estado as estadoSwe } from "./swe-claves.js";
import { el, boton, crearVentana, abrirVentana, agregarPill } from "./ventanas-comun.js";
const PROV_SWE = ["groq", "nvidia"];  // grupos que van al banco del bridge (/web/v1/claves); el resto sigue en /vault
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
  if (q("#pill-claves") && root.querySelector("#ventana-claves")) return;  // ya montada en ESTE DOM (al volver de Configuracion el panel se rehace: se vuelve a montar la pill)
  const { sheet, caja } = crearVentana(root, { id: "ventana-claves", titulo: "Banco de claves", css: "ventana-claves" });
  caja.querySelectorAll(".cl-cuerpo").forEach((n) => n.remove());  // crearVentana es idempotente: un montaje anterior no deja cuerpos duplicados
  agregarPill(q, "pill-claves", "claves ⌄", () => { pintar(); estado(); abrirVentana(root, sheet); });
  const cuerpo = el("div", "cl-cuerpo"); caja.append(cuerpo);
  const msg = el("div", "vn-estado"), msgSwe = el("div", "vn-estado"); msg.setAttribute("role", "status"); msgSwe.setAttribute("role", "status");  // dos lineas: banco Groq/NVIDIA del bridge y banco /vault, sin mezclarlos
  async function estado() {
    msgSwe.textContent = await estadoSwe().catch(() => ""); msgSwe.hidden = !msgSwe.textContent;
    try { const s = await llamar("GET", "/vault/status"); msg.textContent = "Banco: " + (s.unlocked ? "abierto" : "cerrado") + (s.credentials != null ? " · " + s.credentials + " credenciales" : ""); }
    catch (e) { msg.textContent = "Banco no disponible: " + e.message + " (GAP si el servidor no expone /vault)"; }
  }
  const hayCompartibles = () => true;
  function pintar() {
    cuerpo.replaceChildren(); cuerpo.append(msgSwe, msg);
    const ph = el("input", "vn-in"); ph.type = "password"; ph.autocomplete = "off"; ph.placeholder = "Contraseña maestra (solo abre el banco en el servidor)"; ph.setAttribute("aria-label", "Contraseña maestra");
    const fa = el("div", "vn-fila");
    fa.append(boton("Abrir banco", "mini", async () => { try { await llamar("POST", "/vault/unlock", { passphrase: ph.value }); ph.value = ""; tell("Banco abierto"); } catch (e) { tell("No se abrió: " + e.message); } estado(); }),
      boton("Cerrar banco", "mini", async () => { try { await llamar("POST", "/vault/lock"); tell("Banco cerrado"); } catch (e) { tell(e.message); } estado(); }));
    cuerpo.append(ph, fa, el("div", "vn-t", "Guardar o rotar una clave"));
    const ref = el("input", "vn-in"); ref.placeholder = "referencia: grupo/nombre (minúsculas, ej. hf/token)"; ref.setAttribute("aria-label", "Referencia"); ref.autocomplete = "off";
    const sec = el("input", "vn-in"); sec.type = "password"; sec.placeholder = "valor secreto (token, API key…)"; sec.autocomplete = "off"; sec.setAttribute("aria-label", "Valor secreto");
    const valida = () => { if (!REF.test(ref.value.trim())) { tell("La referencia debe ser grupo/nombre en minúsculas, números, punto, guion o guion bajo"); return false; } if (!sec.value) { tell("Falta el valor"); return false; } return true; };
    const anota = (r) => { const v = reg(); v.refs[r] = v.refs[r] || { comparte: { chat: false, constitucion: false, workflows: false, agentes: false }, creada: Date.now() }; escribir(KEYS.claves, v); };
    const fg = el("div", "vn-fila");
    fg.append(boton("Guardar", "mini", async () => { if (!valida()) return; const r = ref.value.trim(); const g = r.split("/")[0]; if (PROV_SWE.includes(g)) { const x = await guardarSwe({ [g]: sec.value }); tell(x.texto); if (x.ok) { sec.value = ""; ref.value = ""; pintar(); estado(); } return; }  // groq/ y nvidia/ viven en el banco del bridge: no se comparten por nombre, y el valor solo se vacia si se guardo try { await llamar("POST", "/vault/credentials", { ref: r, secret: sec.value, scope: "inference" }); anota(r); sec.value = ""; ref.value = ""; tell("Clave guardada en el banco: " + r); pintar(); estado(); } catch (e) { tell("No se guardó: " + e.message); } }),
      boton("Rotar", "mini", async () => { if (!valida()) return; const r = ref.value.trim(); const g = r.split("/")[0]; if (PROV_SWE.includes(g)) { const x = await guardarSwe({ [g]: sec.value }); tell(x.texto); if (x.ok) { sec.value = ""; ref.value = ""; pintar(); estado(); } return; }  // groq/ y nvidia/ viven en el banco del bridge: no se comparten por nombre, y el valor solo se vacia si se guardo try { await llamar("POST", "/vault/rotate", { ref: r, secret: sec.value }); anota(r); sec.value = ""; ref.value = ""; tell("Clave rotada: " + r); pintar(); } catch (e) { tell("No se rotó: " + e.message); } }));
    cuerpo.append(ref, sec, fg, el("div", "vn-estado", "El valor viaja al servidor y no vuelve al navegador. Con grupo groq/ o nvidia/ va al banco cifrado del bridge y reemplaza las claves de ese proveedor."), hayCompartibles() ? el("div", "vn-t", "Compartir con… (solo viaja el nombre de la referencia)") : el("div", "fila-desc", "Las claves groq/ y nvidia/ no se comparten por nombre: SWE CODE y los selectores Groq/NVIDIA las usan solos."));
    const v = reg(), nombres = Object.keys(v.refs).filter((n) => !PROV_SWE.includes(n.split("/")[0]));  // «Compartir con…» no aplica a groq/ ni nvidia/
    if (!nombres.length) cuerpo.append(el("div", "fila-desc", "Las claves que guardes desde aquí aparecerán para compartirlas."));
    nombres.forEach((n) => {
      const f = el("div", "cl-ref"); f.append(el("strong", "", "🔑 " + n));
      const bs = el("div", "vn-fila");
      DEST.forEach(([id, nom]) => { const on = !!(v.refs[n].comparte || {})[id]; const b = boton(nom, "toggle" + (on ? " on" : ""), () => { const x = reg(); x.refs[n].comparte = x.refs[n].comparte || {}; x.refs[n].comparte[id] = !on; escribir(KEYS.claves, x); pintar(); }); b.setAttribute("aria-pressed", String(on)); bs.append(b); });
      bs.append(boton("Olvidar", "mini rojo", () => { if (!confirm("¿Quitar " + n + " de esta lista? (el banco del servidor no se toca)")) return; const x = reg(); delete x.refs[n]; escribir(KEYS.claves, x); pintar(); }));
      f.append(bs); cuerpo.append(f);
    });
  }
}
