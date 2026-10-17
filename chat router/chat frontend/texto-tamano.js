// texto-tamano.js — control A− / A+ del tamaño del texto del chat. Persiste en localStorage (riu_chat_fs).
// Sin valor guardado no toca nada (la apariencia de siempre); con valor, html.riu-fs aplica --riu-chat-fs a mensajes e input.
const CLAVE = "riu_chat_fs", MIN = 11, MAX = 28, PASO = 1;
const aplicar = (px) => {
  const h = document.documentElement;
  if (!px) { h.classList.remove("riu-fs"); h.style.removeProperty("--riu-chat-fs"); return; }
  h.style.setProperty("--riu-chat-fs", px + "px"); h.classList.add("riu-fs");
};
const guardado = () => { const n = Number(localStorage.getItem(CLAVE)); return n >= MIN && n <= MAX ? n : 0; };
try { aplicar(guardado()); } catch (e) {}
export function montarTamano({ q, tell }) {
  const fila = q("#ctl-panel .row.fields") || q(".row.fields");
  if (!fila || q("#fs-grupo")) return;
  const base = () => { const m = q("#histories .item.message .txt") || q("#message"); const v = m ? parseFloat(getComputedStyle(m).fontSize) : 15; return Math.round(v || 15); };
  const g = document.createElement("span"); g.id = "fs-grupo"; g.className = "fs-grupo"; g.setAttribute("role", "group"); g.setAttribute("aria-label", "Tamaño del texto del chat");
  const mk = (txt, id, d, label) => { const b = document.createElement("button"); b.type = "button"; b.id = id; b.className = "pill fs-btn"; b.textContent = txt; b.title = label; b.setAttribute("aria-label", label);
    b.addEventListener("click", () => { const act = guardado() || base(); const n = Math.min(MAX, Math.max(MIN, act + d)); try { localStorage.setItem(CLAVE, String(n)); } catch (e) {} aplicar(n); tell("Texto del chat: " + n + " px"); }); return b; };
  g.append(mk("A−", "fs-menos", -PASO, "Reducir texto del chat"), mk("A+", "fs-mas", PASO, "Aumentar texto del chat"));
  fila.append(g);
}
