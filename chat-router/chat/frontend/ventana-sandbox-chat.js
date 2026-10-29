// ventana-sandbox-chat.js — sandbox: system prompt de code anclado a esta sesión
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export async function montarSandboxChat(ctx) {
  const { chat, q, api, tell } = ctx;
  // ---- sandbox: system prompt de code anclado a esta sesion ----
  const cargarSandbox = async () => {
    try {
      const r = await window.RIU_ACCION("sandbox", { sesion: chat().sesion });
      q("#sandbox-texto").value = r.sandbox || "";
      q("#sb-estado").textContent = r.sandbox ? "encendido" : "apagado";
    } catch (err) { q("#sb-estado").textContent = err.message; }
  };
  q("#sb-guardar").addEventListener("click", async () => {
    try {
      const r = await window.RIU_ACCION("sandbox", { sesion: chat().sesion, texto: q("#sandbox-texto").value });
      q("#sb-estado").textContent = r.encendido ? "encendido" : "apagado";
      tell("Sandbox " + (r.encendido ? "encendido y anclado" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#sb-apagar").addEventListener("click", async () => {
    try {
      await window.RIU_ACCION("sandbox", { sesion: chat().sesion, texto: "" });
      q("#sb-estado").textContent = "apagado";
      tell("Sandbox apagado");
    } catch (err) { tell(err.message); }
  });
  return { cargarSandbox };
}
