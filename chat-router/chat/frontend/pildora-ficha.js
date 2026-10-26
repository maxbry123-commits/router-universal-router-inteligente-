// pildora-ficha.js — píldora de ficha: hoja con todas las fichas (por chat)
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export function montarPildoraFicha(ctx) {
  const { q, fila, chat, pintarFichaPill, cerrarHojas, guardar, root } = ctx;
  // ---- pildora de ficha: hoja con todas las fichas (por chat) ----
  const pintarFichas = () => {
    const lista = q("#sh-ficha-lista");
    lista.replaceChildren();
    for (const m of window.RIU_CONFIG?.modelos || []) {
      lista.append(fila(m.etiqueta.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim(), "", m.id === chat().ficha, () => {
        chat().ficha = m.id;
        try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {}  // la fila NVIDIA/Groq muestra el modelo elegido
        pintarFichaPill();
        pintarFichas();
        cerrarHojas();
        guardar();
      }));
    }
  };
  pintarFichas();
  window.addEventListener("riu:fichas", () => { if (root.isConnected) { pintarFichas(); pintarFichaPill(); } });  // llegan los modelos de Groq/NVIDIA (fichas-externas.js)
}
