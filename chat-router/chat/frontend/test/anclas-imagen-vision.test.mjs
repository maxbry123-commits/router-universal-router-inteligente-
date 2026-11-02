import test from "node:test";
import assert from "node:assert/strict";
import { armar, enviarSwe } from "../swe-directo.js";
import { prepararImagenOArchivo, MAX_ARCHIVO_CHAT } from "../imagen-subida.js";

test("SWE/Groq/NVIDIA transporta los píxeles de las anclas como image_url real", async () => {
  const url = "data:image/png;base64,iVBORw0KGgo=";
  const datos = { model: "nvidia/z-ai/glm-5.3", mensaje: "Describe la fotografía", sesion: "s1", imagenes: [{nombre:"foto.png",url}] };
  const req = armar(datos), partes = req.messages.at(-1).content;
  assert.equal(req.conv_id, "s1");
  assert.deepEqual(partes, [{ type:"text",text:"Describe la fotografía" },{ type:"image_url",image_url:{ url } }]);
  let recibido;
  await enviarSwe(async (_ruta,opts) => {
    recibido = opts.body.messages.at(-1).content;
    return { choices:[{ message:{ content:"respuesta" },finish_reason:"stop" }] };
  },datos);
  assert.deepEqual(recibido, partes);
});

test("sin fotografías mantiene el texto literal; rechaza imágenes externas no verificadas", () => {
  const txt = armar({model:"groq/qwen/qwen3.8-27b",mensaje:"texto exacto",sesion:"x"});
  assert.equal(txt.messages.at(-1).content,"texto exacto");
  const invalido=armar({model:"groq/qwen/qwen3.8-27b",mensaje:"texto",sesion:"x",
    imagenes:[{url:"https://servidor-no-autorizado/prueba.png"}]});
  assert.equal(invalido.messages.at(-1).content,"texto");
});

test("el límite local corresponde al almacén real (700000 bytes)", async () => {
  const pequeno={name:"foto.png",size:10,type:"image/png"};
  assert.equal(await prepararImagenOArchivo(pequeno),pequeno);
  await assert.rejects(() => prepararImagenOArchivo({name:"codigo.zip",type:"application/zip",size:MAX_ARCHIVO_CHAT+1}), /700 KB/);
});
