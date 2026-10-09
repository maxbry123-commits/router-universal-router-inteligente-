// chat-cableado.js — engancha al chat cableado (panel-chat.js) los puntos del Director, cada uno en su módulo.
// Todo pasa por el mismo Router de LIVE_URL.json (api.js): rutas /chat/* y el puente puente_chat. Sin claves aquí.
import { conectarAislado } from "./chat-aislado.js";
import { conectarHistorial } from "./chat-historial.js";
import { conectarArchivos } from "./chat-archivos.js";
import { conectarAgenteHijo } from "./chat-agente-hijo.js";
import { conectarOrquestador } from "./chat-orquestador.js";
import { conectarSelectorModelos } from "./chat-selector-modelos.js";

export function conectar(ctx) {
  const pasos = [conectarAislado, conectarHistorial, conectarArchivos, conectarAgenteHijo, conectarOrquestador, conectarSelectorModelos];
  for (const paso of pasos) {
    try { paso(ctx); } catch (error) { ctx.tell("GAP " + paso.name + ": " + error.message); }
  }
}
