// SWEN CODE free — activación y parser mínimo.
// Regla: el sistema SOLO responde si el texto empieza con "SWEN CODE free".
// Formato: "SWEN CODE free [modo <modo>] <texto>"
//   - "SWEN CODE free modo consulta compara X e Y"
//   - "SWEN CODE free"            → modo por defecto: consulta
// Devuelve null si no está activado.

const MODOS = ["revision", "solucion", "arquitectura", "archivos", "prompt_code", "consulta"];
const CLAVE = /^swen\s+code\s+free\b/i;

function activar(texto) {
  if (!CLAVE.test(texto || "")) return null;
  let resto = texto.replace(CLAVE, "").trim();
  let modo = "consulta";
  const m = resto.match(/^modo\s+(\w+)\s*:?\s*/i);
  if (m) {
    const pedido = m[1].toLowerCase();
    if (!MODOS.includes(pedido)) {
      return { error: `modo desconocido: ${pedido}`, modos: MODOS };
    }
    modo = pedido;
    resto = resto.slice(m[0].length).trim();
  }
  return { sistema: "SWEN CODE free", modo, prompt: resto };
}

module.exports = { activar, MODOS, CLAVE };
