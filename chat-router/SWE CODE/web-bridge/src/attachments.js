// attachments.js — valida partes de contenido OpenAI (image_url) antes de enviarlas a la web.
// G7: solo acepta imagenes https o data:image/*;base64 dentro de limites de tamaño.
// Sin red, sin disco: no descarga nada. Devuelve {ok:true, partes} o {ok:false, code, message}.

const MAX_BYTES = parseInt(process.env.BRIDGE_ADJ_MAX_BYTES || String(10 * 1024 * 1024), 10);
const TIPOS_OK = /^image\/(png|jpe?g|gif|webp)$/i;

function tamañoBase64(b64) {
  const limpio = b64.replace(/\s/g, '');
  const pad = (limpio.endsWith('==') ? 2 : limpio.endsWith('=') ? 1 : 0);
  return Math.floor(limpio.length * 3 / 4) - pad;
}

export function validarAdjuntos(mensajes) {
  const partes = [];
  if (!Array.isArray(mensajes)) return { ok: true, partes };
  for (const m of mensajes) {
    if (!m || !Array.isArray(m.content)) continue;
    for (const p of m.content) {
      if (!p || typeof p !== 'object') continue;
      if (p.type === 'text') continue;
      if (p.type !== 'image_url') {
        return { ok: false, code: 'ADJUNTO_TIPO_NO_SOPORTADO', message: `tipo no soportado: ${p.type}` };
      }
      const url = p.image_url && typeof p.image_url === 'object' ? p.image_url.url : p.image_url;
      if (typeof url !== 'string' || !url) {
        return { ok: false, code: 'ADJUNTO_SIN_URL', message: 'image_url sin url' };
      }
      if (/^https:\/\//i.test(url)) {
        partes.push({ tipo: 'url', url });
        continue;
      }
      const m2 = /^data:([^;,]+);base64,(.*)$/is.exec(url);
      if (!m2) {
        return { ok: false, code: 'ADJUNTO_URL_NO_PERMITIDA', message: 'solo https o data:image/*;base64' };
      }
      if (!TIPOS_OK.test(m2[1])) {
        return { ok: false, code: 'ADJUNTO_TIPO_IMAGEN_NO_SOPORTADO', message: `tipo ${m2[1]}` };
      }
      const bytes = tamañoBase64(m2[2]);
      if (bytes > MAX_BYTES) {
        return { ok: false, code: 'ADJUNTO_DEMASIADO_GRANDE', message: `${bytes} bytes > ${MAX_BYTES}` };
      }
      partes.push({ tipo: 'data', mime: m2[1], bytes });
    }
  }
  return { ok: true, partes };
}
