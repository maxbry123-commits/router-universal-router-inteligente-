// SWEN CODE free — activación y parser mínimo.
// Regla: el sistema SOLO responde si el texto empieza con "SWEN CODE free".
// Formato: "SWEN CODE free [modo <modo>] [con|solo|modelo <modelo>] [chat <id>] <texto>"
//   - "SWEN CODE free modo consulta compara X e Y"
//   - "SWEN CODE free solo deepseek v4 arregla esto"      → un solo modelo web
//   - "SWEN CODE free concilio que hacer con X"           → los 3 modelos web
//   - "SWEN CODE free chat 2 modo solucion bug en api.js" → seccion paralela (conv_id propio)
// Devuelve null si no está activado.

const MODOS = ["revision", "solucion", "arquitectura", "archivos", "prompt_code", "consulta", "despliega", "asesoria"];
const CLAVE = /^\s*swen\s+code\s+free\b/i; // tolera espacios iniciales
const PIPELINES = ["code", "free", "auto"];

// "pipeline [code|free|auto]": code = anota->organiza+refactor->despliega;
// free = instruye->despliega (sin refactor). Default free (esta capa no refactoriza).
function sacaPipeline(resto) {
  const m = resto.match(/^pipeline\b(?:\s+(code|free|auto)\b)?/i);
  if (!m) return null;
  return { pipeline: (m[1] || "free").toLowerCase(), resto: resto.slice(m[0].length).trim() };
}

// nombre hablado -> id de modelo ("consenso" = concilio de los 3 web)
// El id puede ser un texto fijo o una funcion (coincidencia) -> id, para ids completos escritos tal cual.
// Orden importa: primero los ids completos (nada de recortar "nvidia" de "nvidia/z-ai/glm-5.3"),
// luego los alias cortos.
const idLiteral = (a) => a[0].toLowerCase();
const MODELOS_ALIAS = [
  [/^(groq|nvidia)\/[\w.\/-]*\w/i, idLiteral],
  [/^(lfm2\.5-350m|qwen2\.5-coder-1\.5b|qwen3\.5-0\.8b|qwen3-0\.6b)(?![\w-]|\.\w)/i, idLiteral],
  [/^(concilio|c[oó]ncil|consenso|todos|los\s*3)\b/i, "consenso"],
  [/^(deepseek[- ]?v4[- ]?flash|deepseek[- ]?v4|dsv4[- ]?flash|dsv4|deepseek)\b/i, "web-dsv4-flash"],
  [/^(qwen[- ]?3\.?7[- ]?max|qwen[- ]?3\.?7|qwen37[- ]?max|qwen37)\b/i, "web-qwen37max"],
  [/^(qwen[- ]?3\.?8[- ]?max|qwen[- ]?3\.?8|qwen38[- ]?max|qwen38)\b/i, "web-qwen38max"],
  [/^(lfm2\.?5|liquid|lfm)\b/i, "lfm2.5-350m"],
  [/^(qwen[- ]?code|qwen2\.?5|coder)\b/i, "qwen2.5-coder-1.5b"],
  [/^qwen[- ]?3\.?5(?![\w.]*\d)\b/i, "qwen3.5-0.8b"],
  [/^qwen[- ]?3(?![\d.])\b/i, "qwen3-0.6b"],
  [/^groq\b/i, "groq/qwen/qwen3.8-27b"],
  [/^(muse|glimmer)\b/i, "nvidia/meta/muse-glimmer-30b"],
  [/^nemotron\b/i, "nvidia/nvidia/nemotron-3-ultra-550b-a55b"],
  [/^glm(?:[- ]?5\.?3)?\b(?![-.]?\d)/i, "nvidia/z-ai/glm-5.3"],
  [/^minimax\b/i, "nvidia/minimaxai/minimax-m3.1-flash"],
  [/^nvidia\b/i, "nvidia/minimaxai/minimax-m3.1-flash"],
];
const idDe = (id, a) => (typeof id === "function" ? id(a) : id);

// Quita tildes SIN cambiar la longitud (char a char), para casar contra la version
// normalizada y cortar el texto original con los mismos indices ("revisión" -> "revision").
function sinTildes(s) {
  return Array.from(s, (c) => {
    const b = c.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return b.length === c.length ? b : c;
  }).join("");
}

// Distancia de edicion (Levenshtein) para detectar nombres mal escritos.
function distancia(a, b) {
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    prev = cur;
  }
  return prev[b.length];
}

// Nombres base de alias, solo para decidir si un "modelo <palabra>" es un alias mal escrito.
const BASES_ALIAS = ["concilio", "consenso", "deepseek", "nvidia", "liquid", "coder", "qwen", "groq", "lfm", "glimmer", "nemotron", "minimax", "muse", "glm"];
const parecido = (w, bases, tol) => bases.some((b) => distancia(w, b) <= tol(b));

