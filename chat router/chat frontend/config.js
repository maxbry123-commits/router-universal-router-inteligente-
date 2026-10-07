// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La interfaz abre sin pedir clave. El Router funciona en HF CPU de 16 GB; las claves permanecen en el servidor.
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: 'https://6ac593acfbc85ba6823baf04--8000.hf.jobs',
  liveUrl: 'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json',
  harnessUrl: 'https://6ac593acfbc85ba6823baf04--8000.hf.jobs/plugins/puente_chat/call',
  authHeader: 'X-API-Key',
  defecto: 'nv-nemotron-super',
  modelos: []
};
