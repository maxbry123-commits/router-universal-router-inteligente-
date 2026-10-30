// motor.js — el canal cableado: escribe bloques, lee salida, checkpoint, reintento
import { SITES, MODELOS_WEB, escribe, enviar, leerRespuesta, sesionMuerta, elegirModelo } from './sites.js';
import { asegurar, nuevaPagina } from './browser.js';
import { partir, cabecera, checkpointLeer, checkpointGuardar, resumeCard, huella } from './bloques.js';
import { preambulo } from './modos.js';

// consultarWeb(modelo_web, texto, {modo, convId}) -> respuesta del sitio
export async function consultarWeb(modelo, texto, { modo = 'consulta', convId = null } = {}) {
  const cfg = MODELOS_WEB[modelo];
  if (!cfg) throw new Error(`modelo web desconocido: ${modelo}`);
  const site = cfg.site;
  convId = convId || `${site}-${modelo}-${Date.now()}`;
  // cada conv = su propio tab + chat nuevo (tareas en paralelo, separadas)
  const page = await nuevaPagina(site, convId);
  const siteCfg = SITES[site];
  // elige el modelo pedido en el picker de la web (qwen: Select Model)
  await elegirModelo(page, siteCfg, cfg.modelo_regex).catch(() => false);
  const bloques = partir(`${preambulo(modo)}\n${texto}`);
  const h = huella(texto);
  let ck = checkpointLeer(convId, h) || { modo, total: bloques.length, enviados: 0, ultima_salida: '', huella: h };

  // retomo: si habia checkpoint, aviso al modelo donde ibamos
  if (ck.enviados > 0 && ck.enviados < ck.total) {
    await escribe(page, siteCfg, resumeCard(ck));
    await enviar(page, siteCfg);
    await leerRespuesta(page, siteCfg, { timeoutMs: 60000 });
  }

  for (let i = ck.enviados; i < ck.total; i++) {
    const ok = await escribe(page, siteCfg, cabecera(i + 1, ck.total, modo) + bloques[i]);
    if (!ok) throw Object.assign(new Error('INPUT_NO_ENCONTRADO'), { code: 'SELECTOR_BROKEN', site });
    await enviar(page, siteCfg);
    const salida = await leerRespuesta(page, siteCfg);
    if (sesionMuerta(page, siteCfg)) throw Object.assign(new Error('SESION_MUERTA'), { code: 'SESSION_EXPIRED', site });
    ck = { ...ck, enviados: i + 1, ultima_salida: salida || '' };
    checkpointGuardar(convId, ck);
  }

  const final = ck.ultima_salida;
  checkpointGuardar(convId, { ...ck, completo: true });
  return final;
}

// salud: verifica que cada sitio tenga sesion viva (sin gastar un mensaje real)
export async function salud() {
  const out = {};
  for (const site of Object.keys(SITES)) {
    try { await asegurar(site); out[site] = 'vivo'; }
    catch (e) { out[site] = `caido:${e.code || e.message}`; }
  }
  return out;
}
