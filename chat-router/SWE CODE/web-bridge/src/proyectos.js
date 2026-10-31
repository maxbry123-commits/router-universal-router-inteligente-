// proyectos.js — un archivo ASESORIA.md por proyecto: plan, mapa mental, estructura y como resolver problemas, para que OpenClaw lo reuse
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const DIR = () => path.join(process.env.BRIDGE_STATE_DIR || './state', 'proyectos');

export function slug(nombre) {
  const s = String(nombre || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
  // sin letras latinas (o recortado) no se puede usar solo el texto: se agrega un hash corto para que proyectos distintos no compartan archivo
  const crudo = String(nombre || '').trim();
  if (!crudo) return 'general';
  const necesitaHash = !s || crudo.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').length > 60;
  return necesitaHash ? ((s ? s.slice(0, 40) + '-' : 'p-') + crypto.createHash('sha256').update(crudo).digest('hex').slice(0, 8)) : s;
}

export function guardarAsesoria(proyecto, { texto, via = 'web', modelo = '' }) {
  const dir = path.join(DIR(), slug(proyecto));
  fs.mkdirSync(dir, { recursive: true });
  const f = path.join(dir, 'ASESORIA.md');
  const cab = fs.existsSync(f) ? '' : `# Asesoría — ${slug(proyecto)}\n`;
  fs.appendFileSync(f, `${cab}\n---\n## ${new Date().toISOString()} · ${via}${modelo ? ' · ' + modelo : ''}\n\n${texto}\n`);
  return f;
}

export function leerProyecto(proyecto) {
  const f = path.join(DIR(), slug(proyecto), 'ASESORIA.md');
  try { return { proyecto: slug(proyecto), texto: fs.readFileSync(f, 'utf8') }; } catch { return null; }
}

export function listarProyectos() {
  try { return fs.readdirSync(DIR()).filter(d => fs.existsSync(path.join(DIR(), d, 'ASESORIA.md'))); } catch { return []; }
}
