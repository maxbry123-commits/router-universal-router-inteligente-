// bancogithub.js — GitHub como puente del banco de claves, sin tocar Hugging Face: el banco propio (ya cifrado con la clave de acceso) se publica en la rama
// `banco-claves` del repo (nunca en main: no dispara autopull ni reinicios). Un Space nuevo lo trae al arrancar. El repo es privado y el archivo va cifrado.
import fs from 'node:fs';
import path from 'node:path';

const REPO = () => process.env.RIU_REPO || 'maxbry123-commits/router-universal-router-inteligente-';
const API = () => process.env.RIU_GITHUB_API || 'https://api.github.com';
const RAMA = 'banco-claves', ARCHIVO = 'banco-swe.bin';
const local = () => path.join(process.env.BRIDGE_STATE_DIR || './state', ARCHIVO);

async function gh(api, token, ruta, op = {}) {
  const r = await fetch(api + ruta, { ...op, redirect: 'error', signal: AbortSignal.timeout(15000), headers: { authorization: `Bearer ${token}`, accept: 'application/vnd.github+json', 'user-agent': 'riu-bridge', 'content-type': 'application/json' } });
  return { ok: r.ok, status: r.status, json: await r.json().catch(() => ({})) };
}

// una publicacion: lee el sha vigente y hace PUT (un sha desfasado da 409)
async function subir(api, token, base) {
  const actual = await gh(api, token, `${base}/contents/${ARCHIVO}?ref=${RAMA}`);
  const cuerpo = { message: 'banco de claves (cifrado)', branch: RAMA, content: fs.readFileSync(local()).toString('base64'), ...(actual.ok ? { sha: actual.json.sha } : {}) };
  return gh(api, token, `${base}/contents/${ARCHIVO}`, { method: 'PUT', body: JSON.stringify(cuerpo) });
}

export async function publicarEnGithub({ api = API(), token = process.env.GITHUB_TOKEN, repo = REPO() } = {}) {
  try {
    if (!token || !fs.existsSync(local())) return false;
    const base = `/repos/${repo}`;
    if (!(await gh(api, token, `${base}/git/ref/heads/${RAMA}`)).ok) {  // la rama se crea desde main una sola vez
      const m = await gh(api, token, `${base}/git/ref/heads/main`);
      if (!m.ok) return false;
      if (!(await gh(api, token, `${base}/git/refs`, { method: 'POST', body: JSON.stringify({ ref: `refs/heads/${RAMA}`, sha: m.json.object.sha }) })).ok) return false;
    }
    let r = await subir(api, token, base);
    if (!r.ok && (r.status === 409 || r.status === 422)) r = await subir(api, token, base);  // sha desfasado (otra publicacion en medio): se relee el sha y se reintenta UNA vez
    return r.ok;
  } catch { return false; }
}

const MARCA = 'MVPB1';
const valido = (b, size) => Buffer.isBuffer(b) && b.length > 21 && b.subarray(0, 5).toString('latin1') === MARCA && (size == null || b.length === size);
// El banco es binario: se pide en crudo (media type raw). Si llega recodificado a UTF-8 (cada byte >= 0x80 en 2 bytes; pasaba en el Space: 1357 -> 2036) se repara y, si aun no es un banco valido, se descarta.
async function descargar(api, token, repo, meta) {
  const size = typeof meta.size === 'number' ? meta.size : null;
  const candidatos = [];
  try {
    const r = await fetch(`${api.replace(/\/$/, '')}/repos/${repo}/contents/${ARCHIVO}?ref=${RAMA}`, { signal: AbortSignal.timeout(15000), redirect: 'error', headers: { authorization: `Bearer ${token}`, accept: 'application/vnd.github.raw+json', 'user-agent': 'riu-bridge' } });
    if (r.ok) candidatos.push(Buffer.from(await r.arrayBuffer()));
  } catch { /* se prueba el base64 */ }
  if (meta.content) candidatos.push(Buffer.from(meta.content, 'base64'));
  for (const c of [...candidatos, ...candidatos.map((b) => Buffer.from(b.toString('utf8'), 'latin1'))]) if (valido(c, size)) return c;
  return null;
}

// ultimo intento de traer el banco (solo datos de estado, nunca valores): lo muestra /health para diagnosticar sin logs
export const diagTraer = { token: false, http: null, ts: null, escrito: null, error: null };

// Space nuevo: si no hay banco local, trae el de GitHub; nunca pisa uno local
export async function traerDeGithub({ api = API(), token = process.env.GITHUB_TOKEN, repo = REPO(), forzar = false } = {}) {
  try {
    diagTraer.token = !!token;
    if (!token || (!forzar && fs.existsSync(local()))) return false;
    const r = await gh(api, token, `/repos/${repo}/contents/${ARCHIVO}?ref=${RAMA}`);
    diagTraer.http = r.status; diagTraer.ts = new Date().toISOString();
    diagTraer.api = { repo, rama: RAMA, size: r.json.size, sha8: String(r.json.sha || '').slice(0, 8), encoding: r.json.encoding, content_len: String(r.json.content || '').length };  // solo metadatos del archivo remoto, nunca su contenido
    if (!r.ok || !r.json.content) return false;
    fs.mkdirSync(path.dirname(local()), { recursive: true });
    const datos = await descargar(api, token, repo, r.json);
    if (!datos) { diagTraer.escrito = false; diagTraer.error = 'BANCO_REMOTO_INVALIDO'; return false; }  // no es un banco (marca MVPB1) ni tiene el tamaño declarado: no sustituye al local
    const tmp = `${local()}.tmp-${process.pid}`;  // temporal + rename: sustituye el archivo aunque el existente sea de otro usuario o de solo lectura (copia restaurada de /data)
    try { fs.writeFileSync(tmp, datos, { mode: 0o600 }); fs.renameSync(tmp, local()); } catch (e) { try { fs.unlinkSync(tmp); } catch { /* ya no esta */ } throw e; }
    diagTraer.escrito = true; diagTraer.error = null; try { diagTraer.escrito_bytes = fs.statSync(local()).size; diagTraer.marca = fs.readFileSync(local()).subarray(0, 5).toString('latin1').replace(/[^\x20-\x7e]/g, '?'); } catch { /* solo diagnostico */ }
    return true;
  } catch (e) { diagTraer.escrito = false; diagTraer.error = String(e && (e.code || e.name) || 'x').slice(0, 40); return false; }
}
