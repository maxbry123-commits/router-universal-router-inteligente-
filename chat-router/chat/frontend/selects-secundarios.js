import { node } from "./api.js";
// selects-secundarios.js — selects secundarios (dentro de «más»): proveedor, modelo, agente, grupo, cuenta GitHub
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export async function montarSelectsSecundarios(ctx) {
  const { q, api, tell } = ctx;

  // ---- selects secundarios (dentro de más) ----
  const select = (id, options, value, label) => {
    const target = q(id);
    for (const item of options) {
      const option = node("option", item[label]);
      option.value = item[value];
      target.append(option);
    }
  };
  // El Router NO expone /chat/providers ni /chat/agents: expone /v1/providers/health
  // y /v1/agents. Antes, el primer 404 abortaba TODO el bloque y dejaba vacios
  // #provider, #agent y #github (por eso el selector de agente salia vacio).
  // Ahora cada bloque va por separado y el catalogo/los agentes llegan por la
  // funcion serverless /api/control (mismo origen, sin token en el navegador).
  const control = await fetch("/api/control", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const cat = (control && control.catalogo) || {};

  try {
    // UN proveedor por fila (los modelos no se repiten).
    const lista = [];
    const vistos = new Set();
    for (const m of cat.modelos || []) {
      const pv = m.proveedor;
      if ((pv === "nvidia" || pv === "groq") && !vistos.has(pv)) {
        vistos.add(pv);
        lista.push({ id: pv, label: pv.toUpperCase() });
      }
    }
    if ((cat.locales || []).length) lista.push({ id: "local", label: "SWE CODE local (HF)" });
    const sel = q("#provider");
    if (sel && lista.length) select("#provider", lista, "id", "label");
  } catch (error) { tell("Proveedores: " + error.message); }

  try {
    // AGENTES: registro real del Router (GET /v1/agents via /api/control)
    const agentes = (control && control.agentes) || [];
    select("#agent", agentes.map((a) => ({ id: a.id, name: (a.nombre || a.id) + (a.enabled ? "" : " — OFF") })), "id", "name");
    const legacy = q("#agent");
    // El selector de agente se MUESTRA si hay agentes en el registro.
    if (legacy && legacy.closest("label")) legacy.closest("label").hidden = !agentes.length;
  } catch (error) { tell("Agentes: " + error.message); }

  try {
    const accounts = await api("/chat/github/accounts");
    select("#github", accounts.accounts || [], "account", "account");
  } catch (error) { /* cuentas GitHub: opcional */ }
  q("#provider").addEventListener("change", async event => {
    const model = q("#model");
    model.replaceChildren(node("option", "Router elige"));
    if (event.target.value === "auto") return;
    try { select("#model", (await api(`/chat/providers/${encodeURIComponent(event.target.value)}/models`)).models || [], "model_id", "label"); }
    catch (error) { tell(error.message); }
  });
}
