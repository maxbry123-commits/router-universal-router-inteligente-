// Chat2: regresión de salida del chat y cubo 3D, sin motores ni dependencias nuevas.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const src=f=>readFileSync(new URL('../'+f,import.meta.url),'utf8');
test('pensamiento existe solo en el historial visible, nunca entre botones',()=>{
 const js=src('pensando-3d.js'),css=src('pensando-3d.css');
 assert.match(js,/hist\.querySelectorAll\("\.chat-history"\)/);
 assert.match(js,/target\.append\(w\)/);
 assert.doesNotMatch(js,/barra\.insertBefore\(w/);
 assert.match(css,/#histories \.chat-history > \.p3d/);
 assert.doesNotMatch(css,/composer-bar>\.p3d/);
});
test('salida tiene altura mínima móvil y no pierde el área de escritura',()=>{
 const css=src('chat-espacio.css');
 assert.match(css,/height:calc\(100dvh - var\(--chat-top/);
 assert.match(css,/padding:8px 6px 44px 6px !important/);
 assert.match(css,/#composer\{\s*flex:0 0 auto !important/);
 assert.match(css,/max-width:100%/);
});
test('solo hay flecha de bajar en el historial, sin nuevo flotando a mitad del chat',()=>{
 const js=src('chat-riu.js'),panel=src('panel-chat.js');
 assert.match(js,/bajar\.hidden = false/);
 assert.match(js,/h\.scrollTo\(\{ top: h\.scrollHeight/);
 assert.doesNotMatch(js,/const subir = document\.createElement/);
 assert.doesNotMatch(panel,/btn-nuevo-abajo/);
 assert.doesNotMatch(panel,/↓ nuevo/);
});
test('selector NVIDIA, Groq y agentes siguen intactos',()=>{
 const ui=src('selector-modelos.js'),sel=src('panel-chat.html');
 assert.doesNotMatch(ui,/modelo-unificado/);
 for(const id of ['sel-ngt','sel-groq','sel-swe','sel-swen','btn-agentes-swe'])
  assert.match(sel,new RegExp('id="'+id+'"'));
});
