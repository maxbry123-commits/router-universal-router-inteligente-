// chat-riu2.js — resto de componentes RUI del skill (12, 13, 14, 15, 17, 18, 19, 21, 04, 05, 02) llevados a JS simple
// + mejoras de flujo (ventanas accesibles, borrador, campo que crece, aviso sin conexion). Archivo propio, solo frontend, datos reales:
// nada se inventa; lo que muestra sale del chat, del historial local y de los avisos reales.
// Componentes en riu-campana.js, riu-navegacion.js, riu-chats.js, riu-reacciones.js, riu-paneles.js, riu-entrada.js; utilidades en riu-util.js.
import { seguro } from "./riu-util.js";
import { campana } from "./riu-campana.js";
import { navegacion, sinConexion, orbeConexion } from "./riu-navegacion.js";
import { cerrarChats, contadorAncla } from "./riu-chats.js";
import { reacciones, reproductor } from "./riu-reacciones.js";
import { colaMotor, actividad, carpetaVacia } from "./riu-paneles.js";
import { bienvenida, buscadores, ventanasA11y, entrada, soltarArchivos } from "./riu-entrada.js";
export function conectarRiu2(ctx) {
  [campana, navegacion, sinConexion, orbeConexion].forEach((f) => seguro(f));
  [cerrarChats, contadorAncla, reacciones, reproductor, colaMotor, actividad, buscadores, carpetaVacia, bienvenida, soltarArchivos, ventanasA11y, entrada].forEach((f) => seguro(f, ctx));
}
