// No accede a Hugging Face ni a claves reales; usa la ruta REAL del cliente YAIWES.
// Una sola petición, un solo mensaje y un único [DONE] de un modelo HF.
// En el DOM, enviar-mensaje.js sustituye el parcial por la burbuja final.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { enviarSwe, rutaSwe } from '../swe-directo.js';

const respuestaSSE = (texto) => {
  const eventos = [
    { choices: [{ index:0, delta:{role:'assistant',content:''}, finish_reason:null }] },
    { choices: [{ index:0, delta:{content:texto.slice(0,4)}, finish_reason:null }] },
    { choices: [{ index:0, delta:{content:texto.slice(4)}, finish_reason:null }] },
    { choices: [{ index:0, delta:{}, finish_reason:'stop' }] },
  ];
  return { __sse: { body:null,
    text: async () => eventos.map(x => 'data: ' + JSON.stringify(x) + '\n\n').join('') + 'data: [DONE]\n\n' } };
};

test('YAIWES HF local: SSE con 2 deltas = una sola respuesta; va siempre por Harness', async () => {
  const llamadas=[];
  const result=await enviarSwe(async (ruta,{body}) => {
    llamadas.push({ ruta, body });
    return respuestaSSE('HF RESPONDE');
  }, { model:'hf-liquid-lfm25', mensaje:'Hola', historial:[], sesion:'test-sin-secreto',
    modo:'', ejecutor_tools:'swe' });
  assert.equal(llamadas.length,1);
  assert.equal(llamadas[0].ruta, '/plugins/deepseek_harness/modelos/v1/chat/completions');
  assert.equal(llamadas[0].body.model,'lfm2.5-350m');
  assert.equal(llamadas[0].body.stream,true);
  assert.equal(result.reply,'HF RESPONDE');
  assert.equal(result.finish_reason,'stop');
});

test('YAIWES no añade segundo globo por procedencia del proveedor',()=>{
  const src=readFileSync(new URL('../enviar-mensaje.js', import.meta.url),'utf8');
  assert.match(src,/pending\.remove\(\);/);
  assert.match(src,/respuesta\.dataset\.procedencia = answer\.nota/);
  assert.doesNotMatch(src,/if \(answer\.nota\) c\.hist\.append\(node/);
  assert.equal(rutaSwe('hf/lfm2.5-350m'), '/plugins/deepseek_harness/modelos/v1/chat/completions');
});
