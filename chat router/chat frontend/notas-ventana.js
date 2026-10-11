// notas-ventana.js — una sección de NOTAS distinta en cada ventana (y distinta por objetivo en Anclaje). Se guardan solas en este navegador; no viajan con los mensajes.
import { leer, escribir } from "./almacen.js";
import { el, boton } from "./ventanas-comun.js";
const K = "riu_notas_v1";
export function montarNotas({ root, q, tell }) {
  const claveDe = (s) => (s.id === "ventana-ancla" ? "ventana-ancla:" + ((window.RIU_OBJETIVO_ANCLA && window.RIU_OBJETIVO_ANCLA().sesion) || "chat") : s.id);
  const guardar = (s, t) => { const v = leer(K, {}); if (t) v[claveDe(s)] = t.slice(0, 20000); else delete v[claveDe(s)]; escribir(K, v); };
  const equipar = (s) => {
    const caja = s.querySelector(".va-caja"); if (!caja) return;
    let sec = caja.querySelector(".nv-notas");
    if (!sec) {
      sec = el("div", "vn-sec nv-notas"); const ta = el("textarea", "vn-ta nv-ta"), info = el("div", "vn-estado"), fila = el("div", "vn-fila");
      ta.rows = 3; ta.placeholder = "Notas de esta ventana… (solo para ti, se guardan solas)"; ta.setAttribute("aria-label", "Notas de " + (s.getAttribute("aria-label") || s.id));
      let t = 0; ta.addEventListener("input", () => { info.textContent = ta.value.length + " caracteres · guardado"; clearTimeout(t); t = setTimeout(() => guardar(s, ta.value), 300); });
      fila.append(boton("Copiar", "mini", async () => { try { await navigator.clipboard.writeText(ta.value); tell("Notas copiadas"); } catch (e) { tell("No se pudo copiar"); } }), boton("Limpiar", "mini", () => { if (ta.value && !confirm("¿Borrar las notas de esta ventana?")) return; ta.value = ""; guardar(s, ""); info.textContent = ""; }));
      sec.append(el("div", "vn-t", "Notas de esta ventana"), ta, fila, info); caja.append(sec);
    }
    const ta = sec.querySelector(".nv-ta"), v = leer(K, {})[claveDe(s)] || ""; if (ta.value !== v) ta.value = v;
  };
  root.querySelectorAll(".sheet").forEach((s) => { equipar(s); new MutationObserver(() => { if (!s.hidden) equipar(s); }).observe(s, { attributes: true, attributeFilter: ["hidden"] }); });
  const al = () => { if (!root.isConnected) { window.removeEventListener("riu:objetivo", al); return; } const s = q("#ventana-ancla"); if (s) equipar(s); };
  window.addEventListener("riu:objetivo", al);
}
