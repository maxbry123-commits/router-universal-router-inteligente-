// SWEN CODE free — activación y parser mínimo.
// Regla: el sistema SOLO responde si el texto empieza con "SWEN CODE free".
// Formato: "SWEN CODE free [modo <modo>] [con|solo|modelo <modelo>] [chat <id>] <texto>"
//   - "SWEN CODE free modo consulta compara X e Y"
//   - "SWEN CODE free solo deepseek v4 arregla esto"      → un solo modelo web
//   - "SWEN CODE free concilio que hacer con X"           → los 3 modelos web
//   - "SWEN CODE free chat 2 modo solucion bug en api.js" → seccion paralela (conv_id propio)
// Devuelve null si no está activado.

const MODOS = ["revision", "solucion", "arquitectura", "archivos", "prompt_code", "consulta", "despliega"];
const CLAVE = /^swen\s+code\s+free\b/i;

// nombre hablado -> id de modelo ("consenso" = concilio de los 3 web)
const MODELOS_ALIAS = [
  [/^(concilio|c[oó]ncil|consenso|todos|los\s*3)\b/i, "consenso"],
  [/^(deepseek[- ]?v4[- ]?flash|deepseek[- ]?v4|dsv4[- ]?flash|dsv4|deepseek)\b/i, "web-dsv4-flash"],
  [/^(qwen[- ]?3\.?7[- ]?max|qwen[- ]?3\.?7|qwen37[- ]?max|qwen37)\b/i, "web-qwen37max"],
  [/^(qwen[- ]?3\.?8[- ]?max|qwen[- ]?3\.?8|qwen38[- ]?max|qwen38)\b/i, "web-qwen38max"],
  [/^(lfm2\.?5|liquid|lfm)\b/i, "lfm2.5-350m"],
  [/^(qwen[- ]?code|qwen2\.?5|coder)\b/i, "qwen2.5-coder-1.5b"],
];

function sacaModelo(resto) {
  // "con|solo|modelo <nombre...>": el alias puede ser de varias palabras
  const m = resto.match(/^(?:con|solo|modelo)\s+(.+)/i);
  if (m) {
    for (const [re, id] of MODELOS_ALIAS) {
      if (re.test(m[1])) return { modelo: id, resto: m[1].replace(re, "").trim() };
    }
    return { modelo: null, error: m[1].split(/\s+/)[0] };
  }
  // nombre del modelo como primera palabra, sin keyword
  for (const [re, id] of MODELOS_ALIAS) {
    if (re.test(resto)) return { modelo: id, resto: resto.replace(re, "").trim() };
  }
  return null;
}

function sacaChat(resto) {
  const m = resto.match(/^(chat|seccion|conv)\s+([\w-]+)/i);
  if (!m) return null;
  return { conv_id: `chat-${m[2]}`, resto: resto.slice(m[0].length).trim() };
}

function activar(texto) {
  if (!CLAVE.test(texto || "")) return null;
  let resto = texto.replace(CLAVE, "").trim();
  let modo = "consulta";
  let modelo = null;
  let conv_id = null;

  // keywords en cualquier orden: se consumen prefijos hasta que nada cambie
  let cambio = true;
  while (cambio) {
    cambio = false;
    const m = resto.match(/^modo\s+(\w+)\s*:?\s*/i);
    if (m) {
      const pedido = m[1].toLowerCase();
      if (!MODOS.includes(pedido)) {
        return { error: `modo desconocido: ${pedido}`, modos: MODOS };
      }
      modo = pedido;
      resto = resto.slice(m[0].length).trim();
      cambio = true;
    }
    const mod = sacaModelo(resto);
    if (mod) {
      if (mod.error) {
        return { error: `modelo desconocido: ${mod.error}`, modelos: MODELOS_ALIAS.map(a => a[1]) };
      }
      modelo = mod.modelo;
      resto = mod.resto;
      cambio = true;
    }
    const ch = sacaChat(resto);
    if (ch) { conv_id = ch.conv_id; resto = ch.resto; cambio = true; }
  }

  // consulta sin modelo nombrado = concilio (los 3); el resto = objetivo unico
  if (!modelo) modelo = modo === "consulta" ? "consenso" : "web-qwen38max";

  return { sistema: "SWEN CODE free", modo, modelo, conv_id, prompt: resto };
}

module.exports = { activar, MODOS, CLAVE, MODELOS_ALIAS };
