// ventanas-nuevas.js — cablea las ventanas nuevas del chat (cada una en su archivo): workflows, constitución sentinela, banco de claves,
// destinos del anclaje y el contexto que viaja con cada mensaje. Un fallo en una no rompe a las demás ni al chat.
import { instalarContexto } from "./chat-contexto.js";
import { montarDestinos } from "./anclaje-destinos.js";
import { montarHandoffEditor } from "./handoff-editor.js";
import { montarArchivosBorrar } from "./archivos-borrar.js";
import { montarHabilidades } from "./menu-habilidades.js";
import { montarWorkflows } from "./ventana-workflows.js";
import { montarSelectorWorkflows } from "./selector-workflows.js";
import { montarConstitucion } from "./ventana-constitucion.js";
import { montarClaves } from "./ventana-claves.js";
export function conectarVentanasNuevas(ctx) {
  [instalarContexto, montarDestinos, montarHandoffEditor, montarArchivosBorrar, montarHabilidades, montarWorkflows, montarSelectorWorkflows, montarConstitucion, montarClaves].forEach((f) => { try { f(ctx); } catch (e) { console.warn("ventanas-nuevas:", f.name, e); } });
}
