// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La interfaz abre sin pedir clave. El Router funciona en HF CPU de 16 GB; las claves permanecen en el servidor.
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: '',  // la dirección real sale solo de LIVE_URL.json; nunca de un Job histórico
  liveUrl: 'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json',
  harnessUrl: '',  // puente dentro del Router: se rellena desde LIVE_URL.json en la primera resolución
  proxyDestino: 'https://comand-center-1-riu-router.hf.space',  // destino fijo de los rewrites /plugins, /vault, /health de vercel.json y direccion inicial sin esperar LIVE_URL.json
  authHeader: 'X-API-Key',
  defecto: 'nv-muse-glimmer',  // ficha NVIDIA: Glimmer / Nemotron 3 Super (1 clave); las otras 4 claves van a la tool NVIDIA de codigo
  modelos: [
    { id: 'nv-muse-glimmer', etiqueta: 'NV Muse Glimmer 30B' },
    { id: 'nv-nemotron-super', etiqueta: 'NV Nemotron 3 Super' }
  ]
};
