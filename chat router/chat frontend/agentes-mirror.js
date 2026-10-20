// agentes-mirror.js — Selector de agentes mirror (Hermes/OpenClaw/ClaudeCode/Codex) + selector del modelo/ficha
// que usa el motor de ese agente. Llama a mirror_listar / mirror_configurar por POST vía api.js (accion).
// Regla del proyecto: 1 panel = 1 módulo = 1 scope. Este archivo solo monta y gestiona los selectores mirror.
import { accion } from "./api.js";

const MOUNT_ID = "mirror-selector-mount";
const CLAVE_SEL = "riu_mirror_agente";
const CLAVE_MOD = "riu_mirror_modelo";

const AGENTES_FALLBACK = [
  { id: "hermes-01", tipo: "Hermes", nombre: "Hermes 01" },
  { id: "hermes-02", tipo: "Hermes", nombre: "Hermes 02" },
  { id: "hermes-03", tipo: "Hermes", nombre: "Hermes 03" },
  { id: "hermes-04", tipo: "Hermes", nombre: "Hermes 04" },
  { id: "hermes-05", tipo: "Hermes", nombre: "Hermes 05" },
  { id: "hermes-06", tipo: "Hermes", nombre: "Hermes 06" },
  { id: "hermes-07", tipo: "Hermes", nombre: "Hermes 07" },
  { id: "hermes-08", tipo: "Hermes", nombre: "Hermes 08" },
  { id: "hermes-09", tipo: "Hermes", nombre: "Hermes 09" },
  { id: "hermes-10", tipo: "Hermes", nombre: "Hermes 10" },
  { id: "openclaw-01", tipo: "OpenClaw", nombre: "OpenClaw 01" },
  { id: "openclaw-02", tipo: "OpenClaw", nombre: "OpenClaw 02" },
  { id: "openclaw-03", tipo: "OpenClaw", nombre: "OpenClaw 03" },
  { id: "openclaw-04", tipo: "OpenClaw", nombre: "OpenClaw 04" },
  { id: "openclaw-05", tipo: "OpenClaw", nombre: "OpenClaw 05" },
  { id: "openclaw-06", tipo: "OpenClaw", nombre: "OpenClaw 06" },
  { id: "openclaw-07", tipo: "OpenClaw", nombre: "OpenClaw 07" },
  { id: "openclaw-08", tipo: "OpenClaw", nombre: "OpenClaw 08" },
  { id: "openclaw-09", tipo: "OpenClaw", nombre: "OpenClaw 09" },
  { id: "openclaw-10", tipo: "OpenClaw", nombre: "OpenClaw 10" },
  { id: "claudecode-01", tipo: "ClaudeCode", nombre: "ClaudeCode 01" },
  { id: "claudecode-02", tipo: "ClaudeCode", nombre: "ClaudeCode 02" },
  { id: "claudecode-03", tipo: "ClaudeCode", nombre: "ClaudeCode 03" },
  { id: "claudecode-04", tipo: "ClaudeCode", nombre: "ClaudeCode 04" },
  { id: "claudecode-05", tipo: "ClaudeCode", nombre: "ClaudeCode 05" },
  { id: "claudecode-06", tipo: "ClaudeCode", nombre: "ClaudeCode 06" },
  { id: "claudecode-07", tipo: "ClaudeCode", nombre: "ClaudeCode 07" },
  { id: "claudecode-08", tipo: "ClaudeCode", nombre: "ClaudeCode 08" },
  { id: "claudecode-09", tipo: "ClaudeCode", nombre: "ClaudeCode 09" },
  { id: "claudecode-10", tipo: "ClaudeCode", nombre: "ClaudeCode 10" },
  { id: "codex-01", tipo: "Codex", nombre: "Codex 01" },
  { id: "codex-02", tipo: "Codex", nombre: "Codex 02" },
  { id: "codex-03", tipo: "Codex", nombre: "Codex 03" },
  { id: "codex-04", tipo: "Codex", nombre: "Codex 04" },
  { id: "codex-05", tipo: "Codex", nombre: "Codex 05" },
  { id: "codex-06", tipo: "Codex", nombre: "Codex 06" },
  { id: "codex-07", tipo: "Codex", nombre: "Codex 07" },
  { id: "codex-08", tipo: "Codex", nombre: "Codex 08" },
  { id: "codex-09", tipo: "Codex", nombre: "Codex 09" },
  { id: "codex-10", tipo: "Codex", nombre: "Codex 10" },
];

const MODELOS_FALLBACK = [
  { id: "ficha4:qwen38max", grupo: "Ficha 4", nombre: "Qwen 3.8 Max" },
  { id: "ficha4:qwen38flash", grupo: "Ficha 4", nombre: "Qwen 3.8 Flash" },
  { id: "ficha4:qwen37max", grupo: "Ficha 4", nombre: "Qwen 3.7 Max" },
  { id: "ficha4:qwen37flash", grupo: "Ficha 4", nombre: "Qwen 3.7 Flash" },
  { id: "ficha4:dsv4pro", grupo: "Ficha 4", nombre: "DeepSeek V4 Pro" },
  { id: "ficha4:dsv4flash", grupo: "Ficha 4", nombre: "DeepSeek V4 Flash" },
  { id: "ficha4:glm52", grupo: "Ficha 4", nombre: "GLM 5.2" },
  { id: "ficha5:qwen38max", grupo: "Ficha 5", nombre: "Qwen 3.8 Max" },
  { id: "ficha5:qwen38flash", grupo: "Ficha 5", nombre: "Qwen 3.8 Flash" },
  { id: "ficha5:dsv4flash", grupo: "Ficha 5", nombre: "DeepSeek V4 Flash" },
  { id: "nvcode:z-ai/glm-5.3", grupo: "NVIDIA", nombre: "GLM 5.3" },
  { id: "nvcode:stepfun-ai/step-5-preview", grupo: "NVIDIA", nombre: "Step 5 Preview" },
  { id: "nvcode:deepseek-ai/deepseek-v4.1-flash", grupo: "NVIDIA", nombre: "DeepSeek V4.1 Flash" },
  { id: "groq:openai/gpt-oss-120b", grupo: "Groq", nombre: "GPT OSS 120B" },
  { id: "groq:llama-3.3-70b-versatile", grupo: "Groq", nombre: "Llama 3.3 70B" },
  { id: "groq:llama-3.1-8b-instant", grupo: "Groq", nombre: "Llama 3.1 8B" },
];

