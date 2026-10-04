import { createWall } from "./wall/view.js";
import { loadWallState } from "./wall/state.js";

let wallState = null;

export function renderWall(context) {
  const section = document.createElement("section");
  section.className = "panel wall";
  section.dataset.panel = "wall";
  section.innerHTML = `
    <header class="wall-hdr">
      <div class="wall-k">PLANO ÚNICO · PLAN_100 + 6 RAÍCES · <span id="wall-ver">v2</span></div>
      <h1>Raíz Wordflow YAIWES</h1>
      <div class="wall-hilo">
        <span>INPUT</span><i>→</i><span>MISIÓN</span><i>→</i>
        <span>KERNEL</span><i>→</i><span>WORDFLOW</span><i>→</i>
        <span>EVIDENCIA</span><i>→</i><span>OUT</span>
      </div>
      <div class="wall-modes">
        <button type="button" id="wall-mfile" data-wall-mode="file">Tap archivo</button>
        <button type="button" id="wall-mblock" data-wall-mode="block">Tap bloque</button>
      </div>
      <div class="wall-legend">
        <span><b style="background:var(--verde)"></b>cerrado</span>
        <span><b style="background:var(--amarillo)"></b>pendiente</span>
        <span><b style="background:var(--naranja)"></b>mix/plugins</span>
        <span><b style="background:var(--rojo)"></b>faltante</span>
      </div>
    </header>
    <div class="wall-plane">
      <h2>6 raíces autorizadas</h2>
      <div class="wall-tree" id="wall-six"></div>
      <h2>agente-yaiwes/ · árbol definitivo</h2>
      <div class="wall-tree" id="wall-yai"></div>
      <h2>extensions/wordflow/ · R6 vivo</h2>
      <div class="wall-tree" id="wall-wf"></div>
      <h2>raíces añadidas</h2>
      <div class="wall-tree" id="wall-extra"></div>
    </div>
    <div class="wall-add">
      <div class="wall-k">AÑADIR RAÍZ · solo bloque segmentado</div>
      <select id="wall-clone">
        <option value="R5">Plantilla Yaiwes wordflow/</option>
        <option value="R1">Desplegar/</option>
        <option value="R2">PIPELINE/</option>
        <option value="R3">Método/</option>
        <option value="R4">Refactoria/</option>
        <option value="R6">Wordflow Code/</option>
        <option value="EMPTY">Vacía</option>
      </select>
      <input id="wall-ntitle" placeholder="Nombre raíz nueva">
      <textarea id="wall-nmd" rows="3" placeholder="Pega markdown de la raíz"></textarea>
      <button type="button" data-wall-add="1">Crear raíz-bloque</button>
    </div>
    <div class="wall-bar">
      <button type="button" data-wall-save="1">Guardar estado</button>
      <button type="button" class="wall-g" data-wall-sharesel="1">Compartir</button>
    </div>
    <div class="wall-sheet" id="wall-sheet"><div class="wall-box" id="wall-sheetbox"></div></div>
    <div class="wall-toast" id="wall-toast"></div>`;
  if (!wallState) wallState = loadWallState();
  createWall(section, context, wallState);
  return section;
}