// Criterio de error (simple): la palabra tras con/solo/modelo que NO es alias se deja en el prompt
// (es parte de la frase: "solo necesito...", "con el codigo..."). Solo es error si TODO el texto
// restante es exactamente "modelo <palabra>" y la palabra se parece a un alias (<=2 ediciones en
// nombres de 6+ letras, <=1 en los cortos): ahi es casi seguro un alias mal escrito.
// Alias sin keyword: solo si es la PRIMERA palabra, va seguido de mas texto y la palabra siguiente
// no es de las que muestran que el alias es el sujeto de la frase ("deepseek no responde",
// "todos los tests fallan"). Con keyword explicita (con/solo/modelo) siempre manda el alias.
const NO_SELECCION = new Set(["no", "nunca", "tampoco", "ya", "es", "esta", "estan", "son", "se", "me", "te", "de", "del", "en",
  "los", "las", "el", "la", "mis", "tus", "sus", "falla", "fallan", "responde", "funciona", "funcionan", "tarda", "tiene", "tienen", "da", "dan", "devuelve"]);

function sacaModelo(resto, yaHayModelo) {
  const sin = sinTildes(resto);
  // "con|solo|modelo <nombre...>": el alias puede ser de varias palabras
  const m = sin.match(/^(con|solo|modelo)\s+([\s\S]+)/i);
  if (m) {
    const cola = sin.slice(m[0].length - m[2].length);
    for (const [re, id] of MODELOS_ALIAS) {
      const a = cola.match(re);
      if (a) return { modelo: idDe(id, a), resto: resto.slice(m[0].length - m[2].length + a[0].length).trim() };
    }
    const solo = sin.trim().match(/^modelo\s+(\S+)$/i);
    if (solo && parecido(solo[1].toLowerCase(), BASES_ALIAS, (b) => (b.length >= 6 ? 2 : 1))) return { modelo: null, error: solo[1] };
    return null; // no es alias: la palabra es parte del prompt
  }
  if (yaHayModelo) return null;
  // nombre del modelo como primera palabra, sin keyword
  for (const [re, id] of MODELOS_ALIAS) {
    const a = sin.match(re);
    if (!a) continue;
    const despues = resto.slice(a[0].length).trim();
    const sig = sin.slice(a[0].length).trim().split(/\s+/)[0].toLowerCase();
    if (!despues || NO_SELECCION.has(sig)) return null;
    return { modelo: idDe(id, a), resto: despues };
  }
  return null;
}

function sacaChat(resto) {
  const m = resto.match(/^(chat|seccion|conv)\s+([\w-]+)/i);
  if (!m) return null;
  return { conv_id: `chat-${m[2]}`, resto: resto.slice(m[0].length).trim() };
}

// doc|documento|adjunto|archivo|file <ruta>  — se puede repetir para varios
function sacaAdjunto(resto) {
  const m = resto.match(/^(doc|documento|adjunto|archivo|file)\s+([^\s]+)/i);
  if (!m) return null;
  return { archivo: m[2], resto: resto.slice(m[0].length).trim() };
}

function activar(texto) {
  if (typeof texto !== "string" || !CLAVE.test(texto)) return null;
  let resto = texto.replace(CLAVE, "").trim();
  let modo = "consulta";
  let modelo = null;
  let conv_id = null;
  let pipeline = null;
  let adjuntos = [];

  // keywords en cualquier orden: se consumen prefijos hasta que nada cambie
  let cambio = true;
  while (cambio) {
    cambio = false;
    // normalizado sin tildes ("revisión" -> "revision"); misma longitud que resto
    const m = sinTildes(resto).match(/^modo\s+([a-z0-9_]+)(?![\w])\s*:?\s*/i);
    if (m) {
      const pedido = m[1].toLowerCase();
      if (MODOS.includes(pedido)) {
        modo = pedido;
        resto = resto.slice(m[0].length).trim();
        cambio = true;
      } else if (parecido(pedido, MODOS, () => 2)) {
        // nombre de modo mal escrito (<=2 ediciones): error; si no, "modo" es parte de la frase
        return { error: `modo desconocido: ${pedido}`, modos: MODOS };
      }
    }
    const mod = sacaModelo(resto, !!modelo);
    if (mod) {
      if (mod.error) {
        return { error: `modelo desconocido: ${mod.error}`, modelos: MODELOS_ALIAS.map(a => a[1]).filter((id) => typeof id === "string") };
      }
      modelo = mod.modelo;
      resto = mod.resto;
      cambio = true;
    }
    const ch = sacaChat(resto);
    if (ch) { conv_id = ch.conv_id; resto = ch.resto; cambio = true; }
    const pl = sacaPipeline(resto);
    if (pl) { pipeline = pl.pipeline; resto = pl.resto; cambio = true; }
    const ad = sacaAdjunto(resto);
    if (ad) { adjuntos.push(ad.archivo); resto = ad.resto; cambio = true; }
  }

  // consulta sin modelo nombrado = concilio (los 3); el resto = objetivo unico
  if (!modelo) modelo = modo === "consulta" ? "consenso" : "web-qwen38max";

  return { sistema: "SWEN CODE free", modo, modelo, conv_id, pipeline, adjuntos, prompt: resto };
}

module.exports = { activar, MODOS, CLAVE, MODELOS_ALIAS, PIPELINES };
