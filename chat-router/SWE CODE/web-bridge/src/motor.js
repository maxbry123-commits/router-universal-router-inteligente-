// motor.js — el canal cableado: escribe bloques, lee salida, checkpoint, reintento
import { SITES, MODELOS_WEB, escribe, enviar, leerRespuesta, sesionMuerta, elegirModelo } from './sites.js';
import { asegurar, nuevaPagina, cerrarPagina } from './browser.js';
import { partir, cabecera, checkpointLeer, checkpointGuardar, resumeCard, huella } from './bloques.js';
import { cuentaActual } from './cuentas.js';
import { preambulo } from './modos.js';

// consultarWeb(modelo_web, texto, {modo, convId}) -> respuesta del sitio
export async function consultarWeb(modelo, texto, { modo = 'consulta', convId = null } = {}) {
  const cfg = MODELOS_WEB[modelo];
  if (!cfg) throw new Error(`modelo web desconocido: ${modelo}`);
  const site = cfg.site;
  convId = convId || `${site}-${modelo}-${Date.now()}`;
  // cada conv = su propio tab + chat nuevo (tareas en paralelo, separadas)
  const page = await nuevaPagina(site, convId);
  let ck = null;
  try {
    const siteCfg = SITES[site];
    // Verificar el modelo REAL; antes se ignoraba silenciosamente un picker fallido
    // y se respondía bajo el ID solicitado aunque el sitio ejecutara otro modelo.
    const elegido = await elegirModelo(page, siteCfg, cfg.modelo_regex);
    if (siteCfg.model_selector?.length && !elegido) {
      throw Object.assign(new Error('No pude verificar el modelo en el selector de la web'), {
        code:'MODELO_SELECTOR_NO_VERIFICADO', site });
    }
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
    await cerrarPagina(convId).catch(() => {});  // la tab se libera siempre: el checkpoint guarda la URL para retomar
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
