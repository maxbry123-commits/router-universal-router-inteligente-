// acceso.mjs — el bridge exige una clave de acceso en TODAS las rutas salvo /health. Las pruebas de integracion la mandan solas:
// fetch() hacia 127.0.0.1 lleva `x-api-key: ACCESO_TEST` salvo que la llamada fije su propia x-api-key (una vacia = "sin clave").
export const ACCESO_TEST = 'clave-de-acceso-del-chat';
const nativo = globalThis.fetch;
if (!nativo.__conAcceso) {
  const conAcceso = (u, o = {}) => {
    const url = String((u && u.url) || u);
    if (!/^http:\/\/127\.0\.0\.1:/.test(url)) return nativo(u, o);
    const h = new Headers(o.headers || {});
    if (!h.has('x-api-key')) h.set('x-api-key', ACCESO_TEST);
    return nativo(u, { ...o, headers: h });
  };
  conAcceso.__conAcceso = true;
  globalThis.fetch = conAcceso;
}
// env por defecto de un bridge de pruebas: una clave de acceso conocida (salvo __sinAcceso o que ya defina RIU_PUBLIC_CHAT_KEY)
export function envConAcceso(envExtra = {}) {
  const { __sinAcceso, ...resto } = envExtra;
  return __sinAcceso || resto.RIU_PUBLIC_CHAT_KEY ? resto : { RIU_PUBLIC_CHAT_KEY: ACCESO_TEST, ...resto };
}
