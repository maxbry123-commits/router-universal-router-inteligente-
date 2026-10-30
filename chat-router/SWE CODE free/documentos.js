// Lee los adjuntos de activar() y arma el payload `documentos` para el bridge.
// Via: plugins -> deepseek_harness -> HTTP router -> bridge /v1/chat/completions.
const fs = require('fs');
const path = require('path');

const MAX_POR_DOC = 100000; // chars por documento

function leerDocumentos(adjuntos = []) {
  return adjuntos.map(ruta => {
    try {
      const p = path.resolve(ruta);
      return { nombre: path.basename(p), contenido: fs.readFileSync(p, 'utf8').slice(0, MAX_POR_DOC), ok: true };
    } catch (e) {
      return { nombre: ruta, contenido: null, ok: false, error: e.message };
    }
  });
}

// Incrusta el contenido en el prompt (para modelos locales o llamadas directas).
function incrustar(prompt, documentos = []) {
  const bloques = documentos
    .filter(d => d.ok && d.contenido)
    .map(d => `[DOCUMENTO: ${d.nombre}]\n${d.contenido}`)
    .join('\n\n');
  const faltantes = documentos.filter(d => !d.ok).map(d => d.nombre);
  return {
    prompt: bloques ? `${prompt}\n\n${bloques}` : prompt,
    faltantes, // rutas que no se pudieron leer -> avisar al usuario
  };
}

module.exports = { leerDocumentos, incrustar };
