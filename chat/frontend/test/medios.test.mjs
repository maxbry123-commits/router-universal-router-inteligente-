import test from "node:test";
import assert from "node:assert/strict";

let observar;
const elementos = [];
const burbuja = { dataset: {}, textContent: "", after() {} };
globalThis.document = {
  body: {},
  querySelectorAll: () => [burbuja],
  createElement: (tag) => { const e = { tag, after() {} }; elementos.push(e); return e; },
};
globalThis.MutationObserver = class { constructor(fn) { observar = fn; } observe() {} };
await import("../chat-medios.js");

test("crea audio y enlace HTTPS conservando la firma de la URL TTS HTTP", () => {
  elementos.length = 0;
  burbuja.textContent = "[[audio:http://example.com/voz.mp3?signature=a%2Fb&expires=123]]";
  observar();
  assert.equal(burbuja.textContent, "");
  assert.equal(elementos[0].tag, "audio");
  assert.equal(elementos[0].controls, true);
  assert.equal(elementos[0].src, "https://example.com/voz.mp3?signature=a%2Fb&expires=123");
  assert.equal(elementos[1].href, elementos[0].src);
});

test("conserva medios HTTPS y audio data, sin aceptar esquemas ejecutables", () => {
  for (const [tipo, url] of [["imagen", "https://example.com/foto.png"], ["video", "https://example.com/video.mp4"], ["audio", "data:audio/mp3;base64,AAAA"]]) {
    elementos.length = 0; burbuja.textContent = `[[${tipo}:${url}]]`; observar();
    assert.equal(elementos[0].tag, tipo === "imagen" ? "img" : tipo);
    assert.equal(elementos[0].src, url);
  }
  elementos.length = 0; burbuja.textContent = "[[audio:javascript:alert(1)]]"; observar();
  assert.equal(elementos.length, 0);
  assert.equal(burbuja.textContent, "[[audio:javascript:alert(1)]]");
});
