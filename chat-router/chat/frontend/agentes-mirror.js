// agentes-mirror.js — Selector de agentes mirror (Hermes/OpenClaw/ClaudeCode/Codex) + selector del modelo/ficha
// que usa el motor de ese agente. Llama a mirror_listar / mirror_configurar por POST vía api.js (accion).
// Regla del proyecto: 1 panel = 1 módulo = 1 scope. Este archivo solo monta y gestiona los selectores mirror.
import { accion } from "./api.js";

const MOUNT_ID = "mirror-selector-mount";
const CLAVE_SEL = "riu_mirror_agente";
const CLAVE_MOD = "riu_mirror_modelo";

// Solo el backend enumera espejos y modelos: NO publicar agentes simulados.
const sesionActual = () => { try { return window.RIU_CHAT?.chat?.()?.sesion || "web-general"; } catch { return "web-general"; } };

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

async function cargarListado(sesion) {
  try {
    const r = await accion("mirror_listar", { sesion, rapido: true });
    if (r?.ok !== true || !Array.isArray(r.agentes) || !Array.isArray(r.modelos)) throw new Error("CATALOGO_MIRROR_INVALIDO");
    return {
      agentes: r.agentes.filter(a => a && typeof a.id === "string" && typeof a.tipo === "string"),
      modelos: r.modelos.filter(m => m && typeof m.id === "string"),
      conectado: true, error: "",
    };
  } catch {
    // Fallo cerrado: un espejo virtual no es un agente ejecutable.
    return { agentes: [], modelos: [], conectado: false, error: "SIN VERIFICAR · el Router no respondió" };
  }
}
async function configurar(agenteId, modeloId, sesion) {
  if (!agenteId) return { ok: false, error: "Selecciona un espejo" };
  try {
    const r = await accion("mirror_configurar", { sesion, agente: agenteId, modelo: modeloId || "" });
    return r?.ok === true ? r : { ok: false, error: r?.error || "CONFIRMACION_AUSENTE" };
  } catch (e) {
    return { ok: false, error: e.message || "ERROR_CONEXION" };
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

  const sesion = sesionActual();
  const datos = await cargarListado(sesion);
  caja.replaceChildren();

  const wrap = el("div", "row fields mirror-row");
  const lblAg = el("label", "", "Espejo LOOP ");
  const selAg = document.createElement("select");
  selAg.id = "mirror-agente";
  selAg.setAttribute("aria-label", "Agente mirror");
  poblarSelect(selAg, datos.agentes, datos.conectado ? leerSel(CLAVE_SEL + ":" + sesion) : "", "Sin espejo", "tipo");

  const lblMod = el("label", "", "Modelo/Ficha ");
  const selMod = document.createElement("select");
  selMod.id = "mirror-modelo";
  selMod.setAttribute("aria-label", "Modelo o ficha del agente mirror");
  poblarSelect(selMod, datos.modelos, datos.conectado ? leerSel(CLAVE_MOD + ":" + sesion) : "", "Modelo por defecto", "grupo");

  const estado = el("span", "mirror-estado muted", datos.conectado ? "Espejos virtuales · no certifica instalación" : datos.error);
  selAg.disabled = !datos.conectado || !datos.agentes.length;
  selMod.disabled = !datos.conectado || !datos.modelos.length;

  wrap.append(lblAg, selAg, lblMod, selMod, estado);
  caja.append(wrap);

  const aplicar = async () => {
    const ag = selAg.value;
    const mod = selMod.value;
    if (!datos.conectado) return;
    estado.textContent = "Guardando…";
    estado.classList.remove("error");
    const r = await configurar(ag, mod, sesion);
    if (r?.ok === true) {
      guardarSel(CLAVE_SEL + ":" + sesion, ag);
      guardarSel(CLAVE_MOD + ":" + sesion, mod);
      estado.textContent = "Configuración confirmada · ejecución sin verificar";
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
    get conectado() { return datos.conectado; },
    get disponible() { return false; }, // mirror_listar no verifica instalación/ejecución real
  };
}
