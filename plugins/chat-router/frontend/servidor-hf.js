// servidor-hf.js — Botones de control del Space HF en Configuración
// Llama a la API de Hugging Face (restart / status). Requiere token HF con permiso write.
import { el, boton, cargarCss } from "./ventanas-comun.js";

const SPACE = "comand-center-1-riu-router"; // ajusta si el nombre real es otro
const OWNER = "maxbry123-commits";          // ajusta al owner real del Space

const HF_TOKEN_KEY = "riu_hf_token";

function getToken() {
  try { return sessionStorage.getItem(HF_TOKEN_KEY) || ""; } catch { return ""; }
}
function setToken(t) {
  try { if (t) sessionStorage.setItem(HF_TOKEN_KEY, t); else sessionStorage.removeItem(HF_TOKEN_KEY); } catch {}
}

async function hfCall(method, path, body) {
  const token = getToken();
  if (!token) throw new Error("Falta token de Hugging Face. Pégalo arriba y guarda.");
  const r = await fetch("https://huggingface.co/api" + path, {
    method,
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const txt = await r.text();
  let data; try { data = JSON.parse(txt); } catch { data = { raw: txt }; }
  if (!r.ok) throw new Error(data.error || data.message || txt || ("HTTP " + r.status));
  return data;
}

export function montarServidorHF(root, { avisa }) {
  const caja = root.querySelector("#ap-servidor") || root.querySelector("#ap-acceso");
  if (!caja) return;
  if (caja.dataset.srv) return;
  caja.dataset.srv = "1";

  const seccion = el("div", "vn-seccion");
  seccion.append(el("strong", "", "Servidor HF (Space)"));

  const tok = el("input", "vn-in");
  tok.type = "password";
  tok.placeholder = "Token HF (write) — solo en este navegador";
  tok.value = getToken();
  tok.setAttribute("aria-label", "Token Hugging Face");

  const filaTok = el("div", "ac-acc");
  filaTok.append(
    boton("Guardar token", "mini", () => { setToken(tok.value.trim()); avisa("Token HF guardado"); }),
    boton("Borrar token", "mini rojo", () => { setToken(""); tok.value = ""; avisa("Token borrado"); })
  );

  const est = el("div", "vn-estado");
  est.setAttribute("role", "status");

  const fila = el("div", "ac-acc");
  fila.append(
    boton("Estado", "mini", async () => {
      est.textContent = "Consultando…";
      try {
        const s = await hfCall("GET", `/spaces/${OWNER}/${SPACE}`);
        est.textContent = "Estado: " + (s.runtime?.stage || s.status || "desconocido");
      } catch (e) { est.textContent = "Error: " + e.message; }
    }),
    boton("Reiniciar", "mini", async () => {
      est.textContent = "Reiniciando…";
      try {
        await hfCall("POST", `/spaces/${OWNER}/${SPACE}/restart`);
        est.textContent = "Reinicio enviado. Espera ~30-60 s y prueba el chat.";
        avisa("Reinicio solicitado");
      } catch (e) { est.textContent = "Error: " + e.message; }
    }),
    boton("Pausar (sleep)", "mini", async () => {
      est.textContent = "Pausando…";
      try {
        await hfCall("POST", `/spaces/${OWNER}/${SPACE}/pause`);
        est.textContent = "Pausa solicitada.";
        avisa("Pausa solicitada");
      } catch (e) { est.textContent = "Error: " + e.message; }
    })
  );

  seccion.append(tok, filaTok, fila, est, el("div", "vn-estado", "El token solo se guarda en este navegador. Reiniciar despierta un Space dormido."));
  caja.append(seccion);
}
