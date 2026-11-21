// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La interfaz abre sin pedir clave. El Router funciona en HF CPU de 16 GB; las claves permanecen en el servidor.
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: '',  // direccion inicial verificada en proxyDestino
  liveUrl: '',
  harnessUrl: '',  // puente dentro del Router: se rellena desde proxyDestino al iniciar
  proxyDestino: 'https://comand-center-1-riu-router.hf.space',  // destino fijo de los rewrites /plugins, /vault, /health de vercel.json y direccion inicial sin esperar LIVE_URL.json
  authHeader: 'X-API-Key',
  defecto: 'nv-muse-glimmer',  // RESPALDO: ficha NVIDIA mientras el catalogo real no carga; fichas-externas.js lo reemplaza por los modelos reales de NVIDIA (nvidia/<modelo>)
  modelos: [
    { id: 'nv-muse-glimmer', etiqueta: 'NV Muse Glimmer 30B (respaldo)' }  // la ficha Nemotron 3 Super se retiro: ya no esta en el catalogo elegido (Nemotron 3 Ultra si)
  ]
};
