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
import { montarHistorialPersistente } from "./chat-historial-db.js";
import { instalarContextoFichas } from "./chat-contexto-fichas.js";
import { instalarGuardSelector } from "./chat-selector-guard.js";
import { instalarRecuperacionProcesos } from "./chat-proceso-recovery.js";
import { instalarFastVisual } from "./chat-fast-visual.js";
import { instalarSelectorPorSesion } from "./chat-selector-por-sesion.js";
import { montarNotas } from "./notas-ventana.js";
import { instalarAuth, montarAcceso } from "./acceso-clave.js";
export function conectarVentanasNuevas(ctx) {
  [
    instalarContexto,
    instalarAuth,
    montarHistorialPersistente,
    instalarContextoFichas,
    instalarGuardSelector,
    instalarRecuperacionProcesos,
    instalarFastVisual,
    instalarSelectorPorSesion,
    montarDestinos,
    montarMejorasAncla,
    montarHandoffEditor,
    montarAgregarAlChat,
    montarArchivosBorrar,
    montarHabilidades,
    montarWorkflows,
    montarSelectorWorkflows,
    montarConstitucion,
    montarClaves,
    montarAcceso,
    montarPensando3D,
    montarNotas,
  ].forEach((f) => { try { f(ctx); } catch (e) { console.warn("ventanas-nuevas:", f.name, e); } });
}
