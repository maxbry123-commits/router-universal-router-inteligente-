// chat-selector-modelos.js — selector NUEVO de modelos (separado del selector de ficha "modelo ▾", que queda igual).
// Lista fija pedida por el Director. Solo se puede elegir un modelo si el Router lo tiene de verdad:
// se consulta en vivo GET /chat/providers/{proveedor}/models y se compara el id exacto. Los demás: "no disponible".
// Al elegir uno, el chat activo envía por /chat/send con ese proveedor/modelo; al elegir una ficha vuelve al harness.
import { node } from "./api.js";

const GRUPOS = [
  { titulo: "Código y razonamiento", modelos: [
    ["🧠", "Qwen 3.8 Max", "Código complejo", null],
    ["⚡", "Qwen 3.8 Flash", "Código rápido", null],
    ["🧠", "Qwen 3.7 Max", "Razonamiento", null],
    ["⚡", "Qwen 3.7 Plus", "Código + visión", null],
    ["🚀", "Qwen 3.6 Flash", "Rápido / económico", null],
    ["🧠", "DeepSeek V4 Pro", "Código complejo", ["hf", "deepseek-ai/DeepSeek-V4-Pro"]],
    ["🧠", "DeepSeek V4 Pro 0813", "Máxima profundidad", ["hf", "deepseek-ai/DeepSeek-V4-Pro-0813"]],
    ["⚡", "DeepSeek V4 Flash", "Código rápido", ["hf", "deepseek-ai/DeepSeek-V4-Flash"]],
    ["🧠", "GLM 5.2", "Código + agentes", null]] },
  { titulo: "Imágenes", modelos: [
    ["🎨", "Qwen Image 3.0 Pro", "Imágenes", null],
    ["🎨", "Wan 2.7 Image", "Imágenes", null]] },
  { titulo: "Modo recepción · voz", recepcion: true, modelos: [
    ["🔊", "Qwen TTS", "Texto a voz", null],
    ["🎙️", "Qwen Realtime", "Voz en vivo", null],
    ["📝", "Qwen ASR", "Voz a texto", null]] },
];

export function conectarSelectorModelos(ctx) {
  const { q, chat, api, tell } = ctx;
  const pill = q("#sel-nuevo"), lista = q("#sh-modelos-lista");
  const vivos = {};  // proveedor -> Set(model_id) que el Router expone ahora
  const pintarPill = () => {
    const d = chat().directo;
    pill.textContent = d ? d.icono + " " + d.nombre + " ⌄" : "✦ modelos ⌄";
    pill.classList.toggle("on", !!d);
  };
  const elegir = (m, ruta) => {
    const c = chat();
    c.directo = ruta ? { icono: m[0], nombre: m[1], provider: ruta[0], model: ruta[1] } : null;
    pintarPill(); pintar();
    q("#sh-modelos").hidden = true;
    tell(ruta ? "Modelo directo: " + m[1] + " (" + ruta[0] + ")" : "Vuelve a la ficha del chat");
  };
  const pintar = () => {
    const d = chat().directo;
    lista.replaceChildren();
    for (const g of GRUPOS) {
      lista.append(node("h4", g.titulo, "mod-grupo-t"));
      const caja = node("div", "", g.recepcion ? "mod-recepcion" : "mod-grupo");
      for (const m of g.modelos) {
        const ruta = m[3] && vivos[m[3][0]]?.has(m[3][1]) ? m[3] : null;
        const sel = !!(d && ruta && d.model === ruta[1]);
        const b = node("button", "", "mod-fila" + (sel ? " sel" : ""));
        b.type = "button"; b.disabled = !ruta; b.setAttribute("aria-pressed", String(sel));
        const txt = node("span", "", "mod-txt");
        txt.append(node("b", m[1]), node("small", m[2]));
        b.append(node("span", m[0], "mod-ico"), txt, node("span", sel ? "✓" : (ruta ? "" : "no disponible"), sel ? "mod-ck" : "mod-tag"));
        if (ruta) b.addEventListener("click", () => elegir(m, sel ? null : ruta));
        caja.append(b);
      }
      lista.append(caja);
    }
  };
  const cargar = async () => {
    const provs = [...new Set(GRUPOS.flatMap((g) => g.modelos).filter((m) => m[3]).map((m) => m[3][0]))];
    await Promise.all(provs.map(async (p) => {
      try { vivos[p] = new Set(((await api(`/chat/providers/${encodeURIComponent(p)}/models`)).models || []).map((x) => x.model_id)); }
      catch (error) { vivos[p] = new Set(); tell("GAP modelos " + p + ": " + error.message); }
    }));
    pintar();
  };
  pill.addEventListener("click", () => { pill.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); cargar(); });
  // elegir una ficha en el selector existente devuelve el chat al harness
  q("#sh-ficha-lista").addEventListener("click", () => { chat().directo = null; pintarPill(); });
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
}
