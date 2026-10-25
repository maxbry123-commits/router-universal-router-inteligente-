// api/loop.js — estado del LOOP del chat. No toca el Router.
const estados = new Map();
const PARTES = ["objetivo", "plan", "tarea", "verificar"];
const corto = (v, n) => String(v || "").slice(0, n);

function base(sesion) {
  return estados.get(sesion) || { on: false, paso: 0, fase: "apagado", nota: "apagado", objetivo: "", plan: "", tareas: "" };
}
function conTexto(e, body) {
  return {
    on: e.on, paso: e.paso, fase: e.fase, nota: e.nota,
    objetivo: body.objetivo !== undefined ? corto(body.objetivo, 500) : e.objetivo,
    plan: body.plan !== undefined ? corto(body.plan, 800) : e.plan,
    tareas: body.tareas !== undefined ? corto(body.tareas, 1500) : e.tareas,
  };
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  const body = req.body && typeof req.body === "object" ? req.body : {};
  const crudo = req.method === "GET" ? (req.query && req.query.sesion) : body.sesion;
  const sesion = String(crudo || "web").slice(0, 80);
  let e = conTexto(base(sesion), body);
  if (req.method === "POST") {
    if (body.accion === "encender") e = { ...e, on: true, fase: "objetivo", nota: "encendido" };
    else if (body.accion === "apagar") e = { ...e, on: false, fase: "apagado", nota: "apagado" };
    else if (body.accion === "paso") {
      if (!e.on) return res.status(409).json({ detail: "el loop está apagado" });
      const fase = PARTES[(PARTES.indexOf(e.fase) + 1) % PARTES.length];
      e = { ...e, on: true, paso: e.paso + (fase === "objetivo" ? 1 : 0), fase, nota: fase };
    } else return res.status(400).json({ detail: "accion debe ser encender, apagar o paso" });
    estados.set(sesion, e);
  } else if (req.method !== "GET") return res.status(405).json({ detail: "GET o POST" });
  return res.status(200).json(e);
};
