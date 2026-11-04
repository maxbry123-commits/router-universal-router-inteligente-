// motor.js — el canal cableado: escribe bloques, lee salida, checkpoint, reintento
// Vía 14: verificarSesionApi ANTES de MODELO_SELECTOR / elegirModelo.
import { SITES, MODELOS_WEB, escribe, enviar, leerRespuesta, sesionMuerta, elegirModelo, selectorMuestraOtroModelo, verificarSesionApi } from './sites.js';
import { asegurar, nuevaPagina, cerrarPagina } from './browser.js';
import { partir, cabecera, checkpointLeer, checkpointGuardar, resumeCard, huella } from './bloques.js';
import { cuentaActual } from './cuentas.js';
import { preambulo } from './modos.js';

// convId -> {modelo_verificado} de la última consulta (server lo expone en la respuesta)
export const ultimaVerificacion = new Map();

// consultarWeb(modelo_web, texto, {modo, convId}) -> respuesta del sitio
export async function consultarWeb(modelo, texto, { modo = 'consulta', convId = null } = {}) {
  const cfg = MODELOS_WEB[modelo];
  if (!cfg) throw new Error(`modelo web desconocido: ${modelo}`);
  const site = cfg.site;
  convId = convId || `${site}-${modelo}-${Date.now()}`;
  // cada conv = slot sobre la página maestra del sitio (mutex/cola en browser.js)
  const page = await nuevaPagina(site, convId);
  let ck = null;
  try {
    const siteCfg = SITES[site];
    // Vía 14: profile API ANTES del selector de modelo (401/403 = SESSION_EXPIRED).
    const api = await verificarSesionApi(page, siteCfg).catch(() => ({ ok: true, skipped: true }));
    if (api && api.ok === false && (api.status === 401 || api.status === 403)) {
      throw Object.assign(new Error('SESION_API_EXPIRADA'), {
        code: 'SESSION_EXPIRED', site, motivo: 'SESSION_EXPIRED', api_status: api.status, importar: true });
    }
    // Verificar el modelo REAL; antes se ignoraba silenciosamente un picker fallido
    // y se respondía bajo el ID solicitado aunque el sitio ejecutara otro modelo.
    let elegido = await elegirModelo(page, siteCfg, cfg.modelo_regex);
    // Tras login la SPA puede tardar en pintar el picker: un segundo intento tras hidratar.
    if (!elegido) { await page.waitForTimeout(2500).catch(() => {}); elegido = await elegirModelo(page, siteCfg, cfg.modelo_regex); }
    // Sin selector/indicador visible (DeepSeek no tiene picker; Qwen a veces lo oculta) NO es
    // evidencia de otro modelo: se responde marcado modelo_verificado=false. Solo se bloquea si se
    // VE otro modelo o si BRIDGE_MODELO_ESTRICTO=1.
    const estricto = process.env.BRIDGE_MODELO_ESTRICTO === '1';
    let verificado = !!elegido;
    if (!elegido && (estricto || await selectorMuestraOtroModelo(page, siteCfg, cfg.modelo_regex) === 'otro')) {
      throw Object.assign(new Error('No pude verificar el modelo en el selector de la web'), {
        code:'MODELO_SELECTOR_NO_VERIFICADO', site });
    }
    if (ultimaVerificacion.size > 500) ultimaVerificacion.clear();
    ultimaVerificacion.set(convId, { modelo, site, modelo_verificado: verificado, ts: Date.now() });
    if (!verificado) console.warn(`[motor] ${site}/${modelo}: selector no visible; respuesta marcada modelo_verificado=false`);
    const bloques = partir(`${preambulo(modo)}\n${texto}`);
    const h = huella(texto, modo);
    ck = checkpointLeer(convId, h);
    if (ck && ck.total !== bloques.length) ck = null;  // el checkpoint no es de este texto/modo
    ck = ck || { modo, total: bloques.length, enviados: 0, ultima_salida: '', huella: h };
    const cuenta = (() => { try { return cuentaActual().index; } catch { return null; } })();
    ck = { ...ck, modelo, texto: String(texto).slice(0, 200000) };  // lo necesario para retomar sola, sin que el cliente reenvie nada

    // retomo: reabre la MISMA conversacion web (url del checkpoint) en vez de un chat nuevo; si no abre, sigue con el chat nuevo + tarjeta
    if (ck.enviados > 0 && ck.enviados < ck.total && ck.url && ck.cuenta === cuenta) {  // la URL de otra cuenta no abre
      await page.goto(ck.url, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
    }
    // retomo: si habia checkpoint, aviso al modelo donde ibamos
    if (ck.enviados > 0 && ck.enviados < ck.total) {
      await escribe(page, siteCfg, resumeCard(ck));
      await enviar(page, siteCfg);
      await leerRespuesta(page, siteCfg, { timeoutMs: 60000 });
    }

    for (let i = ck.enviados; i < ck.total; i++) {
      const ok = await escribe(page, siteCfg, cabecera(i + 1, ck.total, modo) + bloques[i]);
      if (!ok) throw Object.assign(new Error('INPUT_NO_ENCONTRADO'), { code: 'SELECTOR_BROKEN', site });
      // El texto que ya estaba en pantalla NO prueba que el modelo respondió.
      const previo = await page.evaluate((sel) => {
        const lista = [...document.querySelectorAll(sel)];
        return lista.length ? String(lista[lista.length - 1].innerText || '') : '';
      }, siteCfg.respuesta.join(',')).catch(() => '');
      await enviar(page, siteCfg);
      let salida;
      try {
        salida = await leerRespuesta(page, siteCfg, { previo, timeoutMs:145000 });
      } catch (e) {
        if (e.code === 'WEB_SALIDA_PARCIAL' && e.texto_parcial) {
          // Preservar lo recibido como PARCIAL, jamás declarar DONE o repetir herramientas.
          checkpointGuardar(convId, { ...ck, ultima_salida:String(e.texto_parcial).slice(0,20000),
            estado:'PARCIAL', completo:false, cuenta, url:page.url() });
        }
        throw e;
      }
      if (sesionMuerta(page, siteCfg)) throw Object.assign(new Error('SESION_MUERTA'), { code: 'SESSION_EXPIRED', site });
      ck = { ...ck, enviados: i + 1, ultima_salida: salida || '', cuenta, url: (() => { try { return page.url(); } catch { return ck.url; } })() };
      checkpointGuardar(convId, ck);
    }
  } finally {
    await cerrarPagina(convId).catch(() => {});  // libera slot maestra; no destruye el contexto
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
