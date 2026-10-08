// chat-archivos.js — Punto 4: archivos persistentes del chat ACTIVO (rutas /chat/files/{sesion} del Router).
// Subir (base64, límite revisado antes de enviar), listar, descargar, borrar con confirmación y anclar.
// Los nombres anclados se guardan por chat y viajan como `anclados` en los siguientes mensajes.
import { api, node } from "../api.js";
import { anclados, fijarAnclados } from "./chat-sesion.js";

const LIMITE_B64 = 4_000_000;                      // el Router rechaza datos_b64 mayores (413)
const MAX_BYTES = Math.floor(LIMITE_B64 * 3 / 4);  // ≈ 3 MB de datos reales
const NOMBRE_MALO = /[/\\\u0000-\u001f\u007f]|\.\./;
const ERRORES = {
  ARCHIVO_MUY_GRANDE: "El archivo supera el límite del Router (unos 3 MB).",
  NOMBRE_INVALIDO: "Nombre no válido: 1 a 120 caracteres, sin / \\ .. ni caracteres de control.",
  BASE64_INVALIDO: "El Router no pudo leer el archivo codificado (base64 inválido).",
  ARCHIVO_NO_EXISTE: "El archivo ya no existe en este chat.",
  SESION_INVALIDA: "La sesión de este chat no es válida.",
  "Not Found": "El Router todavía no tiene la ruta de archivos.",
  "Failed to fetch": "Sin conexión con el Router.",
  "HTTP 413": "El archivo supera el límite del Router (unos 3 MB).",
  "HTTP 422": "Datos no válidos para el Router.",
};
const enEspanol = error => ERRORES[error?.message] || `Error del Router: ${error?.message || "desconocido"}`;
const tamano = b => b < 1000 ? `${b} B` : b < 1e6 ? `${(b / 1e3).toFixed(1)} KB` : `${(b / 1e6).toFixed(2)} MB`;  // unidades decimales, como el límite
const fecha = ts => {
  const n = Number(ts);
  const d = new Date(Number.isFinite(n) ? (n < 1e12 ? n * 1000 : n) : ts);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" });
};
const ruta = (sesion, fileId) => `/chat/files/${encodeURIComponent(sesion)}${fileId ? "/" + encodeURIComponent(fileId) : ""}`;

function leerBase64(archivo) {
  return new Promise((ok, falla) => {
    const lector = new FileReader();
    lector.onload = () => ok(String(lector.result).replace(/^data:[^,]*,/, ""));
    lector.onerror = () => falla(new Error("No se pudo leer el archivo del equipo."));
    lector.readAsDataURL(archivo);
  });
}

