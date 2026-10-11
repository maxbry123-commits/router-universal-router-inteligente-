// archivos-borrar.js — borrar UN archivo de la lista (ventana de Anclaje y ventana Archivos). Se quita de la lista y de todo lo anclado;
// si el servidor tiene la acción archivo_borrar, también se borra allí. La marca de borrado se limpia al volver a subir el mismo nombre.
import { leer, escribir, KEYS } from "./almacen.js";
import { el, boton } from "./ventanas-comun.js";
const K = "riu_archivos_borrados_v1", unico = (a) => [...new Set(a)];
const ses = () => { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return c ? c.sesion : "general"; };
const marcados = () => { const t = leer(K, {}), l = t[ses()]; return Array.isArray(l) ? l : []; };
const marcar = (n, on) => { const t = leer(K, {}), s = ses(), l = Array.isArray(t[s]) ? t[s] : []; t[s] = on ? unico([...l, n]) : l.filter((x) => x !== n); escribir(K, t); };
export function quitarDeTodo(nombre) {  // lo borrado deja de estar anclado en cualquier objetivo
  const c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (c) { c.anclados.delete(nombre); try { window.RIU_CHAT.pintar(); } catch (e) {} }
  const con = Object.assign({ items: [] }, leer(KEYS.constitucion, {})); if ((con.items || []).includes(nombre)) { con.items = con.items.filter((x) => x !== nombre); escribir(KEYS.constitucion, con); }
  const wf = leer(KEYS.workflows, { lista: [] }); let cw = false; (wf.lista || []).forEach((w) => { if ((w.items || []).includes(nombre)) { w.items = w.items.filter((x) => x !== nombre); cw = true; } }); if (cw) escribir(KEYS.workflows, wf);
  [KEYS.agentes, KEYS.sandbox].forEach((k) => { const s = leer(k, null); if (s && (s.items || []).includes(nombre)) { s.items = s.items.filter((x) => x !== nombre); escribir(k, s); } });
  const pr = leer("riu_proy_v1", {}); let cp = false; Object.keys(pr).forEach((k) => (Array.isArray(pr[k]) ? pr[k] : []).forEach((p) => { if ((p.items || []).includes(nombre)) { p.items = p.items.filter((x) => x !== nombre); cp = true; } })); if (cp) escribir("riu_proy_v1", pr);
}
export function montarArchivosBorrar({ root, q, tell }) {
  const adj = q("#adjunto"); if (adj && !adj.dataset.borr) { adj.dataset.borr = "1"; adj.addEventListener("change", () => [...(adj.files || [])].forEach((f) => marcar(f.name, false))); }
  ["#anc-lista", "#va-lista"].forEach((sel) => {
    const lista = q(sel); if (!lista || lista.dataset.borrar) return; lista.dataset.borrar = "1";
    const borrar = async (nombre, fila) => {
      if (!confirm("¿Borrar el archivo «" + nombre + "»? Se quita de la lista y de todo lo anclado.")) return;
      quitarDeTodo(nombre); marcar(nombre, true); fila.style.display = "none";
      try { await window.RIU_ACCION("archivo_borrar", { nombre, sesion: ses() }); tell("Archivo borrado: " + nombre); }
      catch (e) { tell("Archivo quitado de la lista: " + nombre + " (el servidor aún no borra el original)"); }
    };
    const aplicar = () => {
      const bor = marcados();
      [...lista.children].forEach((fila) => {
        const nom = fila.querySelector && fila.querySelector(".fila-nom"); if (!nom) return; const nombre = nom.textContent.trim();
        if (bor.includes(nombre)) { fila.style.display = "none"; return; }
        fila.style.display = ""; if (fila.querySelector(".va-borrar")) return;
        const b = boton("✕", "mini va-borrar", () => borrar(nombre, fila)); b.title = "Borrar este archivo"; b.setAttribute("aria-label", "Borrar " + nombre); fila.append(b);
      });
    };
    let p = 0; new MutationObserver(() => { if (!p) p = requestAnimationFrame(() => { p = 0; aplicar(); }); }).observe(lista, { childList: true }); aplicar();
  });
}
