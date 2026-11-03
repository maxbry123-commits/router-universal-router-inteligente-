// ventana-claves.js — banco de claves (tokens, API keys, secretos) conectado al Secret Bank del servidor (/vault/*).
// El valor se envía al servidor y NUNCA vuelve al navegador. "Compartir" = anclar solo el NOMBRE de la referencia al chat, la constitución,
// los workflows o los agentes remotos; el servidor la resuelve. Si el servidor no expone /vault, la ventana lo dice (GAP) y no guarda nada aquí.
import { leer, escribir, KEYS } from "./almacen.js";
import { api } from "./api.js";
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
  // Misma ventana/banco existente: si un agente reporta credencial ausente,
  // abrirla con la referencia preparada; el secreto solo va al servidor.
  const abrir = (proveedor = "") => {
    pintar(); estado(); abrirVentana(root, sheet);
    if (proveedor === "github" || proveedor === "hf") {
      const ref = sheet.querySelector('input[aria-label="Referencia"]');
      const secreto = sheet.querySelector('input[aria-label="Valor secreto"]');
      if (ref) ref.value = proveedor === "github" ? "github/token" : "hf/token";
      if (secreto) secreto.focus();
    }
  };
  agregarPill(q, "pill-claves", "claves ⌄", () => abrir());
  window.RIU_BANCO_CLAVES = { abrir }; // el + API/SDK usa ESTA MISMA ventana de Configuración
  const cuerpo = el("div", "cl-cuerpo"); caja.append(cuerpo);
  const msg = el("div", "vn-estado"), msgSwe = el("div", "vn-estado"); msg.setAttribute("role", "status"); msgSwe.setAttribute("role", "status");  // dos lineas: banco Groq/NVIDIA del bridge y banco /vault, sin mezclarlos
  async function estado() {
    msgSwe.textContent = await estadoSwe().catch(() => "Sin verificar");
    msgSwe.hidden = !msgSwe.textContent;
    try {
      const s = await api("/plugins/deepseek_harness/credenciales/catalogo", { method:"POST", body:{} });
      const lista = s?.result?.proveedores || [];
      msg.textContent = "Banco cifrado compartido: " + lista.map(x => x.id + " · " + x.cantidad).join(" | ");
    } catch { msg.textContent = "Banco compartido sin verificar. Puedes intentar añadir una clave."; }
  }
  function pintar() {
    cuerpo.replaceChildren(); cuerpo.append(msgSwe, msg);
    // Alta aditiva: no reemplaza las claves ya guardadas del proveedor.
    // Harness HTTP autenticado -> plugin banco_proveedores Router MVP -> bridge SWE -> banco cifrado existente.
    const filaApi = el("div", "cl-api-plus"), grupo = el("select", "vn-in");
    for (const [v, t] of [["auto", "Detectar por prefijo"], ["groq", "Groq"], ["nvidia", "NVIDIA"], ["deepseek", "DeepSeek (API / SDK)"], ["minimax", "MiniMax (API / SDK)"], ["openai", "OpenAI (API / SDK)"], ["sdk", "Otro proveedor / SDK"]]) {
      const opt = el("option", "", t); opt.value = v; grupo.append(opt);
    }
    grupo.setAttribute("aria-label", "Proveedor de API key o SDK");
    const personalizado = el("input", "vn-in"); personalizado.placeholder = "Identificador del proveedor (ej. mi-sdk)";
    personalizado.setAttribute("aria-label", "Identificador SDK"); personalizado.autocomplete = "off"; personalizado.hidden = true;
    grupo.addEventListener("change", () => { personalizado.hidden = grupo.value !== "sdk"; });
    const secreta = el("input", "vn-in"); secreta.type = "password"; secreta.autocomplete = "off";
    secreta.placeholder = "Pega API key o token SDK · no se almacena en el navegador";
    secreta.setAttribute("aria-label", "API key o token SDK");
    const aviso = el("div", "vn-estado"); aviso.setAttribute("role", "status");
    const guardarNueva = boton("+ Añadir API / SDK", "mini", async () => {
      const prov = grupo.value === "sdk" ? personalizado.value.trim().toLowerCase() : grupo.value;
      if (!/^(auto|[a-z][a-z0-9_-]{1,31})$/.test(prov) || secreta.value.length < 8 || secreta.value.length > 300) {
        aviso.textContent = "Revisa proveedor y token (8–300 caracteres)."; return;
      }
      guardarNueva.disabled = true; aviso.textContent = "Guardando en el banco cifrado…";
      try {
        const r = await api("/plugins/deepseek_harness/credenciales/anadir", { method: "POST",
          body: { proveedor: prov, tipo: grupo.value === "sdk" ? "sdk" : "api_key", secret: secreta.value } });
        if (r?.status !== "ok" || r.result?.ok !== true) throw new Error("No se confirmó la escritura.");
        secreta.value = ""; aviso.textContent = r.result.proveedor + ": " + r.result.cantidad +
          " clave(s) cifrada(s)" + (r.result.persistido ? " · respaldo actualizado" : " · respaldo sin confirmar") +
          (r.result.compatible ? " · conectado a Router y SWE CODE" : " · SDK registrado (requiere adaptador para inferencia)");
        estado(); window.RIU_FICHAS?.recargar?.().catch(() => {});
      } catch (e) { aviso.textContent = "No se guardó: " + (e?.status === 401 ? "clave de acceso inválida" : "banco no disponible"); }
      finally { guardarNueva.disabled = false; }
    });
    filaApi.append(el("div", "vn-t", "Conectar proveedor · API key / SDK"), grupo, personalizado,
      secreta, guardarNueva, aviso, el("div", "fila-desc", "Groq y NVIDIA se reconocen por prefijo. Para DeepSeek, MiniMax y OpenAI selecciona el proveedor (sus claves no se distinguen de forma fiable). APIs compatibles se usan desde ambos chats; otros SDK necesitan adaptador."));
    cuerpo.append(filaApi);
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
    fg.append(boton("Guardar", "mini", async () => { if (!valida()) return; const r = ref.value.trim(); const g = r.split("/")[0]; if (PROV_SWE.includes(g)) { const x = await guardarSwe({ [g]: sec.value }); tell(x.texto); if (x.ok) { sec.value = ""; ref.value = ""; pintar(); estado(); } return; } /* groq/ y nvidia/ viven en el banco del bridge: no se comparten por nombre, y el valor solo se vacia si se guardo */ try { await llamar("POST", "/vault/credentials", { ref: r, secret: sec.value, scope: "inference" }); anota(r); sec.value = ""; ref.value = ""; tell("Clave guardada en el banco: " + r); pintar(); estado(); } catch (e) { tell("No se guardó: " + e.message); } }),
      boton("Rotar", "mini", async () => { if (!valida()) return; const r = ref.value.trim(); const g = r.split("/")[0]; if (PROV_SWE.includes(g)) { const x = await guardarSwe({ [g]: sec.value }); tell(x.texto); if (x.ok) { sec.value = ""; ref.value = ""; pintar(); estado(); } return; } /* groq/ y nvidia/ viven en el banco del bridge: no se comparten por nombre, y el valor solo se vacia si se guardo */ try { await llamar("POST", "/vault/rotate", { ref: r, secret: sec.value }); anota(r); sec.value = ""; ref.value = ""; tell("Clave rotada: " + r); pintar(); } catch (e) { tell("No se rotó: " + e.message); } }));
    cuerpo.append(ref, sec, fg, el("div", "vn-estado", "El valor viaja al servidor y no vuelve al navegador. Con grupo groq/ o nvidia/ va al banco cifrado del bridge y reemplaza las claves de ese proveedor."), el("div", "vn-t", "Compartir con… (solo viaja el nombre de la referencia; no aplica a groq/ ni nvidia/)"));
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
