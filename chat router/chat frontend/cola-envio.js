// cola-envio.js — "escribir sin esperar": mientras una respuesta corre, la caja sigue activa; lo que envías queda EN COLA
// (visible en el hilo con la etiqueta "en cola") y sale en orden, uno a uno, apenas termina la respuesta actual.
// Cola y no turnos simultáneos: el Router guarda un proceso por sesión (riu_proc_v1 / AGENTE_OCUPADO), así que es lo seguro.
// Detener sigue aparte: corta la respuesta actual y vacía la cola (quien llama devuelve esos textos a la caja: nada se pierde).
// Uso: const cola = crearCola({ ocupado: () => bool, enviar: (item) => void });  cola.poner({ texto, el }) ; al terminar: cola.siguiente()
export function crearCola({ ocupado, enviar }) {
  const items = [];
  let tic = null;
  const cola = {
    items,
    get length() { return items.length; },
    poner(item) {  // true = quedó en cola; false = salió ya (no había nada corriendo ni esperando)
      if (!ocupado() && !items.length) { enviar(item); return false; }
      items.push(item); if (item.el) marcarEnCola(item.el, true);
      return true;
    },
    siguiente() {  // llamar cuando termina (bien, con error o detenida) la respuesta en curso
      clearTimeout(tic);
      for (const x of items) if (x.el && x.el.parentNode) x.el.parentNode.append(x.el);  // ya mismo (antes de pintar): lo que sigue en cola queda debajo de la última respuesta
      tic = setTimeout(() => {  // un tick: deja pintar la respuesta que acaba de llegar antes de lanzar la siguiente
        if (ocupado() || !items.length) return;
        const x = items.shift(); if (x.el) marcarEnCola(x.el, false);
        enviar(x);
      }, 0);
    },
    vaciar() { clearTimeout(tic); const out = items.splice(0); out.forEach((x) => { if (x.el) x.el.remove(); }); return out; },
  };
  return cola;
}
export function marcarEnCola(el, on) {
  estilo();
  el.classList.toggle("en-cola", !!on);
  let t = el.querySelector(":scope > .tag-cola");
  if (on && !t) { t = document.createElement("span"); t.className = "tag-cola"; t.textContent = "en cola"; el.append(t); }
  if (!on && t) t.remove();
}
// para hilos que pintan varias cosas por turno (ROOM): mete el nodo ANTES del primer mensaje en cola (si no hay cola, al final)
export function antesDeCola(hist, nodo) { hist.insertBefore(nodo, hist.querySelector(":scope > .en-cola")); return nodo; }
// devuelve los textos que estaban en cola a la caja (Detener): nada se pierde
export function devolverACaja(input, textos) {
  if (!input || !textos.length) return;
  const v = input.value.trim();
  input.value = [...textos, ...(v ? [v] : [])].join("\n\n");
  input.dispatchEvent(new Event("input", { bubbles: true }));
}
function estilo() {
  if (document.getElementById("cola-envio-css")) return;
  const s = document.createElement("style"); s.id = "cola-envio-css";
  s.textContent = ".en-cola{opacity:.62}.tag-cola{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;font-size:11px;line-height:16px;border:1px dashed currentColor;vertical-align:middle;white-space:nowrap}";
  document.head.append(s);
}
