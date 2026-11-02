// Chat2: regresión de salida del chat y cubo 3D, sin motores ni dependencias nuevas.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const src=f=>readFileSync(new URL('../'+f,import.meta.url),'utf8');
test('pensamiento junto a Enviar, no en el historial',()=>{
 const js=src('pensando-3d.js'),css=src('pensando-3d.css');
 assert.match(js,/barra\.insertBefore\(w, enviar\)/);
 assert.match(js,/barra\.querySelector\("\.action"\)/);
 assert.doesNotMatch(js,/target\.append\(w\)/);
 assert.match(css,/#composer \.composer-bar > \.p3d/);
 assert.doesNotMatch(css,/#histories \.chat-history > \.p3d/);
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
 for(const id of ['sel-ngt','sel-groq','sel-swe','sel-swen'])
  assert.match(sel,new RegExp('id="'+id+'"'));
 assert.doesNotMatch(sel,/id="btn-agentes-swe"/);
});