const el = (tag, cls, txt) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
};

const leerSel = (k) => { try { return sessionStorage.getItem(k) || ""; } catch (_) { return ""; } };
const guardarSel = (k, v) => { try { if (v) sessionStorage.setItem(k, v); else sessionStorage.removeItem(k); } catch (_) {} };

function poblarSelect(sel, items, valorActual, placeholder, grupoKey) {
  sel.replaceChildren();
  if (placeholder) {
    const o = document.createElement("option");
    o.value = "";
    o.textContent = placeholder;
    sel.append(o);
  }
  const grupos = {};
  items.forEach((it) => {
    const g = grupoKey ? it[grupoKey] || "Otros" : "Otros";
    (grupos[g] = grupos[g] || []).push(it);
  });
  Object.entries(grupos).forEach(([g, lista]) => {
    const og = document.createElement("optgroup");
    og.label = g;
    lista.forEach((it) => {
      const o = document.createElement("option");
      o.value = it.id;
      o.textContent = it.nombre || it.id;
      og.append(o);
    });
    sel.append(og);
  });
  if (valorActual) sel.value = valorActual;
}

async function cargarListado() {
  try {
    const r = await accion("mirror_listar", { rapido: true });
    if (r && Array.isArray(r.agentes) && r.agentes.length) {
      return {
        agentes: r.agentes,
        modelos: Array.isArray(r.modelos) && r.modelos.length ? r.modelos : MODELOS_FALLBACK,
        simulado: false,
      };
    }
  } catch (_) {}
  return { agentes: AGENTES_FALLBACK, modelos: MODELOS_FALLBACK, simulado: true };
}

async function configurar(agenteId, modeloId) {
  try {
    const r = await accion("mirror_configurar", { agente: agenteId || "", modelo: modeloId || "" });
    if (r && r.error) throw new Error(r.error);
    return r || { ok: true };
  } catch (e) {
    return { ok: false, error: e.message || String(e) };
  }
}

export async function mountMirrorSelectors(root) {
  if (!root) return;
  let caja = root.querySelector("#" + MOUNT_ID);
  if (!caja) {
    caja = el("div", "mirror-selectores");
    caja.id = MOUNT_ID;
    // Insertar debajo de los selectores existentes (#mode-selector-mount) si existe; si no, al final del root
    const ref = root.querySelector("#mode-selector-mount");
    if (ref && ref.parentNode === root) ref.insertAdjacentElement("afterend", caja);
    else root.append(caja);
  }
  caja.replaceChildren(el("div", "muted", "Cargando mirrors…"));

  const datos = await cargarListado();
  caja.replaceChildren();

  const wrap = el("div", "row fields mirror-row");
  const lblAg = el("label", "", "Agente mirror ");
  const selAg = document.createElement("select");
  selAg.id = "mirror-agente";
  selAg.setAttribute("aria-label", "Agente mirror");
  poblarSelect(selAg, datos.agentes, leerSel(CLAVE_SEL), "Sin agente mirror", "tipo");

  const lblMod = el("label", "", "Modelo/Ficha ");
  const selMod = document.createElement("select");
  selMod.id = "mirror-modelo";
  selMod.setAttribute("aria-label", "Modelo o ficha del agente mirror");
  poblarSelect(selMod, datos.modelos, leerSel(CLAVE_MOD), "Modelo por defecto", "grupo");

  const estado = el("span", "mirror-estado muted", datos.simulado ? "SIMULADO · backend sin mirror_listar" : "");

  wrap.append(lblAg, selAg, lblMod, selMod, estado);
  caja.append(wrap);

  const aplicar = async () => {
    const ag = selAg.value;
    const mod = selMod.value;
    guardarSel(CLAVE_SEL, ag);
    guardarSel(CLAVE_MOD, mod);
    estado.textContent = "Guardando…";
    estado.classList.remove("error");
    const r = await configurar(ag, mod);
    if (r && r.ok !== false) {
      estado.textContent = datos.simulado ? "SIMULADO · guardado local" : "Configurado ✓";
    } else {
      estado.textContent = "Error: " + (r.error || "desconocido");
      estado.classList.add("error");
    }
  };

  selAg.addEventListener("change", aplicar);
  selMod.addEventListener("change", aplicar);

  // Exponer estado mínimo para otros paneles (solo lectura)
  window.RIU_MIRROR = {
    get agente() { return selAg.value; },
    get modelo() { return selMod.value; },
    get simulado() { return datos.simulado; },
  };
}
