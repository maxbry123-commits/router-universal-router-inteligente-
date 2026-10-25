// api/loop.js — estado del LOOP del chat. No toca el Router.
const estados = new Map();
const FASES = ["leer", "paso", "verificar", "repetir"];

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  const body = req.body && typeof req.body === "object" ? req.body : {};
  const crudo = req.method === "GET" ? (req.query && req.query.sesion) : body.sesion;
  const sesion = String(crudo || "web").slice(0, 80);
  let e = estados.get(sesion) || { on: false, paso: 0, fase: "apagado", nota: "apagado" };
  if (req.method === "POST") {
    if (body.accion === "encender") e = { on: true, paso: e.paso, fase: "leer", nota: "encendido" };
    else if (body.accion === "apagar") e = { on: false, paso: e.paso, fase: "apagado", nota: "apagado" };
    else if (body.accion === "paso") {
      if (!e.on) return res.status(409).json({ detail: "el loop está apagado" });
      const fase = FASES[(FASES.indexOf(e.fase) + 1) % FASES.length];
      e = { on: true, paso: e.paso + (fase === "leer" ? 1 : 0), fase, nota: fase };
    } else return res.status(400).json({ detail: "accion debe ser encender, apagar o paso" });
    estados.set(sesion, e);
  } else if (req.method !== "GET") return res.status(405).json({ detail: "GET o POST" });
  return res.status(200).json(e);
};
