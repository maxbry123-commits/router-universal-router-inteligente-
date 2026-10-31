// bancogithub.js — GitHub como puente del banco de claves, sin tocar Hugging Face: el banco propio (ya cifrado con la clave de acceso) se publica en la rama
// `banco-claves` del repo (nunca en main: no dispara autopull ni reinicios). Un Space nuevo lo trae al arrancar. El repo es privado y el archivo va cifrado.
import fs from 'node:fs';
import path from 'node:path';

const REPO = () => process.env.RIU_REPO || 'maxbry123-commits/router-universal-router-inteligente-';
const API = () => process.env.RIU_GITHUB_API || 'https://api.github.com';
const RAMA = 'banco-claves', ARCHIVO = 'banco-swe.bin';
const local = () => path.join(process.env.BRIDGE_STATE_DIR || './state', ARCHIVO);

async function gh(api, token, ruta, op = {}) {
  const r = await fetch(api + ruta, { ...op, signal: AbortSignal.timeout(15000), headers: { authorization: `Bearer ${token}`, accept: 'application/vnd.github+json', 'user-agent': 'riu-bridge', 'content-type': 'application/json' } });
  return { ok: r.ok, status: r.status, json: await r.json().catch(() => ({})) };
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
    const actual = await gh(api, token, `${base}/contents/${ARCHIVO}?ref=${RAMA}`);
    const cuerpo = { message: 'banco de claves (cifrado)', branch: RAMA, content: fs.readFileSync(local()).toString('base64'), ...(actual.ok ? { sha: actual.json.sha } : {}) };
    return (await gh(api, token, `${base}/contents/${ARCHIVO}`, { method: 'PUT', body: JSON.stringify(cuerpo) })).ok;
  } catch { return false; }
}

// ultimo intento de traer el banco (solo datos de estado, nunca valores): lo muestra /health para diagnosticar sin logs
export const diagTraer = { token: false, http: null, ts: null };

// Space nuevo: si no hay banco local, trae el de GitHub; nunca pisa uno local
export async function traerDeGithub({ api = API(), token = process.env.GITHUB_TOKEN, repo = REPO(), forzar = false } = {}) {
  try {
    diagTraer.token = !!token;
    if (!token || (!forzar && fs.existsSync(local()))) return false;
    const r = await gh(api, token, `/repos/${repo}/contents/${ARCHIVO}?ref=${RAMA}`);
    diagTraer.http = r.status; diagTraer.ts = new Date().toISOString();
    if (!r.ok || !r.json.content) return false;
    fs.mkdirSync(path.dirname(local()), { recursive: true });
    fs.writeFileSync(local(), Buffer.from(r.json.content, 'base64'), { mode: 0o600 });
    return true;
  } catch { return false; }
}
