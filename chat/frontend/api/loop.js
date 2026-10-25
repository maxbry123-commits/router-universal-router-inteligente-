// api/loop.js — estado del LOOP del chat. No toca el Router.
const estados = new Map();
const PARTES = ["objetivo", "plan", "tarea", "verificar"];
const corto = (v, n) => String(v || "").slice(0, n);

function base(sesion) {
  return estados.get(sesion) || { on: false, paso: 0, fase: "apagado", nota: "apagado", objetivo: "", plan: "", tareas: "" };
}
function disparar(e) {
  const tareas = String(e.tareas || "").split(/\n/).map((s) => s.trim()).filter(Boolean);
  const fase = PARTES.includes(e.fase) ? e.fase : "objetivo";
  const hecho = e.hecho || 0;
  if (fase === "objetivo") {
    if (!String(e.objetivo || "").trim()) return { ...e, on: true, fase, nota: "falta objetivo", disparo: "" };
    return { ...e, on: true, fase: "plan", nota: "objetivo", disparo: String(e.objetivo).trim().slice(0, 180) };
  }
  if (fase === "plan") {
    if (!String(e.plan || "").trim()) return { ...e, on: true, fase, nota: "falta plan", disparo: "" };
    return { ...e, on: true, fase: "tarea", nota: "plan", disparo: String(e.plan).trim().slice(0, 180) };
  }
  if (fase === "tarea") {
    if (!tareas.length || hecho >= tareas.length) return { ...e, on: true, fase, nota: "sin tareas", disparo: "" };
    return { ...e, on: true, fase: "verificar", hecho: hecho + 1, nota: "tarea", disparo: tareas[hecho].slice(0, 180) };
  }
  if (!e.disparo) return { ...e, on: true, fase: "verificar", nota: "nada que verificar" };
  return { ...e, on: true, fase: "objetivo", paso: (e.paso || 0) + 1, nota: hecho >= tareas.length ? "vuelta completa" : "verificado" };
}
function conTexto(e, body) {
  return {
    on: e.on, paso: e.paso, fase: e.fase, nota: e.nota,
    objetivo: body.objetivo !== undefined ? corto(body.objetivo, 500) : e.objetivo,
    plan: body.plan !== undefined ? corto(body.plan, 800) : e.plan,
    tareas: body.tareas !== undefined ? corto(body.tareas, 1500) : e.tareas,
    hecho: e.hecho || 0, disparo: e.disparo || "",
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
      e = disparar(e);
    } else return res.status(400).json({ detail: "accion debe ser encender, apagar o paso" });
    estados.set(sesion, e);
  } else if (req.method !== "GET") return res.status(405).json({ detail: "GET o POST" });
  return res.status(200).json(e);
};
