// ventana-agentes.js — VENTANA AGENTES del chat.
//
// El Router expone el registro canonico en GET /v1/agents ("el chat los lee de
// aqui, no hardcodeados") y el interruptor real ON/OFF en
// POST /v1/agents/<id>/state {"enabled":bool}. Si un agente esta OFF, el propio
// Router responde 409: "agente X esta OFF ... enciendelo en /v1/agents/X/state
// o en la ventana AGENTES del chat" — esta ventana es esa.
//
// El token del Router NUNCA llega al navegador: todo pasa por la funcion
// serverless /api/control (que lo tiene en el servidor).

const HOJA = "sh-agentes";

async function _control(datos) {
  const r = await fetch("/api/control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });
  return await r.json().catch(() => ({}));
}

async function _estado() {
  const r = await fetch("/api/control", { cache: "no-store" });
  const d = await r.json().catch(() => ({}));
  return { agentes: d.agentes || [], grupos: d.grupos || {} };
}

export async function mountVentanaAgentes(root, { tell } = {}) {
  const hoja = document.getElementById(HOJA);
  if (!hoja) return;
  const lista = hoja.querySelector("#agentes-lista");
  if (!lista) return;

  const pintar = (agentes) => {
    lista.replaceChildren();
    if (!agentes.length) {
      const v = document.createElement("div");
      v.className = "consil-vacio";
      v.textContent = "El Router no devolvió el registro de agentes";
      lista.append(v);
      return;
    }
    for (const a of agentes) {
      const fila = document.createElement("div");
      fila.className = "fila-agente";
      fila.dataset.agente = a.id;

      const info = document.createElement("div");
      info.className = "agente-info";
      const nom = document.createElement("b");
      nom.textContent = a.nombre || a.id;
      const meta = document.createElement("div");
      meta.className = "muted agente-meta";
      meta.textContent = [a.tipo, a.estado, a.enabled ? "ON" : "OFF", a.tools && a.tools.length ? "tools: " + a.tools.join(",") : ""]
        .filter(Boolean).join(" · ");
      const rol = document.createElement("div");
      rol.className = "muted agente-rol";
      rol.textContent = a.rol || "";
      info.append(nom, meta, rol);

      const sw = document.createElement("button");
      sw.type = "button";
      sw.className = "toggle" + (a.enabled ? " on" : "");
      sw.setAttribute("aria-pressed", a.enabled ? "true" : "false");
      sw.title = a.enabled ? "Apagar este agente" : "Encender este agente";
      sw.textContent = a.enabled ? "ON" : "OFF";
      sw.addEventListener("click", async () => {
        sw.disabled = true;
        const d = await _control({ accion: a.enabled ? "agente-off" : "agente-on", agente: a.id });
        sw.disabled = false;
        if (tell) tell(d.ok ? (a.id + ": " + (a.enabled ? "apagado" : "encendido")) : (a.id + ": no se pudo (" + JSON.stringify(d.detalle || d).slice(0, 120) + ")"));
        await refrescar();
      });

      const usar = document.createElement("button");
      usar.type = "button";
      usar.className = "mini";
      usar.textContent = "Usar en el chat";
      usar.title = "Seleccionar este agente en el chat";
      usar.addEventListener("click", async () => {
        const sel = document.getElementById("agent");
        if (sel) {
          sel.value = a.id;
          sel.dispatchEvent(new Event("change", { bubbles: true }));
          const lab = sel.closest("label");
          if (lab) lab.hidden = false;
        }
        if (tell) tell("Agente en el chat: " + (a.nombre || a.id));
        const p = document.getElementById(HOJA);
        if (p) p.hidden = true;
      });

      const probar = document.createElement("button");
      probar.type = "button";
      probar.className = "mini";
      probar.textContent = "Probar";
      probar.title = "Mandar una prueba al agente y ver su salida";
      probar.addEventListener("click", async () => {
        probar.disabled = true;
        probar.textContent = "Probando…";
        const d = await _control({ accion: "agente-probar", agente: a.id, mensaje: "Di en una frase que puedes hacer." });
        probar.disabled = false;
        probar.textContent = "Probar";
        const out = document.getElementById("agente-salida");
        if (out) {
          out.hidden = false;
          out.textContent = "[" + a.id + "] HTTP " + (d.http || "-") + "\n" +
            (d.salida || JSON.stringify(d.respuesta || d).slice(0, 600));
        }
        if (tell) tell(d.ok ? (a.id + ": respondió") : (a.id + ": " + (d.salida || "sin salida")));
        await refrescar();
      });

      const acc = document.createElement("div");
      acc.className = "agente-acc";
      acc.append(sw, usar, probar);
      fila.append(info, acc);
      lista.append(fila);
    }
  };

  const refrescar = async () => {
    try {
      const { agentes } = await _estado();
      pintar(agentes);
    } catch (e) {
      if (tell) tell("Agentes: " + e.message);
    }
  };

  await refrescar();
  // refresco periodico: el estado de los agentes cambia en el Router
  setInterval(refrescar, 30000);
}
