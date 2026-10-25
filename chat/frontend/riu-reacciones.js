// riu-reacciones.js — reacciones a cada respuesta (RUI 13) y reproductor paso a paso de los diagramas (RUI 15). Dividido de chat-riu2.js sin cambiar la lógica.
import { crear, leer, escribir } from "./riu-util.js";
// RUI 13 emoji-reaction: reacciones a cada respuesta (se guardan en este navegador)
export function reacciones({ q }) {
  const hist = q("#histories"); if (!hist) return;
  const R = leer("riu_reac_v1", {});
  const clave = (t) => { const s = t.replace(/[\s`]/g, "").slice(0, 80); let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h + ":" + s.length; };
  const EMO = [["👍", "Me sirvió"], ["👎", "No me sirvió"], ["✅", "Resuelto"]];
  const poner = (m) => {
    if (m.querySelector(".riu-reac")) return;
    const sp = m.querySelector(".txt"); if (!sp || sp.textContent.trim().length < 20) return;
    const k = clave(sp.textContent);
    const fila = crear("div", "riu-reac"); fila.setAttribute("role", "group"); fila.setAttribute("aria-label", "Reacciones");
    EMO.forEach(([e, t]) => {
      const b = crear("button", "riu-r" + (R[k] === e ? " on" : ""), e); b.type = "button"; b.title = t; b.setAttribute("aria-label", t); b.setAttribute("aria-pressed", String(R[k] === e));
      b.addEventListener("click", () => {
        const ya = R[k] === e; if (ya) delete R[k]; else R[k] = e;
        const ks = Object.keys(R); if (ks.length > 300) delete R[ks[0]];
        escribir("riu_reac_v1", R);
        fila.querySelectorAll(".riu-r").forEach((x) => { const on = !ya && x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", String(on)); });
        b.classList.remove("pop"); void b.offsetWidth; b.classList.add("pop");
      });
      fila.append(b);
    });
    m.append(fila);
  };
  let p = 0;
  const revisar = () => { p = 0; hist.querySelectorAll(".message:not(.user):not(.meta):not(.pending):not(.error)").forEach(poner); };
  new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  revisar();
}

// RUI 15 step-player: recorrer paso a paso el diagrama de cada selector
export function reproductor({ root }) {
  const poner = (d) => {
    let b = d.nextElementSibling && d.nextElementSibling.classList.contains("dg-play") ? d.nextElementSibling : null;
    if (!b) {
      b = crear("button", "mini dg-play", "▶ Recorrer"); b.type = "button";
      let t = null;
      const parar = () => { clearInterval(t); t = null; b.textContent = "▶ Recorrer"; d.querySelectorAll(".dg-activo").forEach((x) => x.classList.remove("dg-activo")); };
      b.addEventListener("click", () => {
        if (t) { parar(); return; }
        const pasos = [...d.querySelectorAll(".dg-paso")]; let i = 0; b.textContent = "■ Parar";
        const paso = () => {
          d.querySelectorAll(".dg-activo").forEach((x) => x.classList.remove("dg-activo"));
          if (i >= pasos.length) { parar(); return; }
          pasos[i].classList.add("dg-activo"); pasos[i].scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" }); i++;
        };
        paso(); t = setInterval(paso, 900);
      });
      d.after(b);
    }
    b.hidden = d.hidden || !d.querySelector(".dg-paso");
  };
  root.querySelectorAll(".consil-diagrama").forEach((d) => { poner(d); new MutationObserver(() => poner(d)).observe(d, { childList: true, attributes: true, attributeFilter: ["hidden"] }); });
}
