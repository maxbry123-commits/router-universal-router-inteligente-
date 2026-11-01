// Solo se ejecuta después de cargar la página del chat; no modifica la pantalla previa Preparing Space de HF.
export async function comprobarSalud(fetchFn = fetch, signal) {
  const r = await fetchFn("/health", { cache: "no-store", credentials: "same-origin", signal });
  if (!r || !r.ok) return false;
  const d = await r.json();
  return !!(d && d.status === "ok");
}
export function iniciarIndicadorServidor(doc = document, win = window) {
  const panel = doc.querySelector("#panel");
  if (!panel || doc.querySelector("#riu-inicio-servidor")) return;
  const barra = doc.createElement("div"); barra.id = "riu-inicio-servidor";
  barra.setAttribute("role", "status"); barra.setAttribute("aria-live", "polite");
  const giro = doc.createElement("span"); giro.className = "riu-arranque-spinner"; giro.setAttribute("aria-hidden", "true");
  const texto = doc.createElement("span"); texto.className = "riu-arranque-texto";
  const boton = doc.createElement("button"); boton.type = "button"; boton.className = "mini"; boton.textContent = "Comprobar ahora";
  barra.append(giro, texto, boton); panel.before(barra);
  let intentos = 0, comprobando = false, listo = false, temporizador = 0, ocultar = 0;
  const mensaje = valor => { texto.textContent = valor; barra.hidden = false; };
  async function comprobar() {
    if (comprobando) return;
    win.clearTimeout(temporizador); win.clearTimeout(ocultar); comprobando = true;
    mensaje(intentos ? "Comprobando servidor · intento " + (intentos + 1) + "…" : "Conectando al servidor…");
    const ac = new AbortController(), limite = win.setTimeout(() => ac.abort(), 7000);
    try {
      if (await comprobarSalud(win.fetch.bind(win), ac.signal)) {
        intentos = 0; listo = true; mensaje("Servidor listo · chat conectado");
        try { win.dispatchEvent(new CustomEvent("router-connection", { detail: "Router disponible" })); } catch (e) {}
        ocultar = win.setTimeout(() => { barra.hidden = true; }, 2000);
      } else { listo = false; intentos++; mensaje("Servidor iniciándose o con servicios pendientes · reintentando…"); }
    } catch (e) { listo = false; intentos++; mensaje("Sin respuesta del servidor · reintentando automáticamente…"); }
    finally {
      win.clearTimeout(limite); comprobando = false;
      if (!listo && barra.isConnected)
        temporizador = win.setTimeout(comprobar, Math.min(3000 * 2 ** Math.min(intentos - 1, 3), 30000));
    }
  }
  boton.addEventListener("click", () => { if (!comprobando) comprobar(); });
  win.addEventListener("online", () => { if (!comprobando) comprobar(); });
  doc.addEventListener("visibilitychange", () => { if (doc.visibilityState === "visible" && !comprobando) comprobar(); });
  win.addEventListener("router-connection", e => {
    if (listo && (e.detail === "Sin conexión" || e.detail === "Error de Router")) {
      listo = false; intentos = 0; comprobar();
    }
  });
  comprobar();
}