export function montarArchivos({ activoId }) {
  const $ = s => document.querySelector(s);
  const estado = (texto, error = false) => { $("#archivos-estado").textContent = texto; $("#archivos-estado").dataset.error = String(error); };
  let lista = [];

  function pintar(sesion) {
    const fijos = new Set(anclados(sesion));
    $("#archivos-titulo").textContent = `Archivos de este chat (${lista.length})${fijos.size ? ` · ${fijos.size} anclado${fijos.size > 1 ? "s" : ""}` : ""}`;
    $("#archivos-lista").replaceChildren(...lista.map(f => {
      const fila = node("li", "", "item archivo");
      const boton = (texto, titulo, accion) => {
        const b = node("button", texto, "secondary");
        b.type = "button"; b.title = titulo;
        b.addEventListener("click", () => void accion(b));
        return b;
      };
      const pin = boton(fijos.has(f.nombre) ? "Anclado" : "Anclar", "Enviar este archivo como contexto en los próximos mensajes", () => {
        const actual = new Set(anclados(sesion));
        actual.has(f.nombre) ? actual.delete(f.nombre) : actual.add(f.nombre);
        fijarAnclados(sesion, [...actual]);
        pintar(sesion);
      });
      pin.setAttribute("aria-pressed", String(fijos.has(f.nombre)));
      fila.append(node("span", f.nombre, "nombre"), node("small", `${tamano(Number(f.bytes) || 0)} · ${fecha(f.ts)}`, "muted"),
        pin, boton("Descargar", `Descargar ${f.nombre}`, () => descargar(sesion, f)),
        boton("Borrar", `Borrar ${f.nombre}`, () => borrar(sesion, f)));
      return fila;
    }));
  }

  async function cargar(sesion) {
    if (activoId() === sesion) { lista = []; pintar(sesion); estado("Cargando archivos…"); }
    try {
      const r = await api(ruta(sesion));
      if (activoId() !== sesion) return;
      lista = Array.isArray(r?.files) ? r.files : [];
      const nombres = new Set(lista.map(f => f.nombre));
      fijarAnclados(sesion, anclados(sesion).filter(n => nombres.has(n)));  // el Router manda: sin archivo no hay ancla
      pintar(sesion);
      estado(lista.length ? "" : "Sin archivos en este chat.");
    } catch (error) {
      if (activoId() === sesion) estado(`No se pudieron cargar los archivos: ${enEspanol(error)}`, true);
    }
  }

  async function subir(archivo) {
    const sesion = activoId();
    const nombre = archivo.name;
    if (!nombre || nombre.length > 120 || NOMBRE_MALO.test(nombre)) return estado(ERRORES.NOMBRE_INVALIDO, true);
    if (archivo.size > MAX_BYTES) return estado(`«${nombre}» pesa ${tamano(archivo.size)}: ${ERRORES.ARCHIVO_MUY_GRANDE}`, true);
    $("#archivos-subir").disabled = true;
    estado(`Subiendo «${nombre}»…`);
    try {
      const datos_b64 = await leerBase64(archivo);
      if (datos_b64.length > LIMITE_B64) throw new Error("ARCHIVO_MUY_GRANDE");
      const r = await api(ruta(sesion), { method: "POST", body: { nombre, ...(archivo.type ? { tipo: archivo.type } : {}), datos_b64 } });
      await cargar(sesion);
      if (activoId() === sesion) estado(`Subido «${r.nombre || nombre}» (${tamano(Number(r.bytes) || archivo.size)}).`);
    } catch (error) {
      if (activoId() === sesion) estado(`No se pudo subir «${nombre}»: ${enEspanol(error)}`, true);
    } finally { $("#archivos-subir").disabled = false; }
  }

  async function descargar(sesion, f) {
    try {
      await api(ruta(sesion));  // refresca la dirección viva del Router (LIVE_URL) antes de pedir los bytes
      const headers = {};
      const clave = sessionStorage.getItem("riu_clave");
      if (clave) headers[window.RIU_CONFIG?.authHeader || "X-API-Key"] = clave;
      const base = String(window.RIU_CONFIG?.apiBase || "").replace(/[/]+$/, "");
      const r = await fetch(base + ruta(sesion, f.file_id), { headers, credentials: "omit" });
      if (!r.ok) {
        const detalle = (await r.json().catch(() => ({}))).detail;
        throw new Error(typeof detalle === "string" ? detalle : `HTTP ${r.status}`);
      }
      const url = URL.createObjectURL(await r.blob());
      const enlace = Object.assign(document.createElement("a"), { href: url, download: f.nombre });
      document.body.append(enlace); enlace.click(); enlace.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      estado(`Descargado «${f.nombre}».`);
    } catch (error) { estado(`No se pudo descargar «${f.nombre}»: ${enEspanol(error)}`, true); }
  }

  async function borrar(sesion, f) {
    if (!window.confirm(`¿Borrar «${f.nombre}» de este chat? Se eliminan todas sus versiones en el Router.`)) return;
    try {
      const r = await api(ruta(sesion, f.file_id), { method: "DELETE" });
      fijarAnclados(sesion, anclados(sesion).filter(n => n !== f.nombre));
      await cargar(sesion);
      if (activoId() === sesion) estado(`Borrado «${r.nombre || f.nombre}» (${r.versions ?? 1} versión/es).`);
    } catch (error) { estado(`No se pudo borrar «${f.nombre}»: ${enEspanol(error)}`, true); }
  }

  $("#archivos-subir").addEventListener("click", () => $("#archivos-input").click());
  $("#archivos-input").addEventListener("change", event => {
    const archivo = event.target.files?.[0];
    event.target.value = "";
    if (archivo) void subir(archivo);
  });
  return { cargar };
}
