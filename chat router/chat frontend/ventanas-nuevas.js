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
import { montarMejorasAncla } from "./anclaje-mejoras.js";
import { montarAgregarAlChat } from "./agregar-al-chat.js";
import { montarPensando3D } from "./pensando-3d.js";
import { montarNotas } from "./notas-ventana.js";
import { instalarAuth, montarAcceso } from "./acceso-clave.js";
import { montarWatchdog } from "./watchdog-avisos.js";
export function conectarVentanasNuevas(ctx) {
  [instalarContexto, instalarAuth, montarDestinos, montarMejorasAncla, montarHandoffEditor, montarAgregarAlChat, montarArchivosBorrar, montarHabilidades, montarWorkflows, montarSelectorWorkflows, montarConstitucion, montarClaves, montarAcceso, montarPensando3D, montarNotas, montarWatchdog].forEach((f) => { try { f(ctx); } catch (e) { console.warn("ventanas-nuevas:", f.name, e); } });
}
