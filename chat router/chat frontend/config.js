// Configuracion del chat. Vacio = la pagina la sirve el Router y todo va por su misma direccion (como hoy).
// En Vercel (solo interfaz): apiBase = direccion del Router; harnessUrl = direccion HTTP del harness DeepSeek
// (la da el equipo de Opus). Las claves NUNCA van aqui: la pagina las pide y las guarda solo durante la sesion.
window.RIU_CONFIG = {
  apiBase: "",
  harnessUrl: "",
  authHeader: "X-API-Key"
};
